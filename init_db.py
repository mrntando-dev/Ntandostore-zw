from app import app, db, Admin
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        try:
            print("Creating database tables...")
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
                print("✓ Default admin created: username=Ntando, password=Ntando")
            else:
                print("✓ Admin already exists")
            
            print("✓ Database initialization completed successfully")
        except Exception as e:
            print(f"✗ Database initialization error: {e}")
            raise

if __name__ == '__main__':
    init_database()
