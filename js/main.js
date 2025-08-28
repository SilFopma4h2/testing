// Main JavaScript for NGO Website MVP

document.addEventListener('DOMContentLoaded', function() {
    // Check login status and update navigation
    checkLoginStatusAndUpdateNav();
    
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
async function handleContactForm() {
    const form = document.getElementById('contactForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Get form values
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        subject: formData.get('subject'),
        message: formData.get('message'),
        newsletter: formData.get('newsletter') === '1'
    };
    
    // Basic validation
    if (!data.name || !data.email || !data.message) {
        showAlert('Please fill in all required fields.', 'error');
        return;
    }
    
    if (!isValidEmail(data.email)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="loading-spinner"></span>Sending...';
    
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            form.reset();
        } else {
            showAlert(result.message, 'error');
        }
    } catch (error) {
        showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    }
}

// Donation form handler
async function handleDonationForm() {
    const form = document.getElementById('donateForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    const data = {
        amount: formData.get('amount'),
        customAmount: formData.get('customAmount'),
        donationType: formData.get('donationType'),
        paymentMethod: formData.get('paymentMethod'),
        donorName: formData.get('donorName'),
        donorEmail: formData.get('donorEmail'),
        donorPhone: formData.get('donorPhone'),
        projectSelection: formData.get('projectSelection'),
        donorMessage: formData.get('donorMessage'),
        anonymous: formData.get('anonymous') === '1',
        newsletter: formData.get('newsletter') === '1'
    };
    
    const donationAmount = data.amount === 'custom' ? data.customAmount : data.amount;
    
    // Basic validation
    if (!donationAmount || donationAmount <= 0) {
        showAlert('Please enter a valid donation amount.', 'error');
        return;
    }
    
    if (!data.paymentMethod) {
        showAlert('Please select a payment method.', 'error');
        return;
    }
    
    if (!data.donorName || !data.donorEmail) {
        showAlert('Please fill in your name and email address.', 'error');
        return;
    }
    
    if (!isValidEmail(data.donorEmail)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="loading-spinner"></span>Processing...';
    
    try {
        const response = await fetch('/api/donate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            
            // Redirect to thank you page after successful donation
            setTimeout(() => {
                window.location.href = 'thank-you.html?amount=' + result.amount + '&method=' + result.paymentMethod;
            }, 2000);
        } else {
            showAlert(result.message, 'error');
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    } catch (error) {
        showAlert('Network error. Please check your connection and try again.', 'error');
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

// Newsletter form handler
async function handleNewsletterForm() {
    const form = document.getElementById('newsletterForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    const data = {
        email: formData.get('email')
    };
    
    if (!data.email || !isValidEmail(data.email)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="loading-spinner"></span>Subscribing...';
    
    try {
        const response = await fetch('/api/newsletter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            form.reset();
        } else {
            showAlert(result.message, 'error');
        }
    } catch (error) {
        showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    }
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
    
    // Create alert element with proper structure
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div class="alert-content">
            <div class="alert-message">${message}</div>
            <button type="button" class="alert-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}



// Initialize any additional functionality
function initializeComponents() {
    // Add any component initialization here
    console.log('NGO Website MVP - JavaScript loaded successfully');
}

// Authentication functions
async function checkLoginStatusAndUpdateNav() {
    try {
        const response = await fetch('/api/user/profile');
        if (response.ok) {
            const result = await response.json();
            updateNavForLoggedInUser(result.user);
        }
    } catch (error) {
        // User not logged in, keep default nav
    }
}

function updateNavForLoggedInUser(user) {
    const authLink = document.getElementById('authLink');
    if (authLink) {
        authLink.textContent = `Hi, ${user.first_name}`;
        authLink.href = 'login.html'; // Dashboard page
        authLink.classList.add('user-link');
    }
}

// Global logout function
async function globalLogout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
        });
        
        if (response.ok) {
            showAlert('Logged out successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    } catch (error) {
        showAlert('Error logging out', 'error');
    }
}
