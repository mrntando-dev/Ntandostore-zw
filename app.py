from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import secrets
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import hashlib
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from PIL import Image  # Added missing import
from sqlalchemy import text  # Added for database health check

app = Flask(__name__)

# Simple CSRF token generation (without Flask-WTF)
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def validate_csrf():
    token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    if not token or token != session.get('csrf_token'):
        flash('Security validation failed', 'error')
        return False
    return True

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Database configuration - use PostgreSQL for production
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///ntandostore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'"
    return response

# Session security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/ntandostore.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Ntandostore startup')

db = SQLAlchemy(app)

# Ensure upload directories exist
try:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)
    os.makedirs('logs', exist_ok=True)
except Exception as e:
    app.logger.error(f"Warning: Could not create upload directories: {e}")

# Input validation functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?[\d\s\-\(\)]{10,}$'
    return re.match(pattern, phone) is not None

def sanitize_input(input_string):
    if not input_string:
        return ""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    return sanitized.strip()

def validate_file_upload(file):
    if not file:
        return False, "No file provided"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    if not ('.' in file.filename and 
            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return False, "Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, SVG"
    
    # Check file size (already enforced by MAX_CONTENT_LENGTH)
    return True, "Valid file"

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Models
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Logo(db.Model):
    __tablename__ = 'logo'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))

class CompanyLogo(db.Model):
    __tablename__ = 'company_logo'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    tracking_number = db.Column(db.String(50), unique=True)
    payment_status = db.Column(db.String(20), default='pending')
    estimated_completion = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')
    ip_address = db.Column(db.String(45))

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    subscribed_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(100), unique=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

# Enhanced Services Configuration
SERVICES = {
    'business_email': {
        'name': 'Business Email',
        'price': 9.99,
        'description': 'Professional business email with custom domain',
        'category': 'communication',
        'features': ['Custom domain', '25GB storage', 'Spam protection', 'Mobile access'],
        'delivery_time': '24 hours',
        'revisions': 2
    },
    'domain': {
        'name': 'Domain Registration',
        'price': 24.99,
        'description': 'Custom domain with DNS configuration included',
        'category': 'hosting',
        'features': ['Free DNS setup', 'Domain privacy', 'Email forwarding', '24/7 support'],
        'delivery_time': '1-2 hours',
        'revisions': 1
    },
    'website_design': {
        'name': 'Website Design',
        'price': 35.00,
        'description': 'Professional website design + hosting, security, and upgrades',
        'category': 'web',
        'features': ['Responsive design', 'SEO optimized', 'CMS included', '1 year hosting', 'SSL certificate'],
        'delivery_time': '3-5 days',
        'revisions': 3
    },
    'business_card': {
        'name': 'Business Card Design',
        'price': 15.00,
        'description': 'Professional business card design',
        'category': 'design',
        'features': ['Double-sided design', 'Print-ready files', 'Multiple formats', 'Unlimited concepts'],
        'delivery_time': '48 hours',
        'revisions': 3
    },
    'business_logo': {
        'name': 'Business Logo Design',
        'price': 25.00,
        'description': 'Custom business logo design',
        'category': 'design',
        'features': ['Multiple concepts', 'Vector files', 'Color variations', 'Source files'],
        'delivery_time': '2-3 days',
        'revisions': 3
    },
    'website_hosting': {
        'name': 'Website Hosting',
        'price': 10.00,
        'description': 'Reliable website hosting per month',
        'category': 'hosting',
        'features': ['99.9% uptime', 'Daily backups', 'SSL certificate', '24/7 support'],
        'delivery_time': 'Instant',
        'revisions': 0
    },
    'website_security': {
        'name': 'Website Security',
        'price': 15.00,
        'description': 'SSL certificate and security setup',
        'category': 'security',
        'features': ['SSL certificate', 'Security audit', 'Malware scanning', 'Firewall setup'],
        'delivery_time': '24 hours',
        'revisions': 1
    },
    'wa_bot': {
        'name': 'WhatsApp Bot',
        'price': 50.00,
        'description': 'Custom WhatsApp bot for group management and automation',
        'category': 'automation',
        'features': ['Custom automation', 'Group management', 'Auto-responses', 'Analytics dashboard'],
        'delivery_time': '5-7 days',
        'revisions': 2
    },
    'premium_apps': {
        'name': 'Premium Apps',
        'price': 0.00,
        'description': 'Contact us for premium app solutions',
        'category': 'development',
        'features': ['Custom development', 'Native apps', 'Cross-platform', 'Maintenance included'],
        'delivery_time': 'Custom quote',
        'revisions': 5
    }
}

def generate_tracking_number():
    """Generate unique tracking number"""
    return f"NTD-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

def send_whatsapp_notification(order_data):
    """Send WhatsApp notification about new order"""
    try:
        message = f"""
🔔 NEW ORDER - Ntandostore

📦 Service: {order_data.get('service', 'Unknown')}
💰 Amount: ${order_data.get('amount', 0.00)}

👤 Customer Details:
Name: {order_data.get('customer_name', 'N/A')}
Email: {order_data.get('customer_email', 'N/A')}
Phone: {order_data.get('customer_phone', 'N/A')}

📝 Details: {order_data.get('details', 'No details provided')}

🕒 Order Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔍 Tracking: {order_data.get('tracking_number', 'N/A')}

Payment Number: +263786831091 (EcoCash/Innbucks)
        """
        
        app.logger.info(f"WhatsApp notification to +263718456744: {message}")
        # Here you would integrate with actual WhatsApp API
        return True
    except Exception as e:
        app.logger.error(f"WhatsApp notification error: {e}")
        return False

# Public Routes
@app.route('/')
def index():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(6).all()
        recent_orders = Order.query.filter_by(status='completed').order_by(Order.completed_date.desc()).limit(10).all()
        return render_template('index.html', 
                             services=SERVICES, 
                             company_logo=company_logo,
                             reviews=reviews,
                             recent_orders=recent_orders)
    except Exception as e:
        app.logger.error(f"Error in index route: {e}")
        return render_template('index.html', 
                             services=SERVICES, 
                             company_logo=None,
                             reviews=[],
                             recent_orders=[])

@app.route('/services')
def services():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        category = request.args.get('category', 'all')
        
        if category == 'all':
            filtered_services = SERVICES
        else:
            filtered_services = {k: v for k, v in SERVICES.items() if v['category'] == category}
        
        categories = {}
        for service_id, service in SERVICES.items():
            cat = service['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((service_id, service))
        
        return render_template('services.html', 
                             services=filtered_services,
                             categories=categories,
                             current_category=category,
                             company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in services route: {e}")
        return render_template('services.html', 
                             services=SERVICES, 
                             categories={},
                             current_category='all',
                             company_logo=None)

@app.route('/gallery')
def gallery():
    try:
        logos = Logo.query.order_by(Logo.upload_date.desc()).all()
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('gallery.html', logos=logos, company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in gallery route: {e}")
        return render_template('gallery.html', logos=[], company_logo=None)

@app.route('/testimonials')
def testimonials():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
        return render_template('testimonials.html', reviews=reviews, company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in testimonials route: {e}")
        return render_template('testimonials.html', reviews=[], company_logo=None)

@app.route('/faq')
def faq():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('faq.html', company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in FAQ route: {e}")
        return render_template('faq.html', company_logo=None)

@app.route('/privacy')
def privacy():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('privacy.html', company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in privacy route: {e}")
        return render_template('privacy.html', company_logo=None)

@app.route('/refund')
def refund():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('refund.html', company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in refund route: {e}")
        return render_template('refund.html', company_logo=None)

@app.route('/terms_pdf')
def terms_pdf():
    flash('PDF download will be available soon.', 'info')
    return redirect(url_for('index'))

@app.route('/order/<service_id>')
def order(service_id):
    if service_id not in SERVICES:
        flash('Service not found', 'error')
        return redirect(url_for('index'))
    
    try:
        service = SERVICES[service_id]
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('order.html', 
                             service=service, 
                             service_id=service_id, 
                             company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error in order route: {e}")
        service = SERVICES[service_id]
        return render_template('order.html', 
                             service=service, 
                             service_id=service_id, 
                             company_logo=None)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    if not validate_csrf():
        return redirect(url_for('index'))
    try:
        # Get and validate form data
        service_id = sanitize_input(request.form.get('service_id'))
        customer_name = sanitize_input(request.form.get('customer_name'))
        customer_email = sanitize_input(request.form.get('customer_email'))
        customer_phone = sanitize_input(request.form.get('customer_phone'))
        details = sanitize_input(request.form.get('details', ''))
        
        # Validate inputs
        if not service_id or service_id not in SERVICES:
            flash('Invalid service selected', 'error')
            return redirect(url_for('index'))
        
        if not customer_name or len(customer_name) < 2:
            flash('Please enter a valid name', 'error')
            return redirect(url_for('order', service_id=service_id))
        
        if not validate_email(customer_email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('order', service_id=service_id))
        
        if not validate_phone(customer_phone):
            flash('Please enter a valid phone number', 'error')
            return redirect(url_for('order', service_id=service_id))
        
        service = SERVICES[service_id]
        
        # Generate tracking number and estimated completion
        tracking_number = generate_tracking_number()
        delivery_time = service.get('delivery_time', '3-5 days')
        
        # Create order
        order = Order(
            service=service['name'],
            service_id=service_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            details=details,
            amount=service['price'],
            tracking_number=tracking_number
        )
        db.session.add(order)
        db.session.commit()
        
        # Send WhatsApp notification
        order_data = {
            'service': service['name'],
            'amount': service['price'],
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'details': details,
            'tracking_number': tracking_number
        }
        send_whatsapp_notification(order_data)
        
        flash(f'Order submitted successfully! Tracking number: {tracking_number}. Please make payment to +263786831091 (EcoCash/Innbucks)', 'success')
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f'Error submitting order: {str(e)}')
        db.session.rollback()
        flash(f'Error submitting order. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact_submit():
    if not validate_csrf():
        return redirect(url_for('index'))
    try:
        name = sanitize_input(request.form.get('name'))
        email = sanitize_input(request.form.get('email'))
        service = sanitize_input(request.form.get('service'))
        message = sanitize_input(request.form.get('message'))
        
        # Validate inputs
        if not name or len(name) < 2:
            flash('Please enter a valid name', 'error')
            return redirect(url_for('index') + '#contact')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('index') + '#contact')
        
        if not message or len(message) < 10:
            flash('Please enter a message with at least 10 characters', 'error')
            return redirect(url_for('index') + '#contact')
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Save contact message to database
        contact = ContactMessage(
            name=name,
            email=email,
            service=service,
            message=message,
            ip_address=client_ip
        )
        db.session.add(contact)
        db.session.commit()
        
        # Send notification
        notification_data = {
            'service': 'Contact Form',
            'amount': 0.00,
            'customer_name': name,
            'customer_email': email,
            'customer_phone': 'N/A',
            'details': f"Service Interest: {service}\nMessage: {message}"
        }
        send_whatsapp_notification(notification_data)
        
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('index') + '#contact')
    except Exception as e:
        app.logger.error(f"Contact form error: {e}")
        db.session.rollback()
        flash('Error sending message. Please try again.', 'error')
        return redirect(url_for('index') + '#contact')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if not validate_csrf():
        return redirect(url_for('index'))
    try:
        email = sanitize_input(request.form.get('email'))
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('index'))
        
        # Check if email already exists
        existing = Newsletter.query.filter_by(email=email).first()
        if existing:
            if existing.is_active:
                flash('You are already subscribed to our newsletter!', 'info')
            else:
                existing.is_active = True
                db.session.commit()
                flash('Welcome back! You have been re-subscribed.', 'success')
        else:
            # Add new subscriber
            unsubscribe_token = secrets.token_urlsafe(32)
            subscriber = Newsletter(
                email=email, 
                unsubscribe_token=unsubscribe_token
            )
            db.session.add(subscriber)
            db.session.commit()
            flash('Thank you for subscribing to our newsletter!', 'success')
        
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Subscribe error: {e}")
        db.session.rollback()
        flash('Error subscribing. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    try:
        subscriber = Newsletter.query.filter_by(unsubscribe_token=token).first()
        if subscriber:
            subscriber.is_active = False
            db.session.commit()
            flash('You have been successfully unsubscribed from our newsletter.', 'info')
        else:
            flash('Invalid unsubscribe link.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Unsubscribe error: {e}")
        flash('Error processing unsubscribe request.', 'error')
        return redirect(url_for('index'))

@app.route('/track/<tracking_number>')
def track_order(tracking_number):
    try:
        order = Order.query.filter_by(tracking_number=tracking_number).first()
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        
        if not order:
            flash('Order not found. Please check your tracking number.', 'error')
            return redirect(url_for('index'))
        
        return render_template('track.html', order=order, company_logo=company_logo)
    except Exception as e:
        app.logger.error(f"Error tracking order: {e}")
        flash('Error tracking order. Please try again.', 'error')
        return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            username = sanitize_input(request.form.get('username'))
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter username and password', 'error')
                return render_template('admin_login.html')
            
            admin = Admin.query.filter_by(username=username).first()
            
            # Check if account is locked
            if admin and admin.locked_until and admin.locked_until > datetime.utcnow():
                flash('Account is locked. Please try again later.', 'error')
                return render_template('admin_login.html')
            
            if admin and check_password_hash(admin.password, password):
                # Reset failed attempts
                admin.failed_login_attempts = 0
                admin.locked_until = None
                admin.last_login = datetime.utcnow()
                db.session.commit()
                
                session['admin_logged_in'] = True
                session['admin_username'] = username
                session.permanent = True
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                # Increment failed attempts
                if admin:
                    admin.failed_login_attempts += 1
                    if admin.failed_login_attempts >= 5:
                        admin.locked_until = datetime.utcnow() + timedelta(minutes=30)
                        flash('Account locked due to too many failed attempts. Please try again in 30 minutes.', 'error')
                    else:
                        remaining_attempts = 5 - admin.failed_login_attempts
                        flash(f'Invalid credentials. {remaining_attempts} attempts remaining.', 'error')
                    db.session.commit()
                else:
                    flash('Invalid credentials.', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash('Login error. Please try again.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        logos = Logo.query.order_by(Logo.upload_date.desc()).all()
        orders = Order.query.order_by(Order.order_date.desc()).limit(20).all()
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(10).all()
        
        # Statistics
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        in_progress_orders = Order.query.filter_by(status='in-progress').count()
        completed_orders = Order.query.filter_by(status='completed').count()
        total_revenue = db.session.query(db.func.sum(Order.amount)).filter_by(status='completed').scalar() or 0
        
        # Monthly revenue
        this_month = datetime.utcnow().replace(day=1)
        monthly_revenue = db.session.query(db.func.sum(Order.amount)).filter(
            Order.status == 'completed',
            Order.completed_date >= this_month
        ).scalar() or 0
        
        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'in_progress_orders': in_progress_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'new_messages': ContactMessage.query.filter_by(status='new').count()
        }
        
        return render_template('admin_dashboard.html', 
                             logos=logos, 
                             orders=orders,
                             contact_messages=contact_messages,
                             company_logo=company_logo,
                             stats=stats)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        return render_template('admin_dashboard.html', 
                             logos=[], 
                             orders=[],
                             contact_messages=[],
                             company_logo=None,
                             stats={})

@app.route('/admin/upload_logo', methods=['POST'])
@admin_required
def upload_logo():
    try:
        if 'logo_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['logo_file']
        client_name = sanitize_input(request.form.get('client_name', ''))
        
        is_valid, message = validate_file_upload(file)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('admin_dashboard'))
        
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', filename)
            file.save(filepath)
            
            # Generate file hash
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Optimize image if it's an image file
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img = Image.open(filepath)
                    img.save(filepath, optimize=True, quality=85)
                except Exception as e:
                    app.logger.warning(f"Could not optimize image: {e}")
            
            logo = Logo(
                filename=filename, 
                client_name=client_name,
                file_size=file_size,
                file_hash=file_hash
            )
            db.session.add(logo)
            db.session.commit()
            
            flash('Logo uploaded successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        db.session.rollback()
        flash(f'Error uploading logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/upload_company_logo', methods=['POST'])
@admin_required
def upload_company_logo():
    try:
        if 'company_logo_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['company_logo_file']
        
        is_valid, message = validate_file_upload(file)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('admin_dashboard'))
        
        if file:
            # Deactivate old logos
            CompanyLogo.query.update({CompanyLogo.is_active: False})
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"company_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'company', filename)
            file.save(filepath)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Optimize image
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img = Image.open(filepath)
                    img.save(filepath, optimize=True, quality=85)
                except Exception as e:
                    app.logger.warning(f"Could not optimize company logo: {e}")
            
            company_logo = CompanyLogo(filename=filename, is_active=True, file_size=file_size)
            db.session.add(company_logo)
            db.session.commit()
            
            flash('Company logo updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f"Company logo upload error: {e}")
        db.session.rollback()
        flash(f'Error uploading company logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_logo/<int:logo_id>', methods=['POST'])
@admin_required
def delete_logo(logo_id):
    try:
        logo = Logo.query.get_or_404(logo_id)
        
        # Delete file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', logo.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(logo)
        db.session.commit()
        
        flash('Logo deleted successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f"Delete error: {e}")
        db.session.rollback()
        flash(f'Error deleting logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status in ['pending', 'in-progress', 'completed', 'cancelled']:
            old_status = order.status
            order.status = new_status
            
            # Set completion date if completed
            if new_status == 'completed':
                order.completed_date = datetime.utcnow()
            
            db.session.commit()
            flash(f'Order status updated from {old_status} to {new_status}!', 'success')
        else:
            flash('Invalid status', 'error')
        
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f"Update status error: {e}")
        db.session.rollback()
        flash(f'Error updating order status: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy', 
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy', 
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('404.html', company_logo=company_logo), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('500.html', company_logo=company_logo), 500



# Initialize database
def init_db():
    """Initialize database tables and create default admin"""
    with app.app_context():
        try:
            # Import here to avoid circular imports
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("Creating database tables...")
                db.create_all()
                print("✓ Database tables created")
            else:
                print("✓ Database tables already exist")
            
            # Create default admin if not exists
            try:
                admin = Admin.query.filter_by(username='Ntando').first()
                if not admin:
                    hashed_password = generate_password_hash('Ntando')
                    admin = Admin(
                        username='Ntando',
                        password=hashed_password,
                        email='admin@ntandostore.com'
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("✓ Default admin created: username=Ntando, password=Ntando")
                else:
                    print("✓ Admin already exists")
            except Exception as admin_error:
                print(f"⚠ Admin creation error: {admin_error}")
                # Continue even if admin creation fails
                
            print("✓ Database initialization completed")
            return True
        except Exception as e:
            print(f"✗ Database initialization error: {e}")
            # Don't rollback on initialization errors
            return False

# Auto-initialize database on first request
@app.before_request
def initialize_database():
    """Initialize database on first request"""
    if not hasattr(app, 'db_initialized'):
        try:
            # Test if admin table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'admin' in inspector.get_table_names():
                app.db_initialized = True
            else:
                # Tables don't exist, initialize them
                print("Initializing database on first request...")
                if init_db():
                    app.db_initialized = True
        except Exception as e:
            print(f"Database check error: {e}")
            app.db_initialized = True  # Don't keep trying

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    
    # Create directories if they don't exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run in production mode
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
