from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import MenuItem

menu_bp = Blueprint('menu', __name__)


@menu_bp.route('/order')
@login_required
def order():
    return render_template('order.html')


@menu_bp.route('/api/menu')
@login_required
def get_menu():
    category = request.args.get('category')
    food_type = request.args.get('type')
    flavour = request.args.get('flavour')

    query = MenuItem.query

    # Customers should only ever see items an admin has marked
    # available -- admins bypass this so they can still see
    # unavailable items if this endpoint is ever reused for admin
    # views. Without this check, toggling an item to "unavailable"
    # in admin.py had no actual effect on what /api/menu returned.
    if not current_user.is_admin:
        query = query.filter_by(is_available=True)

    if category:
        query = query.filter_by(category=category)
    if food_type:
        query = query.filter_by(type=food_type)
    if flavour:
        query = query.filter_by(flavour=flavour)

    items = query.all()
    return jsonify([item.to_dict() for item in items])