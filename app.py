from flask import Flask, render_template, redirect, url_for, request, flash, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import SessionLocal, User, Bus, Booking, init_db
import config
from io import BytesIO
import utils
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple user class wrapper for Flask-Login
class FLUser(UserMixin):
    def __init__(self, user):
        self.id = str(user.id)
        self.username = user.username
        self.is_admin = user.is_admin

@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    u = session.query(User).filter_by(id=int(user_id)).first()
    session.close()
    if u:
        return FLUser(u)
    return None

@app.before_first_request
def ensure_db():
    init_db()

@app.route('/')
def index():
    session = SessionLocal()
    buses = session.query(Bus).all()
    session.close()
    return render_template('index.html', buses=buses)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session = SessionLocal()
        if session.query(User).filter_by(username=username).first():
            flash('Username already exists', 'danger')
            session.close()
            return redirect(url_for('register'))
        u = User(username=username, password=generate_password_hash(password), is_admin=False)
        session.add(u)
        session.commit()
        session.close()
        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        session = SessionLocal()
        u = session.query(User).filter_by(username=username).first()
        session.close()
        if u and check_password_hash(u.password, password):
            login_user(FLUser(u))
            flash('Logged in', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    session = SessionLocal()
    buses = session.query(Bus).all()
    bookings = session.query(Booking).all()
    session.close()
    return render_template('admin_dashboard.html', buses=buses, bookings=bookings)

# CRUD for buses
@app.route('/admin/bus/add', methods=['GET','POST'])
@login_required
def add_bus():
    if not current_user.is_admin:
        flash('Admin only', 'danger'); return redirect(url_for('index'))
    if request.method == 'POST':
        session = SessionLocal()
        name = request.form['name']
        route = request.form['route']
        total = int(request.form.get('total_seats') or 40)
        fare = int(request.form.get('fare') or 0)
        depart_time = request.form.get('depart_time','')
        b = Bus(name=name, route=route, total_seats=total, available_seats=total, fare=fare, depart_time=depart_time)
        session.add(b); session.commit(); session.close()
        flash('Bus added', 'success'); return redirect(url_for('admin_dashboard'))
    return render_template('bus_form.html', action='Add', bus=None)

@app.route('/admin/bus/edit/<int:bus_id>', methods=['GET','POST'])
@login_required
def edit_bus(bus_id):
    if not current_user.is_admin:
        flash('Admin only', 'danger'); return redirect(url_for('index'))
    session = SessionLocal()
    bus = session.query(Bus).filter_by(id=bus_id).first()
    if request.method == 'POST':
        bus.name = request.form['name']
        bus.route = request.form['route']
        bus.total_seats = int(request.form.get('total_seats') or bus.total_seats)
        bus.available_seats = max(0, bus.total_seats - sum([bk.seats for bk in bus.bookings]))
        bus.fare = int(request.form.get('fare') or bus.fare)
        bus.depart_time = request.form.get('depart_time','')
        session.commit(); session.close()
        flash('Bus updated', 'success'); return redirect(url_for('admin_dashboard'))
    session.close()
    return render_template('bus_form.html', action='Edit', bus=bus)

@app.route('/admin/bus/delete/<int:bus_id>', methods=['POST'])
@login_required
def delete_bus(bus_id):
    if not current_user.is_admin:
        flash('Admin only', 'danger'); return redirect(url_for('index'))
    session = SessionLocal()
    bus = session.query(Bus).filter_by(id=bus_id).first()
    if bus:
        session.delete(bus); session.commit()
        flash('Bus deleted', 'info')
    session.close()
    return redirect(url_for('admin_dashboard'))

# Import buses CSV
@app.route('/admin/import_buses', methods=['POST'])
@login_required
def import_buses():
    if not current_user.is_admin:
        flash('Admin only', 'danger'); return redirect(url_for('index'))
    file = request.files.get('file')
    if not file:
        flash('No file provided', 'danger'); return redirect(url_for('admin_dashboard'))
    added = utils.import_buses_csv(file)
    flash(f'Imported {added} buses', 'success')
    return redirect(url_for('admin_dashboard'))

# Export bookings CSV
@app.route('/admin/export_bookings')
@login_required
def export_bookings():
    if not current_user.is_admin:
        flash('Admin only', 'danger'); return redirect(url_for('index'))
    csv_text = utils.export_bookings_csv()
    response = make_response(csv_text)
    response.headers['Content-Disposition'] = 'attachment; filename=bookings.csv'
    response.mimetype = 'text/csv'
    return response

# User pages
@app.route('/buses')
def buses():
    session = SessionLocal()
    buses = session.query(Bus).all()
    session.close()
    return render_template('bus_list.html', buses=buses)

@app.route('/book/<int:bus_id>', methods=['GET','POST'])
@login_required
def book(bus_id):
    session = SessionLocal()
    bus = session.query(Bus).filter_by(id=bus_id).first()
    if not bus:
        session.close()
        flash('Bus not found', 'danger'); return redirect(url_for('buses'))
    if request.method == 'POST':
        seats = int(request.form.get('seats', 1))
        passenger_name = request.form.get('passenger_name', current_user.username)
        passenger_phone = request.form.get('passenger_phone','')
        if seats <= 0 or seats > bus.available_seats:
            flash('Invalid seat count', 'danger'); session.close(); return redirect(url_for('book', bus_id=bus_id))
        # create booking
        u_session = SessionLocal()
        user = u_session.query(User).filter_by(id=int(current_user.id)).first()
        booking = Booking(user=user, bus=bus, seats=seats, passenger_name=passenger_name, passenger_phone=passenger_phone)
        bus.available_seats -= seats
        u_session.add(booking)
        u_session.commit()
        u_session.close()
        flash('Booking successful', 'success')
        return redirect(url_for('my_bookings'))
    session.close()
    return render_template('book.html', bus=bus)

@app.route('/my_bookings')
@login_required
def my_bookings():
    session = SessionLocal()
    user = session.query(User).filter_by(id=int(current_user.id)).first()
    bookings = user.bookings if user else []
    session.close()
    return render_template('bookings.html', bookings=bookings)

if __name__ == "__main__":
    app.run(debug=True)
