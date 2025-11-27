from werkzeug.security import generate_password_hash, check_password_hash
from models import SessionLocal, Bus, Booking, User
import csv
import io

def hash_password(pw):
    return generate_password_hash(pw)

def verify_password(hash_pw, pw):
    return check_password_hash(hash_pw, pw)

# File handling: export bookings to CSV
def export_bookings_csv():
    session = SessionLocal()
    bookings = session.query(Booking).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','user','bus','seats','passenger_name','passenger_phone','booked_at'])
    for b in bookings:
        writer.writerow([b.id, b.user.username if b.user else '', b.bus.name if b.bus else '', b.seats, b.passenger_name, b.passenger_phone, b.booked_at])
    session.close()
    return output.getvalue()

# Import buses from CSV. CSV columns: name,route,total_seats,fare,depart_time,extra
def import_buses_csv(file_stream):
    session = SessionLocal()
    reader = csv.DictReader(io.StringIO(file_stream.read().decode('utf-8')))
    added = 0
    for row in reader:
        try:
            total = int(row.get('total_seats', 40))
        except:
            total = 40
        b = Bus(
            name=row.get('name', 'Unnamed'),
            route=row.get('route', ''),
            total_seats=total,
            available_seats=total,
            fare=int(row.get('fare', 0)),
            depart_time=row.get('depart_time', ''),
            extra=row.get('extra', '')
        )
        session.add(b)
        added += 1
    session.commit()
    session.close()
    return added
