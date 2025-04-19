/**
 * Theme Switcher
 * Handles dark/light mode toggling and persistence
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved theme preference or use OS preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme based on saved preference or OS preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        setDarkMode();
    } else {
        setLightMode();
    }
    
    // Set up theme toggle for main website
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }
    
    // Set up theme toggle for admin dashboard
    const adminThemeToggle = document.getElementById('adminThemeToggle');
    if (adminThemeToggle) {
        adminThemeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }
    
    // Theme toggle function
    function toggleTheme() {
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            setLightMode();
        } else {
            setDarkMode();
        }
    }
    
    // Set dark mode
    function setDarkMode() {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        
        // Update toggle icons in main website
        const darkIcon = document.getElementById('darkIcon');
        const lightIcon = document.getElementById('lightIcon');
        if (darkIcon && lightIcon) {
            darkIcon.style.display = 'none';
            lightIcon.style.display = 'inline-block';
        }
        
        // Update toggle icons in admin dashboard
        const adminDarkIcon = document.getElementById('adminDarkIcon');
        const adminLightIcon = document.getElementById('adminLightIcon');
        if (adminDarkIcon && adminLightIcon) {
            adminDarkIcon.style.display = 'none';
            adminLightIcon.style.display = 'inline-block';
        }
    }
    
    // Set light mode
    function setLightMode() {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        
        // Update toggle icons in main website
        const darkIcon = document.getElementById('darkIcon');
        const lightIcon = document.getElementById('lightIcon');
        if (darkIcon && lightIcon) {
            darkIcon.style.display = 'inline-block';
            lightIcon.style.display = 'none';
        }
        
        // Update toggle icons in admin dashboard
        const adminDarkIcon = document.getElementById('adminDarkIcon');
        const adminLightIcon = document.getElementById('adminLightIcon');
        if (adminDarkIcon && adminLightIcon) {
            adminDarkIcon.style.display = 'inline-block';
            adminLightIcon.style.display = 'none';
        }
    }
    
    // Listen for OS theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                setDarkMode();
            } else {
                setLightMode();
            }
        }
    });
}); 