import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from models import SessionLocal, Bus, Booking, User, init_db
from werkzeug.security import check_password_hash
from utils import export_bookings_csv
import os

init_db()

class GUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bus Reservation Pro - Desktop")
        self.session = SessionLocal()
        self.current_user = None
        self.build_login()

    def build_login(self):
        for w in self.root.winfo_children(): w.destroy()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky='w')
        username = ttk.Entry(frame); username.grid(row=0, column=1)
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky='w')
        password = ttk.Entry(frame, show='*'); password.grid(row=1, column=1)

        def do_login():
            u = self.session.query(User).filter_by(username=username.get()).first()
            if u and check_password_hash(u.password, password.get()):
                self.current_user = u
                messagebox.showinfo("Welcome", f"Logged in as {u.username}")
                if u.is_admin:
                    self.build_admin()
                else:
                    self.build_user()
            else:
                messagebox.showerror("Error","Invalid credentials")
        ttk.Button(frame, text="Login", command=do_login).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Quit", command=self.root.quit).grid(row=3, column=0, columnspan=2)

    def build_user(self):
        for w in self.root.winfo_children(): w.destroy()
        top = ttk.Frame(self.root, padding=10); top.pack(fill='x')
        ttk.Label(top, text=f"User: {self.current_user.username}").pack(side='left')
        ttk.Button(top, text="Logout", command=self.logout).pack(side='right')
        ttk.Button(top, text="My Bookings", command=self.show_my_bookings).pack(side='right', padx=5)

        tree = ttk.Treeview(self.root, columns=('route','avail','fare','time'), show='headings')
        for c,h in [('route','Route'),('avail','Seats'),('fare','Fare'),('time','Depart')]:
            tree.heading(c, text=h)
            tree.column(c, width=120)
        tree.pack(fill='both', expand=True)

        def load_buses():
            for i in tree.get_children(): tree.delete(i)
            buses = self.session.query(Bus).all()
            for b in buses:
                tree.insert('', 'end', iid=b.id, values=(b.route, f"{b.available_seats}/{b.total_seats}", b.fare, b.depart_time or ''))
        load_buses()

        def do_book():
            sel = tree.selection()
            if not sel: messagebox.showwarning("Select", "Select a bus"); return
            bus_id = int(sel[0]); bus = self.session.query(Bus).get(bus_id)
            q = simpledialog.askinteger("Seats", f"How many seats? (Available {bus.available_seats})", minvalue=1, maxvalue=bus.available_seats)
            if not q: return
            name = simpledialog.askstring("Passenger name", "Passenger name", initialvalue=self.current_user.username)
            phone = simpledialog.askstring("Phone", "Passenger phone")
            booking = Booking(user=self.current_user, bus=bus, seats=q, passenger_name=name, passenger_phone=phone)
            bus.available_seats -= q
            self.session.add(booking); self.session.commit()
            messagebox.showinfo("Booked", "Booking successful")
            load_buses()
        ttk.Button(self.root, text="Book Selected Bus", command=do_book).pack(pady=5)

    def show_my_bookings(self):
        top = tk.Toplevel(self.root); top.title("My bookings")
        tree = ttk.Treeview(top, columns=('bus','seats','passenger','when'), show='headings')
        for c in ['bus','seats','passenger','when']:
            tree.heading(c, text=c.title())
        tree.pack(fill='both', expand=True)
        bookings = self.session.query(Booking).filter_by(user_id=self.current_user.id).all()
        for b in bookings:
            tree.insert('', 'end', values=(b.bus.name if b.bus else '', b.seats, b.passenger_name, b.booked_at))

    def build_admin(self):
        for w in self.root.winfo_children(): w.destroy()
        top = ttk.Frame(self.root, padding=10); top.pack(fill='x')
        ttk.Label(top, text=f"Admin: {self.current_user.username}").pack(side='left')
        ttk.Button(top, text="Logout", command=self.logout).pack(side='right')
        ttk.Button(top, text="Export Bookings CSV", command=self.export_bookings).pack(side='right', padx=5)
        ttk.Button(top, text="Import Buses CSV", command=self.import_buses).pack(side='right', padx=5)

        columns = ('name','route','seats','fare','time')
        tree = ttk.Treeview(self.root, columns=columns, show='headings')
        for c in columns: tree.heading(c, text=c.title())
        tree.pack(fill='both', expand=True)

        def load():
            for i in tree.get_children(): tree.delete(i)
            for b in self.session.query(Bus).all():
                tree.insert('', 'end', iid=b.id, values=(b.name,b.route,f"{b.available_seats}/{b.total_seats}", b.fare, b.depart_time or ''))
        load()

        def add_bus():
            name = simpledialog.askstring("Name","Bus name")
            if not name: return
            route = simpledialog.askstring("Route","Route")
            total = simpledialog.askinteger("Seats","Total seats", initialvalue=40, minvalue=1)
            fare = simpledialog.askinteger("Fare","Fare", initialvalue=0)
            b = Bus(name=name, route=route, total_seats=total, available_seats=total, fare=fare)
            self.session.add(b); self.session.commit(); load()
        ttk.Button(self.root, text="Add Bus", command=add_bus).pack(pady=5)

        def delete_selected():
            sel = tree.selection()
            if not sel: messagebox.showwarning("Select","Select a bus"); return
            if not messagebox.askyesno("Confirm","Delete selected?"): return
            bus = self.session.query(Bus).get(int(sel[0])); self.session.delete(bus); self.session.commit(); load()
        ttk.Button(self.root, text="Delete Selected Bus", command=delete_selected).pack()

        def edit_selected():
            sel = tree.selection()
            if not sel: messagebox.showwarning("Select","Select a bus"); return
            bus = self.session.query(Bus).get(int(sel[0]))
            name = simpledialog.askstring("Name","Bus name", initialvalue=bus.name)
            route = simpledialog.askstring("Route","Route", initialvalue=bus.route)
            total = simpledialog.askinteger("Seats","Total seats", initialvalue=bus.total_seats)
            fare = simpledialog.askinteger("Fare","Fare", initialvalue=bus.fare)
            if name: bus.name=name; bus.route=route; bus.total_seats=total; bus.fare=fare
            bus.available_seats = max(0, bus.total_seats - sum([bk.seats for bk in bus.bookings]))
            self.session.commit(); load()
        ttk.Button(self.root, text="Edit Selected Bus", command=edit_selected).pack()

    def import_buses(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path, 'rb') as f:
            from utils import import_buses_csv
            added = import_buses_csv(f)
            messagebox.showinfo("Imported", f"Imported {added} buses")
            self.session.commit()

    def export_bookings(self):
        csv_text = export_bookings_csv()
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(csv_text)
        messagebox.showinfo("Export", "Bookings exported")

    def logout(self):
        self.current_user = None
        self.session.close()
        self.session = SessionLocal()
        self.build_login()

if __name__ == "__main__":
    root = tk.Tk()
    app = GUIApp(root)
    root.mainloop()
