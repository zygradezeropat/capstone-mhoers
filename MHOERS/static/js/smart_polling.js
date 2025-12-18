// Optimized polling with exponential backoff
class SmartPolling {
  constructor(endpoint, callback, options = {}) {
    this.endpoint = endpoint;
    this.callback = callback;
    this.minInterval = options.minInterval || 2000; // 2 seconds
    this.maxInterval = options.maxInterval || 30000; // 30 seconds
    this.currentInterval = this.minInterval;
    this.isActive = false;
    this.lastUpdate = null;
    this.consecutiveErrors = 0;
    this.timeout = null;
  }

  start() {
    if (this.isActive) return;
    this.isActive = true;
    this.poll();
  }

  stop() {
    this.isActive = false;
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
  }

  async poll() {
    if (!this.isActive) return;

    try {
      const response = await fetch(this.endpoint, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Cache-Control': 'no-cache'
        },
        cache: 'no-store'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const hasUpdate = this.lastUpdate !== JSON.stringify(data);
      
      if (hasUpdate) {
        this.callback(data);
        this.lastUpdate = JSON.stringify(data);
        this.currentInterval = this.minInterval; // Reset to fast polling
        this.consecutiveErrors = 0;
      } else {
        // No update, gradually increase interval
        this.currentInterval = Math.min(
          this.currentInterval * 1.5,
          this.maxInterval
        );
      }
    } catch (error) {
      console.error('Polling error:', error);
      this.consecutiveErrors++;
      // Increase interval on errors
      this.currentInterval = Math.min(
        this.currentInterval * 2,
        this.maxInterval
      );
    }

    // Schedule next poll
    this.timeout = setTimeout(() => this.poll(), this.currentInterval);
  }

  // Pause when tab is hidden, resume when visible
  handleVisibilityChange() {
    if (document.hidden) {
      this.stop();
    } else {
      this.start();
    }
  }
}

