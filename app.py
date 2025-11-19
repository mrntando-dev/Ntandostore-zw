from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.secret_key = 'ntandostore_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ntandostore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'company'), exist_ok=True)

# Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Logo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class CompanyLogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

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
    
    # Note: You'll need to integrate with a WhatsApp API service
    # For now, this is a placeholder. Popular options include:
    # - Twilio WhatsApp API
    # - WhatsApp Business API
    # - Third-party services like WhatAPI, etc.
    
    # Placeholder for WhatsApp integration
    print(f"WhatsApp notification to +263718456744: {message}")
    return True

@app.route('/')
def index():
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('index.html', services=SERVICES, company_logo=company_logo)

@app.route('/services')
def services():
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('services.html', services=SERVICES, company_logo=company_logo)

@app.route('/gallery')
def gallery():
    logos = Logo.query.order_by(Logo.upload_date.desc()).all()
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('gallery.html', logos=logos, company_logo=company_logo)

@app.route('/order/<service_id>')
def order(service_id):
    if service_id not in SERVICES:
        flash('Service not found', 'error')
        return redirect(url_for('index'))
    
    service = SERVICES[service_id]
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    return render_template('order.html', service=service, service_id=service_id, company_logo=company_logo)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        service_id = request.form.get('service_id')
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        customer_phone = request.form.get('customer_phone')
        details = request.form.get('details')
        
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
        flash(f'Error submitting order: {str(e)}', 'error')
        return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    logos = Logo.query.order_by(Logo.upload_date.desc()).all()
    orders = Order.query.order_by(Order.order_date.desc()).limit(20).all()
    company_logo = CompanyLogo.query.filter_by(is_active=True).first()
    
    return render_template('admin_dashboard.html', logos=logos, orders=orders, company_logo=company_logo)

@app.route('/admin/upload_logo', methods=['POST'])
def upload_logo():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'logo_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['logo_file']
    client_name = request.form.get('client_name', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', filename)
        file.save(filepath)
        
        logo = Logo(filename=filename, client_name=client_name)
        db.session.add(logo)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Logo uploaded successfully'})

@app.route('/admin/upload_company_logo', methods=['POST'])
def upload_company_logo():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'company_logo_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['company_logo_file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
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
        
        return jsonify({'success': True, 'message': 'Company logo updated successfully'})

@app.route('/admin/delete_logo/<int:logo_id>', methods=['POST'])
def delete_logo(logo_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    logo = Logo.query.get_or_404(logo_id)
    
    # Delete file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', logo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(logo)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Logo deleted successfully'})

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        admin = Admin.query.filter_by(username='Ntando').first()
        if not admin:
            admin = Admin(
                username='Ntando',
                password=generate_password_hash('Ntando')
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username=Ntando, password=Ntando")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
