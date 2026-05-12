from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.decorators import admin_required
from models import Product, Supplier
from extensions import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    products = Product.query.order_by(Product.category, Product.name).all()
    low_stock = [p for p in products if p.quantity <= p.reorder_level]
    return render_template('inventory/index.html', products=products, low_stock=low_stock)

@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        p = Product(
            name=request.form['name'], sku=request.form.get('sku'),
            category=request.form.get('category'),
            quantity=int(request.form.get('quantity', 0)),
            reorder_level=int(request.form.get('reorder_level', 5)),
            unit_price=float(request.form.get('unit_price', 0)),
            selling_price=float(request.form.get('selling_price', 0)),
            supplier_id=request.form.get('supplier_id') or None
        )
        db.session.add(p)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('inventory.index'))
    suppliers = Supplier.query.all()
    return render_template('inventory/form.html', product=None, suppliers=suppliers)

@inventory_bp.route('/inventory/<int:id>/restock', methods=['POST'])
@login_required
def restock(id):
    product = Product.query.get_or_404(id)
    qty = int(request.form.get('quantity', 0))
    product.quantity += qty
    product.last_restocked = datetime.utcnow()
    db.session.commit()
    flash(f'Restocked {qty} units of {product.name}', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('inventory/suppliers.html', suppliers=suppliers)

@inventory_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    if request.method == 'POST':
        s = Supplier(
            name=request.form['name'], contact_name=request.form.get('contact_name'),
            phone=request.form.get('phone'), email=request.form.get('email'),
            address=request.form.get('address')
        )
        db.session.add(s)
        db.session.commit()
        flash('Supplier added!', 'success')
        return redirect(url_for('inventory.suppliers'))
    return render_template('inventory/supplier_form.html')
