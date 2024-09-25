from django.urls import re_path,path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<user1>\w+)/(?P<user2>\w+)/$', consumers.ChatConsumer.as_asgi()),
    # re_path(r'ws/test', consumers.ChatConsumer.as_asgi()),
    path('ws/chat/', consumers.SimpleChatConsumer.as_asgi()),
]
