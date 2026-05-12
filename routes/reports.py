from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.decorators import admin_required
from models import Payment, Appointment, Customer, Barber
from extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@admin_required
def index():
    today = date.today()
    period = request.args.get('period', 'week')
    if period == 'week':
        start = today - timedelta(days=6)
    elif period == 'month':
        start = today.replace(day=1)
    else:
        start = today.replace(month=1, day=1)

    # Revenue by day
    revenue_data = []
    delta = (today - start).days + 1
    for i in range(delta):
        day = start + timedelta(days=i)
        rev = db.session.query(func.sum(Payment.amount)).filter(
            func.date(Payment.created_at) == day, Payment.status == 'completed').scalar() or 0
        revenue_data.append({'date': day.strftime('%b %d'), 'revenue': float(rev)})

    # Payment methods breakdown
    methods = db.session.query(Payment.method, func.sum(Payment.amount)).filter(
        Payment.created_at >= start, Payment.status == 'completed').group_by(Payment.method).all()

    # Top services
    from models import Service
    top_services = db.session.query(Service.name, func.count(Appointment.id)).join(
        Appointment, Service.id == Appointment.service_id).filter(
        Appointment.appointment_date >= start).group_by(Service.name).order_by(
        func.count(Appointment.id).desc()).limit(5).all()

    # Barber performance
    barber_perf = Barber.query.order_by(Barber.total_revenue.desc()).all()

    # Customer retention
    total = Customer.query.count()
    returning = Customer.query.filter(Customer.total_visits > 1).count()
    new_this_period = Customer.query.filter(Customer.created_at >= start).count()

    total_revenue = sum(r['revenue'] for r in revenue_data)
    total_appts = Appointment.query.filter(Appointment.appointment_date >= start).count()

    return render_template('reports/index.html',
        period=period, revenue_data=revenue_data, methods=methods,
        top_services=top_services, barber_perf=barber_perf,
        total_revenue=total_revenue, total_appts=total_appts,
        total_customers=total, returning_customers=returning, new_customers=new_this_period)
