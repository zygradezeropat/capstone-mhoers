// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    // Toggle sidebar on mobile
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
        document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
    }
    
    // Close sidebar
    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
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
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 767) {
            closeSidebar();
        }
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
    
    // Add loading animation
    setTimeout(() => {
        if (sidebar) {
            sidebar.style.opacity = '1';
            sidebar.style.transform = 'translateX(0)';
        }
    }, 100);
});

// Add CSS for initial loading state
const style = document.createElement('style');
style.textContent = `
    .sidebar {
        opacity: 0;
        transform: translateX(-20px);
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    .sidebar.loaded {
        opacity: 1;
        transform: translateX(0);
    }
`;
document.head.appendChild(style);
