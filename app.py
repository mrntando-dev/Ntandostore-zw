from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'ntandostore_secret_key_2024')

# Database configuration - use PostgreSQL for production
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///ntandostore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# Ensure upload directories exist
try:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create upload directories: {e}")

# Models
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Logo(db.Model):
    __tablename__ = 'logo'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class CompanyLogo(db.Model):
    __tablename__ = 'company_logo'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    subscribed_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Services Configuration
SERVICES = {
    'business_email': {
        'name': 'Business Email',
        'price': 9.99,
        'description': 'Professional business email with custom domain'
    },
    'domain': {
        'name': 'Domain Registration',
        'price': 24.99,
        'description': 'Custom domain with DNS configuration included'
    },
    'website_design': {
        'name': 'Website Design',
        'price': 35.00,
        'description': 'Professional website design + hosting, security, and upgrades'
    },
    'business_card': {
        'name': 'Business Card Design',
        'price': 15.00,
        'description': 'Professional business card design'
    },
    'business_logo': {
        'name': 'Business Logo Design',
        'price': 25.00,
        'description': 'Custom business logo design'
    },
    'website_hosting': {
        'name': 'Website Hosting',
        'price': 10.00,
        'description': 'Reliable website hosting per month'
    },
    'website_security': {
        'name': 'Website Security',
        'price': 15.00,
        'description': 'SSL certificate and security setup'
    },
    'wa_bot': {
        'name': 'WhatsApp Bot',
        'price': 50.00,
        'description': 'Custom WhatsApp bot for group management and automation'
    },
    'premium_apps': {
        'name': 'Premium Apps',
        'price': 0.00,
        'description': 'Contact us for premium app solutions'
    }
}

def send_whatsapp_notification(order_data):
    """Send WhatsApp notification about new order"""
    try:
        message = f"""
🔔 NEW ORDER - Ntandostore

📦 Service: {order_data['service']}
💰 Amount: ${order_data['amount']}

👤 Customer Details:
Name: {order_data['customer_name']}
Email: {order_data['customer_email']}
Phone: {order_data['customer_phone']}

📝 Details: {order_data['details']}

🕒 Order Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Payment Number: +263786831091 (EcoCash/Innbucks)
        """
        
        print(f"WhatsApp notification to +263718456744: {message}")
        return True
    except Exception as e:
        print(f"WhatsApp notification error: {e}")
        return False

# Public Routes
@app.route('/')
def index():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('index.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', services=SERVICES, company_logo=None)

@app.route('/services')
def services():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('services.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in services route: {e}")
        return render_template('services.html', services=SERVICES, company_logo=None)

@app.route('/gallery')
def gallery():
    try:
        logos = Logo.query.order_by(Logo.upload_date.desc()).all()
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('gallery.html', logos=logos, company_logo=company_logo)
    except Exception as e:
        print(f"Error in gallery route: {e}")
        return render_template('gallery.html', logos=[], company_logo=None)

@app.route('/testimonials')
def testimonials():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        # You can create a separate testimonials.html template or reuse index.html
        return render_template('index.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in testimonials route: {e}")
        return render_template('index.html', services=SERVICES, company_logo=None)

@app.route('/faq')
def faq():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        # You can create a separate faq.html template or reuse index.html
        return render_template('index.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in FAQ route: {e}")
        return render_template('index.html', services=SERVICES, company_logo=None)

@app.route('/privacy')
def privacy():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('index.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in privacy route: {e}")
        return render_template('index.html', services=SERVICES, company_logo=None)

@app.route('/refund')
def refund():
    try:
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        return render_template('index.html', services=SERVICES, company_logo=company_logo)
    except Exception as e:
        print(f"Error in refund route: {e}")
        return render_template('index.html', services=SERVICES, company_logo=None)

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
        return render_template('order.html', service=service, service_id=service_id, company_logo=company_logo)
    except Exception as e:
        print(f"Error in order route: {e}")
        service = SERVICES[service_id]
        return render_template('order.html', service=service, service_id=service_id, company_logo=None)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        service_id = request.form.get('service_id')
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        customer_phone = request.form.get('customer_phone')
        details = request.form.get('details', '')
        
        if service_id not in SERVICES:
            flash('Invalid service', 'error')
            return redirect(url_for('index'))
        
        service = SERVICES[service_id]
        
        # Create order
        order = Order(
            service=service['name'],
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            details=details,
            amount=service['price']
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
            'details': details
        }
        send_whatsapp_notification(order_data)
        
        flash('Order submitted successfully! Please make payment to +263786831091 (EcoCash/Innbucks)', 'success')
        return redirect(url_for('index'))
    
    except Exception as e:
        print(f'Error submitting order: {str(e)}')
        db.session.rollback()
        flash(f'Error submitting order. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact_submit():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        service = request.form.get('service')
        message = request.form.get('message')
        
        # Save contact message to database
        contact = ContactMessage(
            name=name,
            email=email,
            service=service,
            message=message
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
        print(f"Contact form error: {e}")
        db.session.rollback()
        flash('Error sending message. Please try again.', 'error')
        return redirect(url_for('index') + '#contact')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    try:
        email = request.form.get('email')
        
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
            subscriber = Newsletter(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('Thank you for subscribing to our newsletter!', 'success')
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Subscribe error: {e}")
        db.session.rollback()
        flash('Error subscribing. Please try again.', 'error')
        return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            admin = Admin.query.filter_by(username=username).first()
            
            if admin and check_password_hash(admin.password, password):
                session['admin_logged_in'] = True
                session['admin_username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials', 'error')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login error. Please try again.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login to access the admin dashboard', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        logos = Logo.query.order_by(Logo.upload_date.desc()).all()
        orders = Order.query.order_by(Order.order_date.desc()).limit(20).all()
        company_logo = CompanyLogo.query.filter_by(is_active=True).first()
        
        # Statistics
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        completed_orders = Order.query.filter_by(status='completed').count()
        total_revenue = db.session.query(db.func.sum(Order.amount)).filter_by(status='completed').scalar() or 0
        
        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue
        }
        
        return render_template('admin_dashboard.html', 
                             logos=logos, 
                             orders=orders, 
                             company_logo=company_logo,
                             stats=stats)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('admin_dashboard.html', 
                             logos=[], 
                             orders=[], 
                             company_logo=None,
                             stats={})

@app.route('/admin/upload_logo', methods=['POST'])
def upload_logo():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if 'logo_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['logo_file']
        client_name = request.form.get('client_name', '')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', filename)
            file.save(filepath)
            
            logo = Logo(filename=filename, client_name=client_name)
            db.session.add(logo)
            db.session.commit()
            
            flash('Logo uploaded successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"Upload error: {e}")
        db.session.rollback()
        flash(f'Error uploading logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/upload_company_logo', methods=['POST'])
def upload_company_logo():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if 'company_logo_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['company_logo_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if file:
            # Deactivate old logos
            CompanyLogo.query.update({CompanyLogo.is_active: False})
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"company_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'company', filename)
            file.save(filepath)
            
            company_logo = CompanyLogo(filename=filename, is_active=True)
            db.session.add(company_logo)
            db.session.commit()
            
            flash('Company logo updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"Company logo upload error: {e}")
        db.session.rollback()
        flash(f'Error uploading company logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_logo/<int:logo_id>', methods=['POST'])
def delete_logo(logo_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
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
        print(f"Delete error: {e}")
        db.session.rollback()
        flash(f'Error deleting logo: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status in ['pending', 'in-progress', 'completed', 'cancelled']:
            order.status = new_status
            db.session.commit()
            flash(f'Order status updated to {new_status}!', 'success')
        else:
            flash('Invalid status', 'error')
        
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"Update status error: {e}")
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
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', services=SERVICES, company_logo=None), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html', services=SERVICES, company_logo=None), 500

# Initialize database
def init_db():
    """Initialize database tables and create default admin"""
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created")
            
            # Create default admin if not exists
            admin = Admin.query.filter_by(username='Ntando').first()
            if not admin:
                admin = Admin(
                    username='Ntando',
                    password=generate_password_hash('Ntando')
                )
                db.session.add(admin)
                db.session.commit()
                print("✓ Default admin created: username=Ntando, password=Ntando")
            else:
                print("✓ Admin already exists")
                
            print("✓ Database initialization completed")
            return True
        except Exception as e:
            print(f"✗ Database initialization error: {e}")
            db.session.rollback()
            return False

# Auto-initialize database on first request
@app.before_request
def initialize_database():
    """Initialize database on first request"""
    if not hasattr(app, 'db_initialized'):
        try:
            # Test if tables exist
            db.session.execute(db.text('SELECT 1 FROM admin LIMIT 1'))
            app.db_initialized = True
        except:
            # Tables don't exist, initialize them
            print("Initializing database on first request...")
            if init_db():
                app.db_initialized = True

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
