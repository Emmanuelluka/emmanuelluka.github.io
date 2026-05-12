from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Customer, Appointment, Payment
from extensions import db
from datetime import datetime

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers')
@login_required
def index():
    search = request.args.get('search', '')
    query = Customer.query
    if search:
        query = query.filter(Customer.name.ilike(f'%{search}%') | Customer.phone.ilike(f'%{search}%'))
    customers = query.order_by(Customer.created_at.desc()).all()
    return render_template('customers/index.html', customers=customers, search=search)

@customers_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        c = Customer(
            name=request.form['name'], phone=request.form.get('phone'),
            email=request.form.get('email'), preferences=request.form.get('preferences'))
        db.session.add(c)
        db.session.commit()
        flash('Customer added!', 'success')
        return redirect(url_for('customers.index'))
    return render_template('customers/form.html', customer=None)

@customers_bp.route('/customers/<int:id>')
@login_required
def detail(id):
    customer = Customer.query.get_or_404(id)
    appointments = Appointment.query.filter_by(customer_id=id).order_by(Appointment.appointment_date.desc()).limit(10).all()
    payments = Payment.query.filter_by(customer_id=id).order_by(Payment.created_at.desc()).limit(10).all()
    return render_template('customers/detail.html', customer=customer, appointments=appointments, payments=payments)

@customers_bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.preferences = request.form.get('preferences')
        db.session.commit()
        flash('Customer updated!', 'success')
        return redirect(url_for('customers.detail', id=id))
    return render_template('customers/form.html', customer=customer)
