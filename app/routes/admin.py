from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Order, OrderItem, Reservation, MenuItem, CartItem
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter_by(status='paid').scalar() or 0
    total_reservations = Reservation.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        total_reservations=total_reservations,
        recent_orders=recent_orders
    )


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status_filter = request.args.get('status', '')
    query = Order.query.order_by(Order.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_orders = query.all()
    return render_template('admin/orders.html', orders=all_orders, status_filter=status_filter)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['paid', 'pending', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order_id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} deleted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/reservations')
@login_required
@admin_required
def reservations():
    status_filter = request.args.get('status', '')
    query = Reservation.query.order_by(Reservation.slot_time.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_reservations = query.all()
    return render_template('admin/reservations.html',
        reservations=all_reservations,
        status_filter=status_filter
    )


@admin_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'cancelled'
    db.session.commit()
    flash(f'Reservation #{reservation_id} cancelled.', 'success')
    return redirect(url_for('admin.reservations'))


@admin_bp.route('/menu')
@login_required
@admin_required
def menu():
    all_items = MenuItem.query.order_by(MenuItem.category, MenuItem.title).all()
    return render_template('admin/menu.html', items=all_items)


@admin_bp.route('/menu/add', methods=['POST'])
@login_required
@admin_required
def add_menu_item():
    title = request.form.get('title', '').strip()
    desc = request.form.get('desc', '').strip()
    category = request.form.get('category', '').strip()
    food_type = request.form.get('type', '').strip() or None
    flavour = request.form.get('flavour', '').strip()
    price = request.form.get('price', '0')
    image = request.form.get('image', '').strip()
    discount_percent = float(request.form.get('discount_percent', 0) or 0)

    if not all([title, desc, category, flavour, price, image]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.menu'))

    item = MenuItem(
        title=title,
        desc=desc,
        category=category,
        type=food_type,
        flavour=flavour,
        price=float(price),
        image=image,
        is_available=True,
        discount_percent=discount_percent
    )
    db.session.add(item)
    db.session.commit()
    flash(f'"{title}" added to menu.', 'success')
    return redirect(url_for('admin.menu'))


@admin_bp.route('/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.title = request.form.get('title', item.title).strip()
    item.desc = request.form.get('desc', item.desc).strip()
    item.category = request.form.get('category', item.category).strip()
    item.type = request.form.get('type', '').strip() or None
    item.flavour = request.form.get('flavour', item.flavour).strip()
    item.price = float(request.form.get('price', item.price))
    item.image = request.form.get('image', item.image).strip()
    item.discount_percent = float(request.form.get('discount_percent', 0) or 0)
    db.session.commit()
    flash(f'"{item.title}" updated.', 'success')
    return redirect(url_for('admin.menu'))


@admin_bp.route('/menu/<int:item_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    status = 'available' if item.is_available else 'unavailable'
    flash(f'"{item.title}" marked as {status}.', 'success')
    return redirect(url_for('admin.menu'))


@admin_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    title = item.title
    db.session.delete(item)
    db.session.commit()
    flash(f'"{title}" deleted from menu.', 'success')
    return redirect(url_for('admin.menu'))