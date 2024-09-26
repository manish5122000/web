from django.contrib.auth.models import User
from django.db import models
from django.forms import JSONField

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    user1 = models.ForeignKey(User, related_name="user1_rooms", on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name="user2_rooms", on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    def available_users(self):
        return [self.user1.username, self.user2.username]

class Message(models.Model):
    roomname = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True)
    content = JSONField()  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.content['from']} to {self.content['to']} in {self.content['roomname']}"


class TypingIndicator(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)



