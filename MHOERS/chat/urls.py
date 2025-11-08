from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='chat_conversation'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('users/', views.user_list, name='user_list'),
]

