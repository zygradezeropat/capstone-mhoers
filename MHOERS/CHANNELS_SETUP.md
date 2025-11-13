# Django Channels Real-Time Chat Setup

This document explains the Django Channels implementation for real-time chat functionality.

## What Was Implemented

1. **ASGI Configuration** (`MHOERS/asgi.py`)
   - Configured to handle both HTTP and WebSocket connections
   - Added authentication middleware for WebSocket connections
   - Added security validation for allowed hosts

2. **Channel Layers** (`MHOERS/settings.py`)
   - Configured Redis as the channel layer backend
   - Added `ASGI_APPLICATION` setting

3. **WebSocket Consumer** (`chat/consumers.py`)
   - Handles WebSocket connections for chat conversations
   - Manages message sending and receiving
   - Validates user authentication and conversation participation
   - Broadcasts messages to all participants in real-time

4. **WebSocket Routing** (`chat/routing.py`)
   - Routes WebSocket connections to the appropriate consumer
   - URL pattern: `/ws/chat/<conversation_id>/`

5. **Frontend WebSocket Client** (`templates/chat/conversation_detail.html`)
   - Connects to WebSocket on page load
   - Sends messages via WebSocket
   - Receives messages in real-time
   - Automatic reconnection on connection loss
   - Fallback to HTTP if WebSocket is unavailable

6. **HTTP Fallback** (`chat/views.py`)
   - Updated `send_message` view to broadcast via Channels
   - Ensures messages sent via HTTP are also broadcast to WebSocket clients

## Prerequisites

### Redis Installation

Django Channels requires Redis for the channel layer. You need to install and run Redis:

**Windows:**
1. Download Redis from: https://github.com/microsoftarchive/redis/releases
2. Or use WSL (Windows Subsystem for Linux) and install Redis there
3. Or use Docker: `docker run -d -p 6379:6379 redis`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
redis-server
```

### Verify Redis is Running

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

## Running the Application

### Development Server

Instead of using the regular Django development server, you need to use Daphne (ASGI server):

```bash
# Install Daphne if not already installed
pip install daphne

# Run the ASGI server
daphne -b 0.0.0.0 -p 8000 MHOERS.asgi:application
```

Or use the Channels development server:

```bash
python manage.py runserver
```

Note: Django's `runserver` command automatically uses Daphne when Channels is configured.

### Production Deployment

For production, use a proper ASGI server like:
- **Daphne**: `daphne -b 0.0.0.0 -p 8000 MHOERS.asgi:application`
- **Uvicorn**: `uvicorn MHOERS.asgi:application --host 0.0.0.0 --port 8000`
- **Gunicorn with Uvicorn workers**: `gunicorn MHOERS.asgi:application -w 4 -k uvicorn.workers.UvicornWorker`

## Configuration Options

### Using In-Memory Channel Layer (Development Only)

If Redis is not available, you can use an in-memory channel layer for development:

In `MHOERS/settings.py`, comment out the Redis configuration and uncomment:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
```

**Note:** In-memory channel layers only work with a single server instance and are not suitable for production.

### Redis Configuration

The default Redis configuration in `settings.py`:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

For production, you may want to add:
- Password authentication
- Multiple Redis hosts for high availability
- Connection pooling

## How It Works

1. **User opens chat conversation**
   - Frontend JavaScript connects to WebSocket: `ws://localhost:8000/ws/chat/<conversation_id>/`
   - Consumer validates user authentication and conversation participation
   - User joins the conversation's room group

2. **User sends a message**
   - Message is sent via WebSocket to the consumer
   - Consumer saves message to database
   - Consumer broadcasts message to all participants in the room group
   - All connected clients receive the message instantly

3. **Real-time updates**
   - Messages appear instantly for all participants
   - No page refresh needed
   - Automatic reconnection if connection is lost

## Testing

1. Open two browser windows/tabs
2. Log in as different users in each window
3. Start a conversation between the two users
4. Send a message from one window
5. The message should appear instantly in the other window without refreshing

## Troubleshooting

### WebSocket Connection Fails

- Check that Redis is running: `redis-cli ping`
- Verify ASGI application is being used (not WSGI)
- Check browser console for WebSocket errors
- Ensure `ALLOWED_HOSTS` includes your domain

### Messages Not Appearing in Real-Time

- Check browser console for JavaScript errors
- Verify WebSocket connection is established (check console logs)
- Ensure both users are connected to the same conversation
- Check Redis is running and accessible

### Channel Layer Errors

- Verify Redis is installed and running
- Check Redis connection settings in `settings.py`
- For development, you can temporarily use `InMemoryChannelLayer`

## Features

✅ Real-time message delivery  
✅ Automatic reconnection  
✅ HTTP fallback for compatibility  
✅ User authentication validation  
✅ Conversation participation validation  
✅ Duplicate message prevention  
✅ XSS protection (HTML escaping)  

## Next Steps (Optional Enhancements)

- [ ] Typing indicators
- [ ] Message read receipts
- [ ] Online/offline status
- [ ] File/image sharing
- [ ] Message reactions
- [ ] Push notifications

