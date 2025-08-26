from flask import Flask, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import re
import hashlib
import json
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ngo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@hopefoundation.org')

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')  # Will be set by user

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    donations = db.relationship('Donation', backref='user', lazy=True)
    contacts = db.relationship('Contact', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    newsletter = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(20), nullable=False)  # bitcoin, ethereum
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100), unique=True)
    gateway_reference = db.Column(db.String(100))  # External payment gateway reference
    gateway_response = db.Column(db.Text)  # Store gateway response
    payment_type = db.Column(db.String(20), default='donation')  # donation, purchase, fee
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Link to donation if this payment is for a donation
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=True)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    donation_type = db.Column(db.String(20), nullable=False)  # one-time, monthly
    payment_method = db.Column(db.String(20), nullable=False)  # bitcoin, ethereum
    project = db.Column(db.String(50), default='general')
    message = db.Column(db.Text)
    anonymous = db.Column(db.Boolean, default=False)
    newsletter = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship to payment
    payment = db.relationship('Payment', backref='donation', uselist=False)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

# Enhanced Financial Models
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # program, admin, fundraising
    project = db.Column(db.String(50))  # optional project allocation
    date = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_url = db.Column(db.String(200))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0)
    project = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    goal_amount = db.Column(db.Float, nullable=False)
    raised_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    project_category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FinancialReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)  # annual, quarterly, monthly
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer)  # 1-4 for quarterly reports
    month = db.Column(db.Integer)  # 1-12 for monthly reports
    total_income = db.Column(db.Float, default=0)
    total_expenses = db.Column(db.Float, default=0)
    program_expenses = db.Column(db.Float, default=0)
    admin_expenses = db.Column(db.Float, default=0)
    fundraising_expenses = db.Column(db.Float, default=0)
    net_result = db.Column(db.Float, default=0)
    report_data = db.Column(db.Text)  # JSON data for detailed breakdown
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

# Utility functions
def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone(phone):
    if not phone:
        return True  # Phone is optional
    # Basic phone validation (allows international formats)
    pattern = r'^\+?[\d\s\-\(\)]{8,}$'
    return bool(re.match(pattern, phone))

def generate_transaction_id():
    """Generate a unique transaction ID"""
    import time
    import random
    timestamp = str(int(time.time()))
    random_part = str(random.randint(10000, 99999))
    return f"TXN{timestamp}{random_part}"

def require_login(f):
    """Decorator to require user login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please log in to access this feature.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def send_email(to, subject, template, **kwargs):
    """Send email notification"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=template,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_discord_notification(donation_data):
    """Send donation notification to Discord via webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not configured")
        return False
    
    try:
        # Create Discord embed message
        embed = {
            "title": "🎉 New Cryptocurrency Donation Received!",
            "description": f"A new donation of ${donation_data['amount']} has been submitted",
            "color": 0x28a745,  # Green color
            "fields": [
                {
                    "name": "💰 Amount",
                    "value": f"${donation_data['amount']}",
                    "inline": True
                },
                {
                    "name": "🪙 Cryptocurrency",
                    "value": donation_data['payment_method'].title(),
                    "inline": True
                },
                {
                    "name": "🎯 Project",
                    "value": donation_data['project'].replace('-', ' ').title(),
                    "inline": True
                },
                {
                    "name": "👤 Donor",
                    "value": "Anonymous" if donation_data.get('anonymous') else donation_data['donor_name'],
                    "inline": True
                },
                {
                    "name": "📧 Email",
                    "value": donation_data['donor_email'] if not donation_data.get('anonymous') else "Hidden",
                    "inline": True
                },
                {
                    "name": "🔗 Transaction ID",
                    "value": donation_data['transaction_id'],
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "footer": {
                "text": "Hope Foundation Crypto Donations"
            }
        }
        
        if donation_data.get('message'):
            embed["fields"].append({
                "name": "💌 Message",
                "value": donation_data['message'][:500] + ("..." if len(donation_data['message']) > 500 else ""),
                "inline": False
            })
        
        # Send webhook
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")
        return False

# Routes for serving static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field.replace("_", " ").title()} is required.'}), 400
        
        if not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        
        if len(data['password']) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long.'}), 400
        
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            if existing_user.username == data['username']:
                return jsonify({'success': False, 'message': 'Username already exists.'}), 400
            else:
                return jsonify({'success': False, 'message': 'Email already registered.'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the user
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred during registration.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('login') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Username/email and password are required.'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == data['login']) | (User.email == data['login'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'success': False, 'message': 'Invalid login credentials.'}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is deactivated.'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred during login.'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully!'})

@app.route('/api/user/profile', methods=['GET'])
@require_login
def get_profile():
    user = get_current_user()
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/user/profile', methods=['PUT'])
@require_login
def update_profile():
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Update allowed fields
        if data.get('first_name'):
            user.first_name = data['first_name']
        if data.get('last_name'):
            user.last_name = data['last_name']
        if data.get('phone') is not None:
            if data['phone'] and not validate_phone(data['phone']):
                return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
            user.phone = data['phone']
        
        # Email update requires validation
        if data.get('email') and data['email'] != user.email:
            if not validate_email_address(data['email']):
                return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
            
            existing = User.query.filter(User.email == data['email'], User.id != user.id).first()
            if existing:
                return jsonify({'success': False, 'message': 'Email already in use.'}), 400
            
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred updating profile.'}), 500

# API Routes
@app.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'success': False, 'message': 'Name, email, and message are required.'}), 400
        
        if not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        
        if not validate_phone(data.get('phone')):
            return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400
        
        # Create contact record
        contact = Contact(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            subject=data.get('subject', 'General Inquiry'),
            message=data['message'],
            newsletter=data.get('newsletter', False),
            user_id=session.get('user_id')  # Link to logged-in user if available
        )
        
        db.session.add(contact)
        
        # Add to newsletter if requested
        if data.get('newsletter'):
            existing_subscriber = Newsletter.query.filter_by(email=data['email']).first()
            if not existing_subscriber:
                newsletter = Newsletter(email=data['email'])
                db.session.add(newsletter)
        
        db.session.commit()
        
        # Send confirmation email
        email_template = f"""
        <h2>Thank you for contacting Hope Foundation!</h2>
        <p>Dear {data['name']},</p>
        <p>We have received your message and will get back to you within 24-48 hours.</p>
        <p><strong>Your message:</strong></p>
        <p>{data['message']}</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        
        send_email(data['email'], 'Thank you for contacting Hope Foundation', email_template)
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for your message! We will get back to you soon.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

@app.route('/api/donate', methods=['POST'])
def donation_form():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('donorName') or not data.get('donorEmail'):
            return jsonify({'success': False, 'message': 'Name and email are required.'}), 400
        
        if not validate_email_address(data['donorEmail']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        
        # Get donation amount
        amount = data.get('customAmount') if data.get('amount') == 'custom' else data.get('amount')
        if not amount or float(amount) <= 0:
            return jsonify({'success': False, 'message': 'Please enter a valid donation amount.'}), 400
        
        if not data.get('paymentMethod'):
            return jsonify({'success': False, 'message': 'Please select a payment method.'}), 400
        
        # Only allow cryptocurrency payments
        if data['paymentMethod'] not in ['bitcoin', 'ethereum']:
            return jsonify({'success': False, 'message': 'Only cryptocurrency donations are accepted. Please select Bitcoin or Ethereum.'}), 400
        
        # Create donation record
        donation = Donation(
            name=data['donorName'],
            email=data['donorEmail'],
            phone=data.get('donorPhone'),
            amount=float(amount),
            donation_type=data.get('donationType', 'one-time'),
            payment_method=data['paymentMethod'],
            project=data.get('projectSelection', 'general'),
            message=data.get('donorMessage'),
            anonymous=data.get('anonymous', False),
            newsletter=data.get('newsletter', False),
            user_id=session.get('user_id')  # Link to logged-in user if available
        )
        
        db.session.add(donation)
        db.session.flush()  # Get the donation ID
        
        # Create payment record for better tracking
        transaction_id = generate_transaction_id()
        payment = Payment(
            user_id=session.get('user_id'),
            amount=float(amount),
            payment_method=data['paymentMethod'],
            transaction_id=transaction_id,
            payment_type='donation',
            description=f"Donation to {data.get('projectSelection', 'general').replace('-', ' ').title()}",
            donation_id=donation.id
        )
        
        db.session.add(payment)
        donation.transaction_id = transaction_id
        
        # Add to newsletter if requested
        if data.get('newsletter'):
            existing_subscriber = Newsletter.query.filter_by(email=data['donorEmail']).first()
            if not existing_subscriber:
                newsletter = Newsletter(email=data['donorEmail'])
                db.session.add(newsletter)
        
        db.session.commit()
        
        # Send confirmation email
        crypto_addresses = {
            'bitcoin': os.getenv('BITCOIN_ADDRESS', 'BITCOIN_ADDRESS_NOT_SET'),
            'ethereum': os.getenv('ETHEREUM_ADDRESS', 'ETHEREUM_ADDRESS_NOT_SET')
        }
        
        crypto_address = crypto_addresses.get(data['paymentMethod'], 'N/A')
        
        email_template = f"""
        <h2>Thank you for your cryptocurrency donation!</h2>
        <p>Dear {data['donorName']},</p>
        <p>Thank you for your {data['paymentMethod'].title()} donation of ${amount} to Hope Foundation!</p>
        <p><strong>Donation Details:</strong></p>
        <ul>
        <li>Amount: ${amount}</li>
        <li>Type: {data.get('donationType', 'one-time').title()}</li>
        <li>Cryptocurrency: {data['paymentMethod'].title()}</li>
        <li>Project: {data.get('projectSelection', 'general').replace('-', ' ').title()}</li>
        <li>Transaction ID: {transaction_id}</li>
        </ul>
        <p><strong>To complete your donation, please send the cryptocurrency to:</strong></p>
        <p style="background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all;">
        {crypto_address}
        </p>
        <p><strong>Important:</strong> Please send exactly ${amount} worth of {data['paymentMethod'].title()} to the address above.</p>
        <p>Once your transaction is confirmed on the blockchain, we will process your donation.</p>
        <p>Your donation will make a real difference in the lives of those we serve.</p>
        <p>A tax-deductible receipt will be sent once the transaction is confirmed.</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        
        send_email(data['donorEmail'], f'Complete your {data["paymentMethod"].title()} donation to Hope Foundation', email_template)
        
        # Send Discord notification
        discord_data = {
            'amount': amount,
            'payment_method': data['paymentMethod'],
            'project': data.get('projectSelection', 'general'),
            'donor_name': data['donorName'],
            'donor_email': data['donorEmail'],
            'anonymous': data.get('anonymous', False),
            'message': data.get('donorMessage', ''),
            'transaction_id': transaction_id
        }
        send_discord_notification(discord_data)
        
        return jsonify({
            'success': True, 
            'message': f'Thank you! Please send ${amount} worth of {data["paymentMethod"].title()} to complete your donation. Check your email for wallet address details.',
            'amount': amount,
            'paymentMethod': data['paymentMethod'],
            'transactionId': transaction_id,
            'walletAddress': crypto_address
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

@app.route('/api/crypto-addresses', methods=['GET'])
def get_crypto_addresses():
    """Get cryptocurrency addresses for donations"""
    crypto_addresses = {
        'bitcoin': os.getenv('BITCOIN_ADDRESS', 'BITCOIN_ADDRESS_NOT_SET'),
        'ethereum': os.getenv('ETHEREUM_ADDRESS', 'ETHEREUM_ADDRESS_NOT_SET')
    }
    return jsonify({'success': True, 'addresses': crypto_addresses})

# Payment Management Routes
@app.route('/api/payments', methods=['GET'])
@require_login
def get_user_payments():
    """Get all payments for the logged-in user"""
    try:
        user = get_current_user()
        payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
        
        payment_list = []
        for payment in payments:
            payment_dict = {
                'id': payment.id,
                'amount': payment.amount,
                'currency': payment.currency,
                'payment_method': payment.payment_method,
                'payment_status': payment.payment_status,
                'transaction_id': payment.transaction_id,
                'payment_type': payment.payment_type,
                'description': payment.description,
                'created_at': payment.created_at.isoformat(),
                'donation_id': payment.donation_id
            }
            payment_list.append(payment_dict)
        
        return jsonify({'success': True, 'payments': payment_list})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch payments'}), 500

@app.route('/api/user/donations', methods=['GET'])
@require_login
def get_user_donations():
    """Get all donations for the logged-in user"""
    try:
        user = get_current_user()
        donations = Donation.query.filter_by(user_id=user.id).order_by(Donation.created_at.desc()).all()
        
        donation_list = []
        for donation in donations:
            donation_dict = {
                'id': donation.id,
                'amount': donation.amount,
                'donation_type': donation.donation_type,
                'payment_method': donation.payment_method,
                'project': donation.project,
                'status': donation.status,
                'transaction_id': donation.transaction_id,
                'created_at': donation.created_at.isoformat(),
                'anonymous': donation.anonymous
            }
            donation_list.append(donation_dict)
        
        return jsonify({'success': True, 'donations': donation_list})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch donations'}), 500

@app.route('/api/user/dashboard', methods=['GET'])
@require_login
def user_dashboard():
    """Get dashboard data for logged-in user"""
    try:
        user = get_current_user()
        
        # Get user statistics
        total_donations = db.session.query(db.func.sum(Donation.amount)).filter_by(user_id=user.id).scalar() or 0
        donation_count = Donation.query.filter_by(user_id=user.id).count()
        recent_donations = Donation.query.filter_by(user_id=user.id).order_by(Donation.created_at.desc()).limit(5).all()
        
        dashboard_data = {
            'user': user.to_dict(),
            'stats': {
                'total_donated': float(total_donations),
                'donation_count': donation_count,
                'last_donation': recent_donations[0].created_at.isoformat() if recent_donations else None
            },
            'recent_donations': [
                {
                    'amount': d.amount,
                    'project': d.project,
                    'date': d.created_at.isoformat(),
                    'status': d.status
                } for d in recent_donations
            ]
        }
        
        return jsonify({'success': True, 'dashboard': dashboard_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch dashboard data'}), 500

@app.route('/api/newsletter', methods=['POST'])
def newsletter_form():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not validate_email_address(data['email']):
            return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        
        # Check if already subscribed
        existing = Newsletter.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({
                'success': True, 
                'message': 'You are already subscribed to our newsletter!'
            })
        
        # Create newsletter subscription
        newsletter = Newsletter(email=data['email'])
        db.session.add(newsletter)
        db.session.commit()
        
        # Send welcome email
        email_template = f"""
        <h2>Welcome to Hope Foundation Newsletter!</h2>
        <p>Thank you for subscribing to our newsletter.</p>
        <p>You will receive regular updates about our projects, impact stories, and ways to get involved.</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        
        send_email(data['email'], 'Welcome to Hope Foundation Newsletter', email_template)
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for subscribing to our newsletter!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

# Admin routes (basic)
@app.route('/api/admin/stats')
def admin_stats():
    try:
        stats = {
            'contacts': Contact.query.count(),
            'donations': Donation.query.count(),
            'total_donations': db.session.query(db.func.sum(Donation.amount)).scalar() or 0,
            'newsletter_subscribers': Newsletter.query.count(),
            'registered_users': User.query.count(),
            'payments': Payment.query.count(),
            'recent_users': User.query.order_by(User.created_at.desc()).limit(5).all()
        }
        
        # Convert recent users to dict
        stats['recent_users'] = [user.to_dict() for user in stats['recent_users']]
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats'}), 500

# Enhanced Financial API Endpoints
@app.route('/api/financial/overview')
def financial_overview():
    try:
        # Calculate current year financial data
        current_year = datetime.now().year
        
        # Total donations this year
        year_donations = db.session.query(db.func.sum(Donation.amount)).filter(
            db.extract('year', Donation.created_at) == current_year
        ).scalar() or 0
        
        # Total expenses this year
        year_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.status == 'approved'
        ).scalar() or 0
        
        # Expense breakdown by category
        expense_breakdown = db.session.query(
            Expense.category,
            db.func.sum(Expense.amount).label('total')
        ).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.status == 'approved'
        ).group_by(Expense.category).all()
        
        # Campaign progress
        active_campaigns = Campaign.query.filter_by(status='active').all()
        campaign_data = []
        for campaign in active_campaigns:
            progress = (campaign.raised_amount / campaign.goal_amount * 100) if campaign.goal_amount > 0 else 0
            campaign_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'goal': campaign.goal_amount,
                'raised': campaign.raised_amount,
                'progress': round(progress, 1)
            })
        
        return jsonify({
            'year': current_year,
            'total_donations': year_donations,
            'total_expenses': year_expenses,
            'net_result': year_donations - year_expenses,
            'expense_breakdown': {row[0]: row[1] for row in expense_breakdown},
            'active_campaigns': campaign_data,
            'expense_ratio': {
                'program': round((expense_breakdown[0][1] if expense_breakdown and expense_breakdown[0][0] == 'program' else 0) / year_expenses * 100, 1) if year_expenses > 0 else 0,
                'admin': round((expense_breakdown[1][1] if len(expense_breakdown) > 1 and expense_breakdown[1][0] == 'admin' else 0) / year_expenses * 100, 1) if year_expenses > 0 else 0,
                'fundraising': round((expense_breakdown[2][1] if len(expense_breakdown) > 2 and expense_breakdown[2][0] == 'fundraising' else 0) / year_expenses * 100, 1) if year_expenses > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'error': 'Failed to fetch financial overview'}), 500

@app.route('/api/financial/campaigns')
def get_campaigns():
    try:
        campaigns = Campaign.query.filter_by(status='active').all()
        campaign_list = []
        for campaign in campaigns:
            progress = (campaign.raised_amount / campaign.goal_amount * 100) if campaign.goal_amount > 0 else 0
            campaign_list.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'goal_amount': campaign.goal_amount,
                'raised_amount': campaign.raised_amount,
                'progress': round(progress, 1),
                'project_category': campaign.project_category,
                'start_date': campaign.start_date.isoformat() if campaign.start_date else None,
                'end_date': campaign.end_date.isoformat() if campaign.end_date else None
            })
        return jsonify(campaign_list)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch campaigns'}), 500

@app.route('/api/financial/impact-calculator', methods=['POST'])
def impact_calculator():
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        # Impact calculations based on average costs
        impact = {
            'clean_water_families': int(amount / 25),  # $25 per family per year
            'school_meals': int(amount / 0.50),       # $0.50 per meal
            'medical_treatments': int(amount / 15),    # $15 per basic treatment
            'educational_supplies': int(amount / 10),  # $10 per student supply kit
            'emergency_kits': int(amount / 40)         # $40 per emergency family kit
        }
        
        return jsonify({
            'donation_amount': amount,
            'impact': impact,
            'message': f'Your ${amount} donation can make a significant impact!'
        })
    except Exception as e:
        return jsonify({'error': 'Failed to calculate impact'}), 500

@app.route('/api/financial/transparency')
def financial_transparency():
    try:
        # Get latest financial report or generate current data
        current_year = datetime.now().year
        
        # Calculate transparency metrics
        total_donations = db.session.query(db.func.sum(Donation.amount)).filter(
            db.extract('year', Donation.created_at) == current_year
        ).scalar() or 0
        
        total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.status == 'approved'
        ).scalar() or 0
        
        # Expense breakdown
        program_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.category == 'program',
            Expense.status == 'approved'
        ).scalar() or 0
        
        admin_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.category == 'admin',
            Expense.status == 'approved'
        ).scalar() or 0
        
        fundraising_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            db.extract('year', Expense.date) == current_year,
            Expense.category == 'fundraising',
            Expense.status == 'approved'
        ).scalar() or 0
        
        return jsonify({
            'year': current_year,
            'total_income': total_donations,
            'total_expenses': total_expenses,
            'program_percentage': round((program_expenses / total_expenses * 100), 1) if total_expenses > 0 else 0,
            'admin_percentage': round((admin_expenses / total_expenses * 100), 1) if total_expenses > 0 else 0,
            'fundraising_percentage': round((fundraising_expenses / total_expenses * 100), 1) if total_expenses > 0 else 0,
            'efficiency_rating': 'Excellent' if (program_expenses / total_expenses * 100) > 80 else 'Good' if (program_expenses / total_expenses * 100) > 70 else 'Fair',
            'program_expenses': program_expenses,
            'admin_expenses': admin_expenses,
            'fundraising_expenses': fundraising_expenses
        })
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transparency data'}), 500

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)