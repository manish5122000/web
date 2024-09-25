# chat_app/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import ChatRoom, Message, TypingIndicator
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class SimpleChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("hello-----------")
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Disconnect handling (optional)
        pass

    async def receive(self, text_data):
        # Handle incoming messages
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message back
        await self.send(text_data=json.dumps({
            'message': message
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    active_users = set()

    async def connect(self):
        self.user1 = self.scope['url_route']['kwargs']['user1']
        self.user2 = self.scope['url_route']['kwargs']['user2']
        token = self.scope['query_string'].decode('utf-8').split('=')[-1]

        try:
            payload = AccessToken(token)
            user_id = payload['user_id']
            self.user1_instance = await database_sync_to_async(User.objects.get)(id=user_id)
        except TokenError:
            await self.close()
            logger.error("Invalid token provided.")
            return
        except User.DoesNotExist:
            await self.close()
            logger.error(f"User with ID {user_id} does not exist.")
            return

        self.room_name = f"{self.user1}_{self.user2}"
        self.room_group_name = f"chat_{self.room_name}"

        self.active_users.add(self.user1_instance.username)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user1_instance.username} connected to chat room {self.room_name}.")


    async def disconnect(self, close_code):
        self.active_users.discard(self.user1_instance.username)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user1_instance.username} disconnected from chat room {self.room_name}.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('event')

        if event_type == 'send_message':
            await self.send_message(data)
        elif event_type == 'typing':
            await self.typing_indicator(data)
        elif event_type == 'mark_read':
            await self.mark_messages_read(data)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def create_or_get_room(self, user1, user2):
        user1_obj = User.objects.get(username=user1)
        user2_obj = User.objects.get(username=user2)
        room_name = f"{user1}_{user2}"
        room, _ = ChatRoom.objects.get_or_create(user1=user1_obj, user2=user2_obj, name=room_name)
        return room

    async def send_message(self, data):
        sender = data['sender']
        recipient = data['recipient']
        message_content = data['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': sender,
                'recipient': recipient
            }
        )

        await self.save_message(sender, recipient, message_content)

    @sync_to_async
    def save_message(self, sender_username, recipient_username, message_content):
        try:
            room = ChatRoom.objects.get(name=self.room_name)
            sender = User.objects.get(username=sender_username)
            recipient = User.objects.get(username=recipient_username)

            message = Message.objects.create(
                room=room,
                sender=sender,
                content=message_content,
                is_read=False,
                is_delivered=False
            )

            if self.is_user_online(recipient):
                message.is_delivered = True
            message.save()
            logger.info(f"Message sent from {sender_username} to {recipient_username}: {message_content}")
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    async def typing_indicator(self, data):
        user = data['user']
        is_typing = data['is_typing']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_status',
                'user': user,
                'is_typing': is_typing
            }
        )

        await self.update_typing_status(user, is_typing)

    @sync_to_async
    def update_typing_status(self, user, is_typing):
        room = ChatRoom.objects.get(name=self.room_name)
        user_obj = User.objects.get(username=user)
        typing_status, _ = TypingIndicator.objects.get_or_create(room=room, user=user_obj)
        typing_status.is_typing = is_typing
        typing_status.save()
        logger.info(f"Typing status updated for user {user}: {is_typing}")

    async def mark_messages_read(self, data):
        recipient = data['recipient']

        await self.mark_all_messages_as_read(recipient)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f"Messages read by {recipient}",
                'sender': 'system',
                'recipient': recipient
            }
        )

    @sync_to_async
    def mark_all_messages_as_read(self, recipient_username):
        room = ChatRoom.objects.get(name=self.room_name)
        recipient = User.objects.get(username=recipient_username)

        unread_messages = Message.objects.filter(room=room, is_read=False)
        for message in unread_messages:
            message.is_read = True
            message.save()
            logger.info(f"Marked message as read for recipient {recipient_username}.")

    def is_user_online(self, user):
        return user.username in self.active_users
