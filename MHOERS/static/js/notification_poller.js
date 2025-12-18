// Notification polling using SmartPolling
(function() {
  'use strict';
  
  let notificationPoller = null;
  
  function updateNotificationBadge(data) {
    const badge = document.getElementById('notif-count');
    if (!badge) return;
    
    if (data.unseen_count > 0) {
      badge.innerText = data.unseen_count;
      badge.style.display = 'inline';
      
      // Optional: Request browser notification permission and show notification
      if ('Notification' in window && Notification.permission === 'granted') {
        // Only show if count increased (not on first load)
        if (notificationPoller && notificationPoller.lastUpdate) {
          new Notification('New Notification', {
            body: `You have ${data.unseen_count} new notification(s)`,
            icon: '/static/images/MHO-LOGO.png',
            tag: 'notification-update'
          });
        }
      }
    } else {
      badge.style.display = 'none';
    }
  }
  
  function initializeNotificationPolling() {
    // Check if SmartPolling is available
    if (typeof SmartPolling === 'undefined') {
      console.warn('SmartPolling not available, using fallback polling');
      // Fallback to simple polling
      function checkNotifications() {
        fetch('/notifications/check/')
          .then(response => response.json())
          .then(data => updateNotificationBadge(data))
          .catch(error => console.error('Error checking notifications:', error));
      }
      checkNotifications();
      setInterval(checkNotifications, 5000);
      return;
    }
    
    // Get notification endpoint
    const notificationEndpoint = '/notifications/check/';
    
    // Create poller
    notificationPoller = new SmartPolling(
      notificationEndpoint,
      updateNotificationBadge,
      { 
        minInterval: 3000,  // Start with 3 seconds
        maxInterval: 30000  // Max 30 seconds when idle
      }
    );
    
    // Start polling
    notificationPoller.start();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    
    // Pause when tab is hidden, resume when visible
    document.addEventListener('visibilitychange', () => {
      notificationPoller.handleVisibilityChange();
    });
    
    // Stop polling when page is unloading
    window.addEventListener('beforeunload', () => {
      if (notificationPoller) {
        notificationPoller.stop();
      }
    });
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNotificationPolling);
  } else {
    initializeNotificationPolling();
  }
})();

