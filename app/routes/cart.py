from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, CartItem, MenuItem

cart_bp = Blueprint('cart', __name__)

MAX_QTY_PER_ITEM = 20


def cart_summary(user_id):
    """Single place that computes a user's cart items + total.

    get_cart(), add_to_cart(), and remove_from_cart() all used to run
    this same query-and-sum independently. Now they all call this, so
    the calculation can't drift out of sync between them.
    """
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

    # The frontend caps qty at MAX_QTY_PER_ITEM client-side, but that's
    # only a UI nicety -- nothing stops someone from POSTing directly
    # to this endpoint with an arbitrary or malformed value, so the
    # real check has to live here.
    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return jsonify({"error": "qty must be a whole number"}), 400

    if qty > MAX_QTY_PER_ITEM:
        return jsonify({"error": f"qty cannot exceed {MAX_QTY_PER_ITEM} per item"}), 400

    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404

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