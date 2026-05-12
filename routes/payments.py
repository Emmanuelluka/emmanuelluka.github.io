from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.decorators import admin_required
from models import Payment, PromoCode, Customer, Appointment, Service, Barber
from extensions import db
from datetime import datetime, date
from sqlalchemy import func
import random, string

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/payments')
@login_required
def index():
    filter_date = request.args.get('date', '')
    filter_method = request.args.get('method', '')
    query = Payment.query
    if filter_date:
        query = query.filter(func.date(Payment.created_at) == filter_date)
    if filter_method:
        query = query.filter_by(method=filter_method)
    payments = query.order_by(Payment.created_at.desc()).limit(50).all()
    today = date.today()
    today_total = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.created_at) == today, Payment.status == 'completed').scalar() or 0
    return render_template('payments/index.html', payments=payments,
                           today_total=today_total, filter_date=filter_date, filter_method=filter_method)

@payments_bp.route('/payments/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        promo = request.form.get('promo_code', '')
        discount = 0
        if promo:
            code = PromoCode.query.filter_by(code=promo.upper(), is_active=True).first()
            if code and code.used_count < code.max_uses:
                discount = code.discount_value if code.discount_type == 'fixed' else amount * code.discount_value / 100
                code.used_count += 1
        appt_id = request.form.get('appointment_id') or None
        barber_id = request.form.get('barber_id')
        commission = 0
        if barber_id:
            barber = Barber.query.get(barber_id)
            if barber:
                commission = (amount - discount) * barber.commission_rate / 100
        receipt_no = 'RCP' + ''.join(random.choices(string.digits, k=6))
        p = Payment(
            appointment_id=appt_id,
            customer_id=request.form.get('customer_id') or None,
            amount=amount - discount,
            method=request.form.get('method'),
            status='completed',
            discount_amount=discount,
            promo_code=promo.upper() if promo else None,
            receipt_number=receipt_no,
            barber_commission=commission
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Payment recorded! Receipt: {receipt_no}', 'success')
        return redirect(url_for('payments.receipt', id=p.id))
    customers = Customer.query.order_by(Customer.name).all()
    appointments = Appointment.query.filter_by(status='scheduled').limit(20).all()
    barbers = Barber.query.all()
    return render_template('payments/new.html', customers=customers, appointments=appointments, barbers=barbers)

@payments_bp.route('/payments/<int:id>/receipt')
@login_required
def receipt(id):
    payment = Payment.query.get_or_404(id)
    return render_template('payments/receipt.html', payment=payment)

@payments_bp.route('/api/validate-promo')
@login_required
def validate_promo():
    code = request.args.get('code', '').upper()
    promo = PromoCode.query.filter_by(code=code, is_active=True).first()
    if promo and promo.used_count < promo.max_uses:
        return jsonify({'valid': True, 'type': promo.discount_type, 'value': promo.discount_value})
    return jsonify({'valid': False})

@payments_bp.route('/promos', methods=['GET', 'POST'])
@login_required
@admin_required
def promos():
    if request.method == 'POST':
        p = PromoCode(
            code=request.form['code'].upper(),
            discount_type=request.form['discount_type'],
            discount_value=float(request.form['discount_value']),
            max_uses=int(request.form.get('max_uses', 100)),
            valid_until=datetime.strptime(request.form['valid_until'], '%Y-%m-%d') if request.form.get('valid_until') else None
        )
        db.session.add(p)
        db.session.commit()
        flash('Promo code created!', 'success')
    promos = PromoCode.query.order_by(PromoCode.id.desc()).all()
    return render_template('payments/promos.html', promos=promos)
