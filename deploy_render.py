#!/usr/bin/env python3
"""
Render.com deployment setup script for NtandoStore
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        sys.exit(1)

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'requirements.txt',
        'render.yaml',
        'Procfile',
        '.gitignore'
    ]
    
    print("🔍 Checking required files...")
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            sys.exit(1)
        else:
            print(f"✅ {file} exists")
    
    print("✅ All required files are present")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        'logs',
        'static/uploads/logos',
        'static/uploads/company'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created {directory}")

def test_app_locally():
    """Test if app can start locally"""
    print("🧪 Testing application startup...")
    try:
        import app
        print("✅ App imports successfully")
        
        # Test database initialization
        with app.app.app_context():
            app.initialize_on_startup()
            print("✅ Database initialization works")
            
    except Exception as e:
        print(f"❌ App test failed: {e}")
        sys.exit(1)

def main():
    print("🚀 Render.com Deployment Setup for NtandoStore")
    print("=" * 50)
    
    check_dependencies()
    create_directories()
    test_app_locally()
    
    print("\n✅ Deployment setup completed!")
    print("\n📋 Next Steps for Render.com Deployment:")
    print("1. Push your code to GitHub")
    print("2. Create a new Web Service on render.com")
    print("3. Connect your GitHub repository")
    print("4. Render will automatically detect render.yaml")
    print("5. Your app will be deployed and available at: https://your-app-name.onrender.com")
    print("\n🔑 Default Admin Credentials:")
    print("   Username: Ntando")
    print("   Password: Ntando")
    print("\n⚠️  Important: Change default password after first login!")

if __name__ == "__main__":
    main()
