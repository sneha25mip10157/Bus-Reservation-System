from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import config

Base = declarative_base()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(256), nullable=False)  # hashed
    is_admin = Column(Boolean, default=False)
    bookings = relationship("Booking", back_populates="user")

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    route = Column(String(200), nullable=False)
    total_seats = Column(Integer, default=40)
    available_seats = Column(Integer, default=40)
    fare = Column(Integer, default=0)
    depart_time = Column(String(50), nullable=True)
    extra = Column(Text, nullable=True)
    bookings = relationship("Booking", back_populates="bus")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    bus_id = Column(Integer, ForeignKey('buses.id'))
    seats = Column(Integer, default=1)
    booked_at = Column(DateTime, default=datetime.utcnow)
    passenger_name = Column(String(120), nullable=False)
    passenger_phone = Column(String(50), nullable=True)

    user = relationship("User", back_populates="bookings")
    bus = relationship("Bus", back_populates="bookings")

def init_db():
    Base.metadata.create_all(engine)
