from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.models import db, CartItem, MenuItem

cart_bp = Blueprint('cart', __name__)

MAX_QTY_PER_ITEM = 20


def cart_summary(user_id):
    """Single place that computes a user's cart items + total."""
    # joinedload fetches every referenced menu item in the same round
    # trip; to_dict() and the total read menu_item on each row.
    items = (CartItem.query.options(joinedload(CartItem.menu_item))
             .filter_by(user_id=user_id).all())
    # Use the discounted price so the total always matches the per-item
    # subtotals and the payment page. (It previously used menu_item.price,
    # silently charging full price for discounted items.)
    total = sum((item.menu_item.discounted_price() * item.qty for item in items), Decimal('0.00'))
    return items, total


@cart_bp.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    items, total = cart_summary(current_user.id)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })


@cart_bp.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    # get_json(silent=True) returns None on a malformed/missing body instead
    # of crashing the request; treat it as an explicit client error.
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    menu_item_id = data.get('menu_item_id')
    qty = data.get('qty', 1)

    if not menu_item_id:
        return jsonify({"error": "menu_item_id required"}), 400

    # Reject anything that isn't a whole number (floats like 1.5, bools,
    # strings like "abc"). int(float) would silently truncate 1.9 to 1.
    try:
        qty = int(str(qty).strip())
    except (TypeError, ValueError):
        return jsonify({"error": "qty must be a whole number"}), 400

    if qty > MAX_QTY_PER_ITEM:
        return jsonify({"error": f"qty cannot exceed {MAX_QTY_PER_ITEM} per item"}), 400

    # db.session.get is the modern Session.get API (same identity-map
    # semantics and None-on-miss as the legacy Query.get it replaces).
    menu_item = db.session.get(MenuItem, menu_item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404

    # This is the real enforcement point for availability. menu.py now
    # shows unavailable items to customers (as "sold out") instead of
    # hiding them, so nothing there stops a request from targeting one
    # -- this check is what actually prevents it from being ordered,
    # regardless of what the frontend does or doesn't disable.
    if qty > 0 and not menu_item.is_available:
        return jsonify({"error": "This item is currently unavailable."}), 400

    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        menu_item_id=menu_item_id
    ).first()

    if cart_item:
        cart_item.qty = qty
        if cart_item.qty <= 0:
            db.session.delete(cart_item)
    else:
        if qty > 0:
            cart_item = CartItem(
                user_id=current_user.id,
                menu_item_id=menu_item_id,
                qty=qty
            )
            db.session.add(cart_item)

    db.session.commit()

    items, total = cart_summary(current_user.id)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })


@cart_bp.route('/api/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    menu_item_id = data.get('menu_item_id')

    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        menu_item_id=menu_item_id
    ).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    items, total = cart_summary(current_user.id)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })