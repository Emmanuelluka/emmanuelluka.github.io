from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import WalkInQueue, Service, Barber
from extensions import db
from datetime import datetime

queue_bp = Blueprint('queue', __name__)

@queue_bp.route('/queue')
@login_required
def index():
    queue = WalkInQueue.query.filter_by(status='waiting').order_by(WalkInQueue.joined_at).all()
    in_service = WalkInQueue.query.filter_by(status='in-service').all()
    services = Service.query.filter_by(is_active=True).all()
    barbers = Barber.query.filter_by(is_available=True).all()
    return render_template('queue/index.html', queue=queue, in_service=in_service,
                           services=services, barbers=barbers)

@queue_bp.route('/queue/join', methods=['POST'])
@login_required
def join():
    last = WalkInQueue.query.filter(
        WalkInQueue.joined_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    entry = WalkInQueue(
        customer_name=request.form['customer_name'],
        phone=request.form.get('phone'),
        service_id=request.form.get('service_id') or None,
        barber_id=request.form.get('barber_id') or None,
        queue_number=last + 1
    )
    db.session.add(entry)
    db.session.commit()
    flash(f'{entry.customer_name} added to queue. Queue #{entry.queue_number}', 'success')
    return redirect(url_for('queue.index'))

@queue_bp.route('/queue/<int:id>/serve', methods=['POST'])
@login_required
def serve(id):
    entry = WalkInQueue.query.get_or_404(id)
    entry.status = 'in-service'
    db.session.commit()
    return redirect(url_for('queue.index'))

@queue_bp.route('/queue/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    entry = WalkInQueue.query.get_or_404(id)
    entry.status = 'completed'
    entry.served_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('queue.index'))

@queue_bp.route('/queue/<int:id>/remove', methods=['POST'])
@login_required
def remove(id):
    entry = WalkInQueue.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('queue.index'))

@queue_bp.route('/api/queue-count')
def queue_count():
    count = WalkInQueue.query.filter_by(status='waiting').count()
    return jsonify({'count': count})
