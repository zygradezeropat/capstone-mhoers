// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.querySelector('.main-content');
    
    // Ensure sidebar is always expanded (remove any collapsed state)
    if (sidebar) {
        sidebar.classList.remove('collapsed');
    }
    if (mainContent) {
        mainContent.classList.remove('sidebar-collapsed');
    }
    
    // Toggle sidebar on mobile
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
        
        // Enhanced mobile body scroll prevention
        if (sidebar.classList.contains('active')) {
            document.body.classList.add('sidebar-open');
            document.body.style.overflow = 'hidden';
            document.body.style.position = 'fixed';
            document.body.style.width = '100%';
        } else {
            document.body.classList.remove('sidebar-open');
            document.body.style.overflow = '';
            document.body.style.position = '';
            document.body.style.width = '';
        }
    }
    
    // Close sidebar
    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        document.body.classList.remove('sidebar-open');
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
    }
    
    
    // Event listeners
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }
    
    // Close sidebar when clicking on a nav link (mobile)
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 767) {
                closeSidebar();
            }
        });
    });
    
    // Touch gesture support for mobile
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    
    // Handle touch start
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    
    // Handle touch end
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, { passive: true });
    
    // Handle swipe gestures
    function handleSwipe() {
        const deltaX = touchEndX - touchStartX;
        const deltaY = touchEndY - touchStartY;
        const minSwipeDistance = 50;
        
        // Check if it's a horizontal swipe (not vertical scroll)
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
            // Swipe right to open sidebar (only if sidebar is closed and we're on mobile)
            if (deltaX > 0 && window.innerWidth <= 767 && !sidebar.classList.contains('active')) {
                // Only trigger if swipe starts from left edge of screen
                if (touchStartX < 50) {
                    toggleSidebar();
                }
            }
            // Swipe left to close sidebar (only if sidebar is open)
            else if (deltaX < 0 && sidebar.classList.contains('active')) {
                closeSidebar();
            }
        }
    }
    
    // Handle window resize with debouncing
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            if (window.innerWidth > 767) {
                closeSidebar();
                // Ensure sidebar is always expanded on desktop
                sidebar.classList.remove('collapsed');
                if (mainContent) {
                    mainContent.classList.remove('sidebar-collapsed');
                }
            } else {
                // On mobile, remove collapsed state and ensure sidebar is closed
                sidebar.classList.remove('collapsed');
                if (mainContent) {
                    mainContent.classList.remove('sidebar-collapsed');
                }
                closeSidebar();
            }
        }, 150);
    });
    
    // Keyboard support (ESC key to close sidebar)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
    
    // Add active class to current page
    const currentPath = window.location.pathname;
    const navLinksWithActive = document.querySelectorAll('.sidebar-nav .nav-link');
    
    navLinksWithActive.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
    
    // Smooth scroll for sidebar
    if (sidebar) {
        sidebar.addEventListener('scroll', function() {
            // Add shadow effect when scrolling
            if (this.scrollTop > 0) {
                this.style.boxShadow = '2px 0 20px rgba(0,0,0,0.15)';
            } else {
                this.style.boxShadow = '2px 0 10px rgba(0,0,0,0.1)';
            }
        });
    }
    
    // Force sidebar to be visible immediately
    if (sidebar) {
        sidebar.style.opacity = '1';
        sidebar.style.visibility = 'visible';
        sidebar.style.transform = 'translateX(0)';
        sidebar.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
    }
    
    // Add loading animation (but ensure visibility)
    setTimeout(() => {
        if (sidebar) {
            sidebar.style.opacity = '1';
            sidebar.style.transform = 'translateX(0)';
            sidebar.classList.add('loaded');
            // Ensure sidebar is always expanded
            sidebar.classList.remove('collapsed');
        }
        if (mainContent) {
            mainContent.classList.remove('sidebar-collapsed');
        }
    }, 100);
});
