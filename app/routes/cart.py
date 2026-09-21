from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, CartItem, MenuItem

cart_bp = Blueprint('cart', __name__)

MAX_QTY_PER_ITEM = 20


def cart_summary(user_id):
    """Single place that computes a user's cart items + total."""
    items = CartItem.query.filter_by(user_id=user_id).all()
    total = sum(item.menu_item.price * item.qty for item in items)
    return items, float(total)


@cart_bp.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    items, total = cart_summary(current_user.id)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": total
    })


@cart_bp.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    menu_item_id = data.get('menu_item_id')
    qty = data.get('qty', 1)

    if not menu_item_id:
        return jsonify({"error": "menu_item_id required"}), 400

    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return jsonify({"error": "qty must be a whole number"}), 400

    if qty > MAX_QTY_PER_ITEM:
        return jsonify({"error": f"qty cannot exceed {MAX_QTY_PER_ITEM} per item"}), 400

    menu_item = MenuItem.query.get(menu_item_id)
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
        "total": total
    })


@cart_bp.route('/api/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
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
        "total": total
    })