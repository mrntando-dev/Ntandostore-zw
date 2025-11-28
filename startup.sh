#!/bin/bash

# Ntandostore Startup Script - Built by Ntando Mods Team

echo "🚀 Starting Ntandostore application..."

# Set Python version
export PYTHONPATH=$PYTHONPATH:/opt/render/project/src

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "✅ Virtual environment exists"
    source venv/bin/activate
fi

# Check if database needs initialization
echo "🔍 Checking database status..."
python3 -c "
import sys
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print('✅ Database tables ready')
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p static/uploads/logos
mkdir -p static/uploads/company
mkdir -p logs

# Set permissions
chmod 755 static/uploads
chmod 755 static/uploads/logos
chmod 755 static/uploads/company
chmod 755 logs

echo "✅ Startup complete!"

# Start the application
echo "🌟 Starting Gunicorn server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile -
