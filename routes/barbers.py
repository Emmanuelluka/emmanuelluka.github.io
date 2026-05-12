from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models import Barber, User, BarberSchedule, Appointment, Payment
from extensions import db
from werkzeug.security import generate_password_hash
from datetime import date
from sqlalchemy import func

barbers_bp = Blueprint('barbers', __name__)

@barbers_bp.route('/barbers')
@login_required
def index():
    barbers = Barber.query.all()
    receptionists = User.query.filter_by(role='receptionist').all()
    return render_template('barbers/index.html', barbers=barbers, receptionists=receptionists)

@barbers_bp.route('/barbers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('barbers.add'))
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already in use.', 'error')
            return redirect(url_for('barbers.add'))
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            full_name=request.form['full_name'],
            phone=request.form.get('phone'),
            role='barber',
            password_hash=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.flush()
        barber = Barber(
            user_id=user.id,
            specialization=request.form.get('specialization'),
            commission_rate=float(request.form.get('commission_rate', 40)),
            years_experience=int(request.form.get('years_experience', 0)),
            bio=request.form.get('bio')
        )
        db.session.add(barber)
        db.session.commit()
        flash(f'Barber {user.full_name} added successfully!', 'success')
        return redirect(url_for('barbers.index'))
    return render_template('barbers/form.html', role='barber')

@barbers_bp.route('/barbers/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    barber = Barber.query.get_or_404(id)
    user = User.query.get(barber.user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('barbers.index'))
    # Keep appointment records but unlink barber
    Appointment.query.filter_by(barber_id=barber.id).update({'barber_id': None})
    BarberSchedule.query.filter_by(barber_id=barber.id).delete()
    name = user.full_name
    db.session.delete(barber)
    db.session.delete(user)
    db.session.commit()
    flash(f'Barber {name} has been removed.', 'success')
    return redirect(url_for('barbers.index'))

@barbers_bp.route('/barbers/<int:id>')
@login_required
def detail(id):
    barber = Barber.query.get_or_404(id)
    today = date.today()
    month_start = today.replace(day=1)
    month_revenue = db.session.query(func.sum(Payment.amount)).join(Appointment).filter(
        Appointment.barber_id == id, Payment.created_at >= month_start,
        Payment.status == 'completed').scalar() or 0
    recent_appts = Appointment.query.filter_by(barber_id=id).order_by(
        Appointment.appointment_date.desc()).limit(10).all()
    schedules = BarberSchedule.query.filter_by(barber_id=id).all()
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    return render_template('barbers/detail.html', barber=barber, month_revenue=month_revenue,
                           recent_appts=recent_appts, schedules=schedules, days=days)

@barbers_bp.route('/barbers/<int:id>/schedule', methods=['POST'])
@login_required
def save_schedule(id):
    BarberSchedule.query.filter_by(barber_id=id).delete()
    for day in range(7):
        if request.form.get(f'day_{day}'):
            sched = BarberSchedule(
                barber_id=id, day_of_week=day,
                start_time=request.form.get(f'start_{day}', '08:00'),
                end_time=request.form.get(f'end_{day}', '18:00'),
                is_working=True
            )
            db.session.add(sched)
    db.session.commit()
    flash('Schedule updated!', 'success')
    return redirect(url_for('barbers.detail', id=id))

@barbers_bp.route('/barbers/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_availability(id):
    barber = Barber.query.get_or_404(id)
    barber.is_available = not barber.is_available
    db.session.commit()
    return redirect(url_for('barbers.index'))

# ── Receptionist Management ──────────────────────────────────────────────────

@barbers_bp.route('/receptionists/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_receptionist():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('barbers.add_receptionist'))
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already in use.', 'error')
            return redirect(url_for('barbers.add_receptionist'))
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            full_name=request.form['full_name'],
            phone=request.form.get('phone'),
            role='receptionist',
            password_hash=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Receptionist {user.full_name} added successfully!', 'success')
        return redirect(url_for('barbers.index'))
    return render_template('barbers/form.html', role='receptionist')

@barbers_bp.route('/receptionists/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_receptionist(id):
    user = User.query.filter_by(id=id, role='receptionist').first_or_404()
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('barbers.index'))
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    flash(f'Receptionist {name} has been removed.', 'success')
    return redirect(url_for('barbers.index'))
