from models import init_db, SessionLocal, User
from werkzeug.security import generate_password_hash

def create_admin():
    session = SessionLocal()
    admin = session.query(User).filter_by(username='admin').first()
    if not admin:
        a = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
        session.add(a)
        session.commit()
        print("Created default admin: username=admin password=admin123")
    else:
        print("Admin exists.")
    session.close()

if __name__ == "__main__":
    init_db()
    create_admin()
