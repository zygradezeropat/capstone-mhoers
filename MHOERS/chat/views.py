from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Max, Sum
from django.core.paginator import Paginator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Conversation, Message, MessageNotification
from .forms import MessageForm
import json


@login_required
def chat_home(request):
    """Main chat page showing all conversations"""
    user = request.user
    
    # Get all conversations for the user
    conversations = Conversation.objects.filter(
        participants=user,
        is_active=True
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user) & Q(messages__is_deleted=False))
    ).order_by('-updated_at')
    
    # Get unread message count for each conversation and add other user name
    for conversation in conversations:
        try:
            notification = MessageNotification.objects.get(
                user=user,
                conversation=conversation
            )
            conversation.user_unread_count = notification.unread_count
        except MessageNotification.DoesNotExist:
            conversation.user_unread_count = 0
        
        # Add other user name for display
        other_user = conversation.get_other_participant(user)
        conversation.other_user_name = other_user.get_full_name() or other_user.username if other_user else "Unknown User"
    
    context = {
        'conversations': conversations,
        'active_page': 'chat',
    }
    return render(request, 'chat/chat_home.html', context)


@login_required
def start_conversation(request, user_id):
    """Start a new conversation with a user"""
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_conversation:
            return redirect('chat:chat_conversation', conversation_id=existing_conversation.id)
        
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        
        # Redirect directly without flashing a success alert to avoid a green bar under the chat
        return redirect('chat:chat_conversation', conversation_id=conversation.id)
        
    except Exception as e:
        messages.error(request, f'Error starting conversation: {str(e)}')
        return redirect('chat:chat_home')


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Mark all messages in this conversation as read for the current user
    Message.objects.filter(
        conversation=conversation
    ).exclude(sender=request.user).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    # Reset unread count for this conversation
    MessageNotification.objects.filter(
        user=request.user,
        conversation=conversation
    ).update(unread_count=0)
    
    # Get messages for this conversation (exclude deleted messages)
    messages_list = conversation.messages.filter(is_deleted=False).order_by('created_at')
    
    # Pagination
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Update unread count for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                notification, created = MessageNotification.objects.get_or_create(
                    user=participant,
                    conversation=conversation
                )
                notification.unread_count += 1
                notification.save()
            
            return redirect('chat:chat_conversation', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': messages_page,
        'form': form,
        'other_user': conversation.get_other_participant(request.user),
        'active_page': 'chat',
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
def send_message(request, conversation_id):
    """Send a message via AJAX"""
    if request.method == 'POST':
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'Message content is required'}, status=400)
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Update unread count for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                notification, created = MessageNotification.objects.get_or_create(
                    user=participant,
                    conversation=conversation
                )
                notification.unread_count += 1
                notification.save()
            
            # Broadcast message to WebSocket clients
            try:
                channel_layer = get_channel_layer()
                room_group_name = f'chat_{conversation_id}'
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.get_full_name() or message.sender.username,
                    'sender_id': message.sender.id,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_read': message.is_read
                }
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_data
                    }
                )
            except Exception as e:
                # If channel layer is not available, continue without broadcasting
                # This allows the HTTP endpoint to work even if Channels is not fully configured
                print(f"Warning: Could not broadcast message via Channels: {e}")
            
            return JsonResponse({
                'success': True,
                'id': message.id,
                'message_id': message.id,
                'content': message.content,
                'sender': message.sender.get_full_name() or message.sender.username,
                'sender_id': message.sender.id,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_deleted': message.is_deleted
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def get_messages(request, conversation_id):
    """Get messages for a conversation via AJAX"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        # Get last message ID for pagination
        last_message_id = request.GET.get('last_message_id')
        
        if last_message_id:
            messages_list = conversation.messages.filter(id__gt=last_message_id, is_deleted=False).order_by('created_at')
        else:
            messages_list = conversation.messages.filter(is_deleted=False).order_by('-created_at')[:20]
            messages_list = list(reversed(messages_list))
        
        messages_data = []
        for message in messages_list:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender': message.sender.get_full_name() or message.sender.username,
                'sender_id': message.sender.id,
                'is_own': message.sender == request.user,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': message.is_read,
                'is_deleted': message.is_deleted
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_unread_count(request):
    """Get unread message count for the current user"""
    try:
        total_unread = MessageNotification.objects.filter(
            user=request.user
        ).aggregate(total=Sum('unread_count'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'unread_count': total_unread
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def user_list(request):
    """Get list of users for starting conversations"""
    search_query = request.GET.get('search', '')
    
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id).filter(is_active=True)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    users = users.order_by('first_name', 'last_name', 'username')[:20]
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'is_staff': user.is_staff
        })
    
    return JsonResponse({
        'success': True,
        'users': users_data
    })


@login_required
def delete_message(request, message_id):
    """Delete a message (soft delete)"""
    if request.method == 'POST':
        try:
            message = get_object_or_404(Message, id=message_id)
            
            # Check if user is the sender or a participant in the conversation
            if message.sender != request.user and request.user not in message.conversation.participants.all():
                return JsonResponse({'error': 'You do not have permission to delete this message'}, status=403)
            
            # Soft delete the message
            message.delete_message(request.user)
            
            # Broadcast delete event to WebSocket clients
            try:
                channel_layer = get_channel_layer()
                room_group_name = f'chat_{message.conversation.id}'
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message.id
                    }
                )
            except Exception as e:
                print(f"Warning: Could not broadcast delete via Channels: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'Message deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation (soft delete by setting is_active=False)"""
    if request.method == 'POST':
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            
            # Soft delete the conversation by setting is_active=False
            conversation.is_active = False
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Conversation deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)