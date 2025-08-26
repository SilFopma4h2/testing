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
    payment_method = db.Column(db.String(20), nullable=False)  # card, mpesa, bank, paypal
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
    payment_method = db.Column(db.String(20), nullable=False)  # mpesa, card, bank
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
        email_template = f"""
        <h2>Thank you for your generous donation!</h2>
        <p>Dear {data['donorName']},</p>
        <p>Thank you for your donation of ${amount} to Hope Foundation!</p>
        <p><strong>Donation Details:</strong></p>
        <ul>
        <li>Amount: ${amount}</li>
        <li>Type: {data.get('donationType', 'one-time').title()}</li>
        <li>Payment Method: {data['paymentMethod'].title()}</li>
        <li>Project: {data.get('projectSelection', 'general').replace('-', ' ').title()}</li>
        </ul>
        <p>Your donation will make a real difference in the lives of those we serve.</p>
        <p>A tax-deductible receipt will be sent separately.</p>
        <p>Best regards,<br>Hope Foundation Team</p>
        """
        
        send_email(data['donorEmail'], 'Thank you for your donation to Hope Foundation', email_template)
        
        return jsonify({
            'success': True, 
            'message': f'Thank you for your donation of ${amount}! Processing payment via {data["paymentMethod"]}...',
            'amount': amount,
            'paymentMethod': data['paymentMethod'],
            'transactionId': transaction_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

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

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)