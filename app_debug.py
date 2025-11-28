# Debug version for Render.com troubleshooting
import os
import sys

print("=== RENDER DEBUG INFO ===")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Environment variables: {dict(os.environ)}")

try:
    import flask
    print(f"✅ Flask version: {flask.__version__}")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    import flask_sqlalchemy
    print(f"✅ Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ Flask-SQLAlchemy import failed: {e}")

try:
    import PIL
    print(f"✅ Pillow version: {PIL.__version__}")
except ImportError as e:
    print(f"❌ Pillow import failed: {e}")

try:
    import psycopg2
    print(f"✅ psycopg2-binary version: {psycopg2.__version__}")
except ImportError as e:
    print(f"❌ psycopg2-binary import failed: {e}")

try:
    import gunicorn
    print(f"✅ Gunicorn version: {gunicorn.__version__}")
except ImportError as e:
    print(f"❌ Gunicorn import failed: {e}")

print("=== DEBUG COMPLETE ===")

# Now try to import the main app
try:
    from app import app
    print("✅ Main app imported successfully")
except Exception as e:
    print(f"❌ Main app import failed: {e}")
    import traceback
    traceback.print_exc()
