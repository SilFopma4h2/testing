from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
import os
from dotenv import load_dotenv
import re

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
            newsletter=data.get('newsletter', False)
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
            newsletter=data.get('newsletter', False)
        )
        
        db.session.add(donation)
        
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
            'paymentMethod': data['paymentMethod']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later.'}), 500

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
            'newsletter_subscribers': Newsletter.query.count()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats'}), 500

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)