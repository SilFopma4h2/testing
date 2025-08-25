// Main JavaScript for NGO Website MVP

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarNav = document.querySelector('.navbar-nav');
    
    if (navbarToggle && navbarNav) {
        navbarToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
        });
        
        // Close mobile menu when clicking on a link
        const navLinks = navbarNav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navbarNav.classList.remove('active');
            });
        });
    }
    
    // Active navigation highlighting
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.navbar-nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Contact form handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleContactForm();
        });
    }
    
    // Donation form handling
    const donateForm = document.getElementById('donateForm');
    if (donateForm) {
        donateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleDonationForm();
        });
    }
    
    // Newsletter subscription
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleNewsletterForm();
        });
    }
});

// Contact form handler
function handleContactForm() {
    const form = document.getElementById('contactForm');
    const formData = new FormData(form);
    
    // Get form values
    const name = formData.get('name');
    const email = formData.get('email');
    const subject = formData.get('subject');
    const message = formData.get('message');
    
    // Basic validation
    if (!name || !email || !message) {
        showAlert('Please fill in all required fields.', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    // Simulate form submission
    showAlert('Thank you for your message! We will get back to you soon.', 'success');
    form.reset();
}

// Donation form handler
function handleDonationForm() {
    const form = document.getElementById('donateForm');
    const formData = new FormData(form);
    
    const amount = formData.get('amount');
    const customAmount = formData.get('customAmount');
    const paymentMethod = formData.get('paymentMethod');
    const donorName = formData.get('donorName');
    const donorEmail = formData.get('donorEmail');
    
    const donationAmount = amount === 'custom' ? customAmount : amount;
    
    // Basic validation
    if (!donationAmount || donationAmount <= 0) {
        showAlert('Please enter a valid donation amount.', 'error');
        return;
    }
    
    if (!paymentMethod) {
        showAlert('Please select a payment method.', 'error');
        return;
    }
    
    if (!donorName || !donorEmail) {
        showAlert('Please fill in your name and email address.', 'error');
        return;
    }
    
    if (!isValidEmail(donorEmail)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    // Simulate payment processing
    showAlert(`Thank you for your donation of $${donationAmount}! Processing payment via ${paymentMethod}...`, 'success');
    
    // In a real implementation, this would redirect to the payment processor
    setTimeout(() => {
        window.location.href = 'thank-you.html?amount=' + donationAmount + '&method=' + paymentMethod;
    }, 2000);
}

// Newsletter form handler
function handleNewsletterForm() {
    const form = document.getElementById('newsletterForm');
    const formData = new FormData(form);
    
    const email = formData.get('email');
    
    if (!email || !isValidEmail(email)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    showAlert('Thank you for subscribing to our newsletter!', 'success');
    form.reset();
}

// Utility functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button type="button" class="alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add alert styles
    alert.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 600;
        z-index: 9999;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    alert.style.backgroundColor = colors[type] || colors.info;
    
    // Add close button styles
    const closeButton = alert.querySelector('.alert-close');
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        float: right;
        margin-left: 10px;
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// Add CSS animation for alerts
if (!document.querySelector('#alert-animations')) {
    const style = document.createElement('style');
    style.id = 'alert-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize any additional functionality
function initializeComponents() {
    // Add any component initialization here
    console.log('NGO Website MVP - JavaScript loaded successfully');
}