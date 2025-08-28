// Main JavaScript for NGO Website - Static Frontend

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
    
    console.log('NGO Website Static Frontend - JavaScript loaded successfully');
});

// Contact form handler (client-side only)
function handleContactForm() {
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
    
    // Simulate form submission (since no backend)
    setTimeout(() => {
        showAlert('Thank you for your message! We will get back to you soon.', 'success');
        form.reset();
        
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }, 1500);
}

// Donation form handler (client-side only)
function handleDonationForm() {
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
    
    // Simulate donation processing (since no backend)
    setTimeout(() => {
        showAlert('Thank you for your generous donation! You will be redirected to complete the payment.', 'success');
        
        // Redirect to thank you page after "successful" donation
        setTimeout(() => {
            window.location.href = `thank-you.html?amount=${donationAmount}&method=${data.paymentMethod}`;
        }, 2000);
    }, 1500);
}

// Newsletter form handler (client-side only)
function handleNewsletterForm() {
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
    
    // Simulate newsletter subscription (since no backend)
    setTimeout(() => {
        showAlert('Thank you for subscribing to our newsletter!', 'success');
        form.reset();
        
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }, 1500);
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
