from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Appointment, Customer, Barber, Service, Payment
from extensions import db
from datetime import datetime, date, time, timedelta
import random, string

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments')
@login_required
def index():
    filter_date = request.args.get('date', date.today().isoformat())
    filter_status = request.args.get('status', '')
    query = Appointment.query.filter_by(appointment_date=filter_date)
    if filter_status:
        query = query.filter_by(status=filter_status)
    appointments = query.order_by(Appointment.appointment_time).all()
    barbers = Barber.query.all()
    services = Service.query.filter_by(is_active=True).all()
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('appointments/index.html',
        appointments=appointments, barbers=barbers, services=services,
        customers=customers, filter_date=filter_date, filter_status=filter_status)

@appointments_bp.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        cid = request.form.get('customer_id')
        if not cid:
            # Create new customer
            customer = Customer(
                name=request.form.get('customer_name'),
                phone=request.form.get('customer_phone'),
                email=request.form.get('customer_email', '')
            )
            db.session.add(customer)
            db.session.flush()
            cid = customer.id
        appt = Appointment(
            customer_id=cid,
            barber_id=request.form.get('barber_id'),
            service_id=request.form.get('service_id'),
            appointment_date=request.form.get('appointment_date'),
            appointment_time=request.form.get('appointment_time'),
            notes=request.form.get('notes', '')
        )
        db.session.add(appt)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointments.index'))
    barbers = Barber.query.all()
    services = Service.query.filter_by(is_active=True).all()
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('appointments/book.html', barbers=barbers, services=services, customers=customers)

@appointments_bp.route('/appointments/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    appt = Appointment.query.get_or_404(id)
    new_status = request.form.get('status')
    appt.status = new_status
    if new_status == 'completed':
        service = Service.query.get(appt.service_id)
        barber = Barber.query.get(appt.barber_id)
        customer = Customer.query.get(appt.customer_id)
        # Create payment record
        receipt_no = 'RCP' + ''.join(random.choices(string.digits, k=6))
        commission = service.price * (barber.commission_rate / 100)
        payment = Payment(
            appointment_id=appt.id,
            customer_id=appt.customer_id,
            amount=service.price,
            method=request.form.get('payment_method', 'cash'),
            status='completed',
            receipt_number=receipt_no,
            barber_commission=commission
        )
        db.session.add(payment)
        barber.total_clients += 1
        barber.total_revenue += service.price
        customer.total_visits += 1
        customer.total_spent += service.price
        customer.last_visit = datetime.utcnow()
        customer.loyalty_points += int(service.price / 100)
    db.session.commit()
    flash(f'Appointment marked as {new_status}', 'success')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    appt = Appointment.query.get_or_404(id)
    appt.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointments.index'))

@appointments_bp.route('/api/barber-slots')
@login_required
def barber_slots():
    barber_id = request.args.get('barber_id')
    appt_date = request.args.get('date')
    booked = [a.appointment_time for a in Appointment.query.filter_by(
        barber_id=barber_id, appointment_date=appt_date, status='scheduled').all()]
    all_slots = []
    for h in range(8, 20):
        for m in ['00', '30']:
            slot = f"{h:02d}:{m}"
            all_slots.append({'time': slot, 'available': slot not in booked})
    return jsonify(all_slots)
