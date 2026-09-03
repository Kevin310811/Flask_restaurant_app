from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, CartItem, MenuItem

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.menu_item.discounted_price() * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })


@cart_bp.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    menu_item_id = data.get('menu_item_id')
    qty = data.get('qty', 1)

    if not menu_item_id:
        return jsonify({"error": "menu_item_id required"}), 400

    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404

    if not menu_item.is_available:
        return jsonify({"error": "Item is not available"}), 400

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

    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.menu_item.discounted_price() * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
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

    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.menu_item.discounted_price() * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })


@cart_bp.route('/api/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})