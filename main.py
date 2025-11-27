import sqlite3
import csv
import os
from getpass import getpass

DB = "bus_main.db"

# ----------------------------------------------------
# DATABASE SETUP
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        is_admin INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        route TEXT,
        total_seats INTEGER,
        available_seats INTEGER,
        fare INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bus_id INTEGER,
        seats INTEGER,
        passenger_name TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(bus_id) REFERENCES buses(id)
    )
    """)
    
    # Create default admin if not exists
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username, password, is_admin) VALUES (?,?,?)",
                    ('admin', 'admin123', 1))
        conn.commit()
        print("Default admin created (admin / admin123)")
    
    conn.commit()
    conn.close()

# ----------------------------------------------------
# USER LOGIN & REGISTRATION
# ----------------------------------------------------
def register_user():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    username = input("Enter username: ")
    password = getpass("Enter password: ")

    try:
        cur.execute("INSERT INTO users(username, password, is_admin) VALUES (?,?,0)",
                    (username, password))
        conn.commit()
        print("User registered successfully!")
    except Exception:
        print("Username already exists!")

    conn.close()


def login():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    username = input("Username: ")
    password = getpass("Password: ")

    cur.execute("SELECT id, is_admin FROM users WHERE username=? AND password=?",
                (username, password))
    user = cur.fetchone()
    conn.close()

    if user:
        print("Login successful!")
        return {"id": user[0], "username": username, "is_admin": user[1]}
    else:
        print("Invalid credentials.")
        return None

# ----------------------------------------------------
# ADMIN FUNCTIONS
# ----------------------------------------------------
def add_bus():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    name = input("Bus name: ")
    route = input("Route: ")
    seats = int(input("Total seats: "))
    fare = int(input("Ticket fare: "))

    cur.execute("INSERT INTO buses(name, route, total_seats, available_seats, fare) VALUES (?,?,?,?,?)",
                (name, route, seats, seats, fare))
    conn.commit()
    conn.close()
    print("Bus added successfully!")


def view_buses():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT * FROM buses")
    buses = cur.fetchall()
    conn.close()

    print("\n--- Available Buses ---")
    for b in buses:
        print(f"ID: {b[0]} | {b[1]} | {b[2]} | Seats: {b[4]}/{b[3]} | Fare: {b[5]}")
    print()


def delete_bus():
    view_buses()
    bus_id = int(input("Enter Bus ID to delete: "))

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("DELETE FROM buses WHERE id=?", (bus_id,))
    conn.commit()
    conn.close()

    print("Bus deleted!")


def export_bookings_csv():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    SELECT bookings.id, users.username, buses.name, bookings.seats, bookings.passenger_name
    FROM bookings
    JOIN users ON bookings.user_id = users.id
    JOIN buses ON bookings.bus_id = buses.id
    """)
    data = cur.fetchall()
    conn.close()

    with open("bookings_export.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["BookingID", "User", "Bus", "Seats", "Passenger"])
        writer.writerows(data)

    print("Bookings exported to bookings_export.csv")

# ----------------------------------------------------
# USER FUNCTIONS
# ----------------------------------------------------
def book_seat(user):
    view_buses()
    bus_id = int(input("Enter Bus ID: "))
    seats = int(input("How many seats? "))
    name = input("Passenger Name: ")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT available_seats FROM buses WHERE id=?", (bus_id,))
    available = cur.fetchone()

    if not available or seats > available[0]:
        print("Not enough seats available!")
        conn.close()
        return

    # Deduct seats
    cur.execute("UPDATE buses SET available_seats = available_seats - ? WHERE id=?", (seats, bus_id))

    # Store booking
    cur.execute("INSERT INTO bookings(user_id, bus_id, seats, passenger_name) VALUES (?,?,?,?)",
                (user["id"], bus_id, seats, name))

    conn.commit()
    conn.close()

    print("Seat booked successfully!")


def view_my_bookings(user):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    SELECT bookings.id, buses.name, buses.route, bookings.seats, bookings.passenger_name 
    FROM bookings 
    JOIN buses ON bookings.bus_id = buses.id
    WHERE user_id=?
    """, (user["id"],))
    bookings = cur.fetchall()
    conn.close()

    print("\n--- My Bookings ---")
    for bk in bookings:
        print(f"BookingID: {bk[0]} | Bus: {bk[1]} | Route: {bk[2]} | Seats: {bk[3]} | Passenger: {bk[4]}")
    print()

# ----------------------------------------------------
# MENUS
# ----------------------------------------------------
def admin_menu(user):
    while True:
        print("\n--- Admin Menu ---")
        print("1. Add Bus")
        print("2. View Buses")
        print("3. Delete Bus")
        print("4. Export Bookings CSV")
        print("5. Logout")

        ch = input("Enter choice: ")

        if ch == '1':
            add_bus()
        elif ch == '2':
            view_buses()
        elif ch == '3':
            delete_bus()
        elif ch == '4':
            export_bookings_csv()
        elif ch == '5':
            break
        else:
            print("Invalid choice")


def user_menu(user):
    while True:
        print("\n--- User Menu ---")
        print("1. View Buses")
        print("2. Book Seat")
        print("3. View My Bookings")
        print("4. Logout")

        ch = input("Enter choice: ")

        if ch == '1':
            view_buses()
        elif ch == '2':
            book_seat(user)
        elif ch == '3':
            view_my_bookings(user)
        elif ch == '4':
            break
        else:
            print("Invalid choice")

# ----------------------------------------------------
# MAIN PROGRAM
# ----------------------------------------------------
def main():
    init_db()

    print("\n======= BUS RESERVATION SYSTEM =======")

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            register_user()
        elif choice == '2':
            user = login()
            if user:
                if user["is_admin"] == 1:
                    admin_menu(user)
                else:
                    user_menu(user)
        elif choice == '3':
            print("Thank you for using the system!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
