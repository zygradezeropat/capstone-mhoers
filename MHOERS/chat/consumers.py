import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Message, MessageNotification
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Reject connection if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get conversation ID from URL
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Verify user is a participant in this conversation
        is_participant = await self.is_participant(self.conversation_id, self.user)
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                content = text_data_json.get('content', '').strip()
                
                if not content:
                    await self.send(text_data=json.dumps({
                        'error': 'Message content is required'
                    }))
                    return
                
                # Save message to database
                message_data = await self.save_message(
                    self.conversation_id,
                    self.user,
                    content
                )
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_data
                    }
                )
            elif message_type == 'typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.get_full_name() or self.user.username,
                        'is_typing': text_data_json.get('is_typing', False)
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def chat_message(self, event):
        """Receive message from room group and send to WebSocket"""
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def message_deleted(self, event):
        """Handle message deletion event from room group"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id']
        }))
    
    @database_sync_to_async
    def is_participant(self, conversation_id, user):
        """Check if user is a participant in the conversation"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, conversation_id, sender, content):
        """Save message to database and return message data"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content
            )
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Update unread count for other participants
            for participant in conversation.participants.exclude(id=sender.id):
                notification, created = MessageNotification.objects.get_or_create(
                    user=participant,
                    conversation=conversation
                )
                notification.unread_count += 1
                notification.save()
            
            return {
                'id': message.id,
                'content': message.content,
                'sender': sender.get_full_name() or sender.username,
                'sender_id': sender.id,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': message.is_read,
                'is_deleted': message.is_deleted
            }
        except Conversation.DoesNotExist:
            raise ValueError('Conversation not found')
        except Exception as e:
            raise ValueError(f'Error saving message: {str(e)}')

