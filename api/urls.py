from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import *
from django.urls import re_path
from . import consumers


urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    path('get_unread_messages/', get_unread_messages, name='get_unread_messages'),
    path('create_connection/', create_connection, name='create_connection'),
    path('mark_message_read/', mark_message_read, name='mark_message_read'),
    path('typing_status/', typing_status, name='typing_status'),
    path('send_message/', send_message, name='send_message'),

    re_path(r'ws/chat/(?P<user1>\w+)/(?P<user2>\w+)/$', consumers.ChatConsumer.as_asgi(), name='ws_chat'),
    # path('ws/chat/', consumers.SimpleChatConsumer.as_asgi()),


    

]