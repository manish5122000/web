"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# application = get_asgi_application()

# import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from api import routing  

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             routing.websocket_urlpatterns  
#         )
#     ),
# })
# import os
# import django
# from channels.routing import get_default_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabulator.settings')

# django.setup()

# application = get_default_application()


import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path,re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django_asgi_app = get_asgi_application()

from api.consumers import *
import api

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": 
        # AuthMiddlewareStack(
            URLRouter([
                # path('ws/chat/', SimpleChatConsumer.as_asgi()),
                re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),

            ])
        # )
    ,
})

