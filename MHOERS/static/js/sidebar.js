// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarToggleDesktop = document.getElementById('sidebarToggleDesktop');
    const collapseIcon = document.getElementById('collapseIcon');
    const mainContent = document.querySelector('.main-content');
    
    // Debug: Log elements to console
    console.log('Sidebar elements found:', {
        sidebar: !!sidebar,
        sidebarToggle: !!sidebarToggle,
        sidebarClose: !!sidebarClose,
        sidebarOverlay: !!sidebarOverlay,
        sidebarToggleDesktop: !!sidebarToggleDesktop,
        collapseIcon: !!collapseIcon,
        mainContent: !!mainContent
    });
    
    // Force set the collapse icon immediately
    if (collapseIcon) {
        console.log('Collapse icon found, setting to chevron-left');
        collapseIcon.className = 'bi bi-chevron-left';
        collapseIcon.innerHTML = '';
    }
    
    // Additional fallback - find collapse icon by parent button
    const desktopToggle = document.getElementById('sidebarToggleDesktop');
    if (desktopToggle) {
        const iconInButton = desktopToggle.querySelector('i');
        if (iconInButton) {
            console.log('Found icon in desktop toggle button, setting to chevron-left');
            iconInButton.className = 'bi bi-chevron-left';
            iconInButton.innerHTML = '';
        }
    }
    
    // Check if sidebar is collapsed from localStorage
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed && window.innerWidth > 767) {
        sidebar.classList.add('collapsed');
        if (mainContent) {
            mainContent.classList.add('sidebar-collapsed');
        }
        if (collapseIcon) {
            collapseIcon.className = 'bi bi-chevron-right';
        }
    } else {
        // Initialize collapse icon for expanded state
        if (collapseIcon && window.innerWidth > 767) {
            collapseIcon.className = 'bi bi-chevron-left';
        }
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
    
    // Toggle sidebar collapse on desktop
    function toggleSidebarCollapse() {
        if (window.innerWidth > 767) {
            sidebar.classList.toggle('collapsed');
            if (mainContent) {
                mainContent.classList.toggle('sidebar-collapsed');
            }
            
            // Update icon
            if (collapseIcon) {
                if (sidebar.classList.contains('collapsed')) {
                    collapseIcon.className = 'bi bi-chevron-right';
                    collapseIcon.innerHTML = '';
                } else {
                    collapseIcon.className = 'bi bi-chevron-left';
                    collapseIcon.innerHTML = '';
                }
            }
            
            // Additional fallback - update icon in desktop toggle button
            const desktopToggle = document.getElementById('sidebarToggleDesktop');
            if (desktopToggle) {
                const iconInButton = desktopToggle.querySelector('i');
                if (iconInButton) {
                    if (sidebar.classList.contains('collapsed')) {
                        iconInButton.className = 'bi bi-chevron-right';
                        iconInButton.innerHTML = '';
                    } else {
                        iconInButton.className = 'bi bi-chevron-left';
                        iconInButton.innerHTML = '';
                    }
                }
            }
            
            // Save state to localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            
            // Force a small delay to ensure CSS transitions work properly
            setTimeout(() => {
                sidebar.style.transition = 'all 0.3s ease';
            }, 10);
        }
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
    
    if (sidebarToggleDesktop) {
        sidebarToggleDesktop.addEventListener('click', function(e) {
            // Only allow desktop collapse on screens wider than 767px
            if (window.innerWidth > 767) {
                toggleSidebarCollapse();
            }
        });
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
                // Restore collapsed state on desktop
                const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
                if (isCollapsed) {
                    sidebar.classList.add('collapsed');
                    if (mainContent) {
                        mainContent.classList.add('sidebar-collapsed');
                    }
                    if (collapseIcon) {
                        collapseIcon.className = 'bi bi-chevron-right';
                    }
                } else {
                    sidebar.classList.remove('collapsed');
                    if (mainContent) {
                        mainContent.classList.remove('sidebar-collapsed');
                    }
                    if (collapseIcon) {
                        collapseIcon.className = 'bi bi-chevron-left';
                    }
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
    
    // Ensure collapse icon is properly initialized
    if (collapseIcon && window.innerWidth > 767) {
        if (sidebar.classList.contains('collapsed')) {
            collapseIcon.className = 'bi bi-chevron-right';
            console.log('Icon set to chevron-right (collapsed)');
        } else {
            collapseIcon.className = 'bi bi-chevron-left';
            console.log('Icon set to chevron-left (expanded)');
        }
    } else {
        console.log('Collapse icon not found or not on desktop');
    }
    
    // Add loading animation (but ensure visibility)
    setTimeout(() => {
        if (sidebar) {
            sidebar.style.opacity = '1';
            sidebar.style.transform = 'translateX(0)';
            sidebar.classList.add('loaded');
        }
        
        // Double-check icon initialization after DOM is fully loaded
        if (collapseIcon && window.innerWidth > 767) {
            if (sidebar.classList.contains('collapsed')) {
                collapseIcon.className = 'bi bi-chevron-right';
            } else {
                collapseIcon.className = 'bi bi-chevron-left';
            }
        }
    }, 100);
});
