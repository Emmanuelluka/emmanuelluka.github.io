from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Appointment, Customer, Payment, Barber, WalkInQueue, Product
from extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    # Today's appointments
    today_appointments = Appointment.query.filter_by(appointment_date=today).count()
    today_completed = Appointment.query.filter_by(appointment_date=today, status='completed').count()
    # Revenue today
    today_revenue = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.created_at) == today, Payment.status == 'completed').scalar() or 0
    # Monthly revenue
    month_start = today.replace(day=1)
    month_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.created_at >= month_start, Payment.status == 'completed').scalar() or 0
    # Total customers
    total_customers = Customer.query.count()
    # Active barbers
    active_barbers = Barber.query.filter_by(is_available=True).count()
    # Low stock
    low_stock = Product.query.filter(Product.quantity <= Product.reorder_level).count()
    # Queue count
    queue_count = WalkInQueue.query.filter_by(status='waiting').count()
    # Recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(8).all()
    # Weekly revenue chart
    week_data = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        rev = db.session.query(func.sum(Payment.amount)).filter(
            func.date(Payment.created_at) == day, Payment.status == 'completed').scalar() or 0
        week_data.append({'day': day.strftime('%a'), 'revenue': float(rev)})
    # Top barbers
    barbers = Barber.query.order_by(Barber.total_revenue.desc()).limit(5).all()

    return render_template('dashboard/index.html',
        today_appointments=today_appointments,
        today_completed=today_completed,
        today_revenue=today_revenue,
        month_revenue=month_revenue,
        total_customers=total_customers,
        active_barbers=active_barbers,
        low_stock=low_stock,
        queue_count=queue_count,
        recent_appointments=recent_appointments,
        week_data=week_data,
        barbers=barbers,
        today=today
    )

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    today = date.today()
    revenue = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.created_at) == today, Payment.status == 'completed').scalar() or 0
    return jsonify({'today_revenue': float(revenue),
                    'queue': WalkInQueue.query.filter_by(status='waiting').count()})
