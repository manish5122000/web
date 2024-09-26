# chat_app/consumers.py
from datetime import timezone
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
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected for room: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for room: {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_username = data['from']
        recipient_username = data['to']

        # Save the message in the database, including room name in the JSON content
        await self.save_message(sender_username, recipient_username, message, self.room_name)

        # Send message to the room group (broadcast to other users in the room)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'from': sender_username,
                'to': recipient_username,
                'roomname': self.room_name,
                'timestamp': timezone.now().isoformat()
            }
        )

    # Receive message from the room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['from']
        recipient = event['to']
        room_name = event['roomname']
        timestamp = event['timestamp']

        # Send the message to WebSocket clients
        await self.send(text_data=json.dumps({
            'message': message,
            'from': sender,
            'to': recipient,
            'roomname': room_name,
            'timestamp': timestamp
        }))

    @sync_to_async
    def save_message(self, sender_username, recipient_username, message_content, room_name):
        """
        Save the message to the database with room name in the JSON content.
        """
        try:
            # Find the users by their usernames
            sender = User.objects.get(username=sender_username)
            recipient = User.objects.get(username=recipient_username)

            # Find or create the chat room by room name
            room, created = ChatRoom.objects.get_or_create(name=room_name)

            # Prepare message content as a JSON structure
            message_data = {
                "roomname": room_name,
                "from": sender_username,
                "to": recipient_username,
                "message": message_content,
                "timestamp": timezone.now().isoformat()
            }

            # Create and save the message in the database
            Message.objects.create(
                content=message_data,  # Save the message as JSON
                timestamp=timezone.now()
            )
            logger.info(f"Message saved: {message_data}")
        except User.DoesNotExist as e:
            logger.error(f"Error saving message: {e}")
