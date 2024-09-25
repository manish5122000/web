from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from rest_framework import viewsets
from .models import *
from .serializers import *

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.urls import reverse
from django.utils import timezone

# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 200,"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def create_connection(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        user1 = body.get('user1')
        user2 = body.get('user2')

        if not user1 or not user2:
            return JsonResponse({'status': 'error', 'message': 'Both user1 and user2 must be provided.'})

        try:
            user1_instance = User.objects.get(username__iexact=user1)
            user2_instance = User.objects.get(username__iexact=user2)

            websocket_url = reverse('api:ws_chat', kwargs={'user1': user1, 'user2': user2})

            return JsonResponse({
                'status': 'success',
                'message': f'Connected {user1} to {user2}',
                'websocket_url': websocket_url  
            })
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'One or both users do not exist.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@csrf_exempt
def mark_message_read(request):
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        try:
            message = Message.objects.get(id=message_id)
            message.is_read = True
            message.save()
            return JsonResponse({'status': 'success', 'message': 'Message marked as read'})
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'})

@csrf_exempt
def typing_status(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        is_typing = request.POST.get('is_typing') == 'true'
        
        return JsonResponse({'status': 'success', 'message': f'{user} is typing: {is_typing}'})

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        room_name = request.POST.get('roomname')
        sender_username = request.POST.get('from')
        receiver_username = request.POST.get('to')
        message_text = request.POST.get('message')

        try:
            sender = User.objects.get(username=sender_username)
            receiver = User.objects.get(username=receiver_username)

            room, created = ChatRoom.objects.get_or_create(name=room_name)

            message_content = {
                "roomname": room_name,
                "from": sender.username,
                "to": receiver.username,
                "message": message_text,
                "timestamp": timezone.now(), 
                "is_read": False,
                "is_delivered": True,
            }

            message = Message.objects.create(content=message_content)

            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp,
                }
            })
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'One or both users do not exist.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@csrf_exempt
def get_unread_messages(request):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        recipient = User.objects.get(username=recipient_username)

        unread_messages = Message.objects.filter(recipient=recipient, is_read=False)

        messages_list = []
        for message in unread_messages:
            messages_list.append({
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp,
                'is_read': message.is_read
            })

        return JsonResponse({'status': 'success', 'messages': messages_list})
