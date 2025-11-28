// Ntandostore JavaScript - Enhanced by Ntando Mods Team

// Utility Functions
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Global Variables
let isDarkMode = localStorage.getItem('theme') === 'dark';
let isPlaying = false;

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    initializeAnimations();
    initializeFormValidation();
    initializePerformanceOptimizations();
});

// Initialize App
function initializeApp() {
    console.log('🚀 Ntandostore initialized');
    setupTheme();
    setupLoadingScreen();
    setupServiceCards();
    setupTestimonialSlider();
    setupCountUpAnimations();
    setupParallaxEffects();
    setupIntersectionObserver();
}

// Setup Theme
function setupTheme() {
    const themeToggle = $('#themeToggle');
    const themeIcon = $('#themeIcon');
    
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        if (themeIcon) themeIcon.className = 'fas fa-sun';
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-mode');
    const themeIcon = $('#themeIcon');
    
    if (themeIcon) {
        themeIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    
    // Add transition effect
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
}

// Loading Screen
function setupLoadingScreen() {
    const loadingScreen = $('#loadingScreen');
    
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }, 1500);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Mobile Menu Toggle
    const mobileMenuToggle = $('#mobileMenuToggle');
    const navMenu = $('.nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');
        });
    }
    
    // Background Music
    setupBackgroundMusic();
    
    // Scroll to Top
    setupScrollToTop();
    
    // Smooth Scrolling
    setupSmoothScrolling();
    
    // Alert Close Buttons
    setupAlertClose();
    
    // Service Category Filter
    setupServiceFilter();
    
    // Live Chat
    setupLiveChat();
    
    // Order Tracking Widget
    setupTrackingWidget();
    
    // Navigation Active State
    setupNavigationActive();
}

// Background Music
function setupBackgroundMusic() {
    const bgMusic = $('#bgMusic');
    const musicToggle = $('#musicToggle');
    
    if (bgMusic && musicToggle) {
        musicToggle.addEventListener('click', () => {
            if (isPlaying) {
                bgMusic.pause();
                musicToggle.innerHTML = '<i class="fas fa-volume-mute"></i>';
            } else {
                bgMusic.play().catch(e => console.log('Audio play failed:', e));
                musicToggle.innerHTML = '<i class="fas fa-volume-up"></i>';
            }
            isPlaying = !isPlaying;
        });
        
        // Set volume
        bgMusic.volume = 0.3;
    }
}

// Scroll to Top
function setupScrollToTop() {
    const scrollToTopBtn = $('#scrollToTop');
    
    if (scrollToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.classList.add('show');
            } else {
                scrollToTopBtn.classList.remove('show');
            }
        });
        
        scrollToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// Smooth Scrolling
function setupSmoothScrolling() {
    $$('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = $(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Alert Close
function setupAlertClose() {
    $$('.alert-close').forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        });
    });
}

// Service Cards
function setupServiceCards() {
    const serviceCards = $$('.service-card');
    
    serviceCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Service Filter
function setupServiceFilter() {
    const categoryBtns = $$('.category-btn');
    const serviceCards = $$('.service-card');
    
    if (categoryBtns.length > 0 && serviceCards.length > 0) {
        categoryBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Update active state
                categoryBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const category = this.dataset.category;
                
                // Filter cards
                serviceCards.forEach(card => {
                    if (category === 'all' || card.dataset.category === category) {
                        card.style.display = 'block';
                        setTimeout(() => {
                            card.classList.add('animate-fadeIn');
                        }, 10);
                    } else {
                        card.style.display = 'none';
                        card.classList.remove('animate-fadeIn');
                    }
                });
            });
        });
    }
}

// Live Chat
function setupLiveChat() {
    const liveChatBtn = $('#liveChatBtn');
    
    if (liveChatBtn) {
        liveChatBtn.addEventListener('click', () => {
            window.open('https://wa.me/263718456744', '_blank');
        });
    }
}

// Tracking Widget
function setupTrackingWidget() {
    const trackingToggle = $('#trackingToggle');
    const trackingWidget = $('#trackingWidget');
    const trackingForm = $('#trackingForm');
    
    if (trackingToggle && trackingWidget) {
        trackingToggle.addEventListener('click', () => {
            trackingWidget.classList.toggle('active');
        });
        
        if (trackingForm) {
            trackingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const trackingInput = $('#trackingInput');
                const trackingNumber = trackingInput.value.trim();
                
                if (trackingNumber) {
                    window.location.href = `/track/${trackingNumber}`;
                }
            });
        }
    }
}

// Navigation Active State
function setupNavigationActive() {
    const currentPath = window.location.pathname;
    const navLinks = $$('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        }
    });
}

// Animations
function initializeAnimations() {
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
            }
        });
    }, observerOptions);
    
    // Observe elements
    $$('.service-card, .feature-card, .process-step, .stat-card').forEach(el => {
        observer.observe(el);
    });
}

// Testimonial Slider
function setupTestimonialSlider() {
    const reviewCards = $$('.review-card');
    
    if (reviewCards.length > 0) {
        let currentSlide = 0;
        
        function showSlide(index) {
            reviewCards.forEach((card, i) => {
                card.style.display = i === index ? 'block' : 'none';
            });
        }
        
        // Auto-rotate testimonials
        setInterval(() => {
            currentSlide = (currentSlide + 1) % reviewCards.length;
            showSlide(currentSlide);
        }, 5000);
        
        // Show first slide
        showSlide(0);
    }
}

// Count Up Animations
function setupCountUpAnimations() {
    const statNumbers = $$('.stat-number');
    
    const countUpObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const endValue = parseInt(target.textContent.replace(/[^0-9]/g, ''));
                animateCountUp(target, endValue);
                countUpObserver.unobserve(target);
            }
        });
    });
    
    statNumbers.forEach(stat => {
        countUpObserver.observe(stat);
    });
}

function animateCountUp(element, end) {
    let start = 0;
    const duration = 2000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const value = Math.floor(start + (end - start) * progress);
        element.textContent = value.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = end.toLocaleString();
        }
    }
    
    requestAnimationFrame(update);
}

// Parallax Effects
function setupParallaxEffects() {
    const heroSection = $('.hero');
    
    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = $$('.floating-card');
            
            parallaxElements.forEach((element, index) => {
                const speed = 0.5 + (index * 0.1);
                element.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }
}

// Intersection Observer
function initializeIntersectionObserver() {
    const options = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, options);
    
    // Observe elements for scroll animations
    $$('.service-card, .feature-card, .process-step, .trust-badges .badge').forEach(el => {
        observer.observe(el);
    });
}

// Form Validation
function initializeFormValidation() {
    const forms = $$('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = this.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    showError(field, 'This field is required');
                } else {
                    clearError(field);
                }
                
                // Email validation
                if (field.type === 'email' && field.value) {
                    if (!validateEmail(field.value)) {
                        isValid = false;
                        showError(field, 'Please enter a valid email address');
                    }
                }
                
                // Phone validation
                if (field.name === 'phone' && field.value) {
                    if (!validatePhone(field.value)) {
                        isValid = false;
                        showError(field, 'Please enter a valid phone number');
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
        
        // Clear errors on input
        form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('input', () => clearError(field));
        });
    });
}

function showError(field, message) {
    clearError(field);
    
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    errorElement.style.color = '#e74c3c';
    errorElement.style.fontSize = '0.9rem';
    errorElement.style.marginTop = '0.25rem';
    
    field.parentElement.appendChild(errorElement);
    field.style.borderColor = '#e74c3c';
}

function clearError(field) {
    const errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
    field.style.borderColor = '';
}

// Validation Functions
function validateEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email);
}

function validatePhone(phone) {
    const pattern = /^[\d\s\-\+\(\)]+$/;
    return pattern.test(phone) && phone.length >= 10;
}

// Performance Optimizations
function initializePerformanceOptimizations() {
    // Lazy load images
    lazyLoadImages();
    
    // Debounce scroll events
    debounceScrollEvents();
    
    // Optimize animations
    optimizeAnimations();
}

function lazyLoadImages() {
    const images = $$('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
}

function debounceScrollEvents() {
    let scrollTimeout;
    
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            window.cancelAnimationFrame(scrollTimeout);
        }
        
        scrollTimeout = window.requestAnimationFrame(() => {
            // Handle scroll-based animations
            handleScrollAnimations();
        });
    });
}

function handleScrollAnimations() {
    const scrolled = window.pageYOffset;
    const windowHeight = window.innerHeight;
    
    // Parallax effects
    const parallaxElements = $$('.parallax');
    parallaxElements.forEach(element => {
        const speed = element.dataset.speed || 0.5;
        element.style.transform = `translateY(${scrolled * speed}px)`;
    });
    
    // Fade in elements
    const fadeElements = $$('.fade-on-scroll');
    fadeElements.forEach(element => {
        const elementTop = element.offsetTop;
        const elementHeight = element.offsetHeight;
        
        if (scrolled + windowHeight > elementTop + elementHeight * 0.2) {
            element.classList.add('visible');
        }
    });
}

function optimizeAnimations() {
    // Reduce motion for users who prefer it
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--transition', 'none');
        
        // Disable parallax
        $$('.parallax').forEach(element => {
            element.style.transform = 'none';
        });
        
        // Disable auto-rotating testimonials
        clearInterval(window.testimonialInterval);
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Analytics (if enabled)
function trackEvent(eventName, properties = {}) {
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, properties);
    }
    
    // Console logging for development
    if (window.location.hostname === 'localhost') {
        console.log('📊 Analytics Event:', eventName, properties);
    }
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('🚨 JavaScript Error:', e.error);
    
    // Track errors in production
    if (window.location.hostname !== 'localhost') {
        trackEvent('javascript_error', {
            error_message: e.message,
            error_filename: e.filename,
            error_lineno: e.lineno,
            error_colno: e.colno
        });
    }
});

// Service Worker (for PWA functionality)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('✅ ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('❌ ServiceWorker registration failed:', error);
            });
    });
}

// Export functions for global access
window.NtandoStore = {
    toggleTheme,
    scrollToTop: () => window.scrollTo({ top: 0, behavior: 'smooth' }),
    trackEvent,
    validateEmail,
    validatePhone,
    debounce,
    throttle
};

console.log('🎯 Ntandostore JavaScript loaded successfully');
