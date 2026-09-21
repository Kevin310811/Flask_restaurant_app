from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
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

    # Return every item, available or not -- is_available is already
    # exposed in to_dict(), so the frontend can show unavailable items
    # as "sold out" rather than hiding them entirely. Actually
    # preventing an unavailable item from being ordered happens
    # server-side in cart.py's add_to_cart(), not here -- filtering
    # visibility was never what made ordering safe, so removing the
    # filter here doesn't reopen that gap.
    if category:
        query = query.filter_by(category=category)
    if food_type:
        query = query.filter_by(type=food_type)
    if flavour:
        query = query.filter_by(flavour=flavour)

    items = query.all()
    return jsonify([item.to_dict() for item in items])