from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='barber')  # admin, barber, receptionist
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    barber = db.relationship('Barber', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Barber(db.Model):
    __tablename__ = 'barbers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(120))
    commission_rate = db.Column(db.Float, default=40)
    years_experience = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    rating = db.Column(db.Float, default=5.0)
    total_clients = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0)
    is_available = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='barber', lazy=True)
    schedules = db.relationship('BarberSchedule', backref='barber', lazy=True)

class BarberSchedule(db.Model):
    __tablename__ = 'barber_schedules'
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('barbers.id'), nullable=False)
    day_of_week = db.Column(db.Integer)  # 0=Mon, 6=Sun
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    is_working = db.Column(db.Boolean, default=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    preferences = db.Column(db.Text)
    haircut_history = db.Column(db.Text)
    loyalty_points = db.Column(db.Integer, default=0)
    total_visits = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0)
    last_visit = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointments = db.relationship('Appointment', backref='customer', lazy=True)
    payments = db.relationship('Payment', backref='customer', lazy=True)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer)  # minutes
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    barber_id = db.Column(db.Integer, db.ForeignKey('barbers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no-show
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reminder_sent = db.Column(db.Boolean, default=False)
    service = db.relationship('Service', backref='appointments')
    payment = db.relationship('Payment', backref='appointment', uselist=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30))  # cash, mpesa, airtel, card
    status = db.Column(db.String(20), default='pending')  # pending, completed, refunded
    reference = db.Column(db.String(100))
    discount_amount = db.Column(db.Float, default=0)
    promo_code = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    barber_commission = db.Column(db.Float, default=0)
    receipt_number = db.Column(db.String(30))

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=5)
    unit_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    last_restocked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='supplier', lazy=True)

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_type = db.Column(db.String(10))  # percent, fixed
    discount_value = db.Column(db.Float)
    max_uses = db.Column(db.Integer, default=100)
    used_count = db.Column(db.Integer, default=0)
    valid_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class WalkInQueue(db.Model):
    __tablename__ = 'walk_in_queue'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    barber_id = db.Column(db.Integer, db.ForeignKey('barbers.id'))
    queue_number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='waiting')  # waiting, in-service, completed
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    served_at = db.Column(db.DateTime)
    service = db.relationship('Service')
    barber = db.relationship('Barber')
