from flask import Flask
from extensions import db, login_manager, mail
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'barbershop-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barbershop.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.appointments import appointments_bp
    from routes.customers import customers_bp
    from routes.barbers import barbers_bp
    from routes.payments import payments_bp
    from routes.inventory import inventory_bp
    from routes.reports import reports_bp
    from routes.queue import queue_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(barbers_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(queue_bp)

    with app.app_context():
        db.create_all()
        seed_data()

    return app

def seed_data():
    from models import User, Barber, Service, Product, Supplier
    from werkzeug.security import generate_password_hash

    if User.query.first():
        return

    admin = User(username='admin', email='admin@barbershop.com',
                 password_hash=generate_password_hash('admin123'), role='admin', full_name='Admin User')
    barber_user = User(username='john', email='john@barbershop.com',
                       password_hash=generate_password_hash('john123'), role='barber', full_name='John Kamau')
    receptionist = User(username='mary', email='mary@barbershop.com',
                        password_hash=generate_password_hash('mary123'), role='receptionist', full_name='Mary Auma')
    db.session.add_all([admin, barber_user, receptionist])
    db.session.commit()

    b1 = Barber(user_id=barber_user.id, specialization='Classic & Fades', commission_rate=40,
                years_experience=5, bio='Expert in classic cuts and modern fades.')
    b2 = Barber(user_id=admin.id, specialization='Beard & Grooming', commission_rate=45,
                years_experience=8, bio='Master barber specializing in beard styling.')
    db.session.add_all([b1, b2])

    services = [
        Service(name='Classic Haircut', price=1500, duration=30, category='haircut'),
        Service(name='Fade Cut', price=2000, duration=45, category='haircut'),
        Service(name='Beard Trim', price=1000, duration=20, category='beard'),
        Service(name='Hot Towel Shave', price=2500, duration=40, category='shave'),
        Service(name='Hair Wash & Style', price=1200, duration=25, category='styling'),
        Service(name='Kids Cut', price=1000, duration=25, category='haircut'),
        Service(name='Full Package', price=4500, duration=90, category='package'),
    ]
    db.session.add_all(services)

    supplier = Supplier(name='KK Barber Supplies', contact_name='Kevin Kariuki',
                        phone='+254700000001', email='kk@supplies.co.ke', address='Nairobi CBD')
    db.session.add(supplier)
    db.session.commit()

    products = [
        Product(name='Hair Gel (500ml)', category='styling', quantity=15, reorder_level=5,
                unit_price=350, selling_price=500, supplier_id=supplier.id, sku='HG001'),
        Product(name='Clipper Oil', category='equipment', quantity=8, reorder_level=3,
                unit_price=200, selling_price=350, supplier_id=supplier.id, sku='CO001'),
        Product(name='Shaving Cream', category='shaving', quantity=12, reorder_level=4,
                unit_price=450, selling_price=700, supplier_id=supplier.id, sku='SC001'),
        Product(name='After Shave Lotion', category='grooming', quantity=3, reorder_level=4,
                unit_price=600, selling_price=900, supplier_id=supplier.id, sku='AS001'),
    ]
    db.session.add_all(products)
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
