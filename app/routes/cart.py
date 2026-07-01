from flask import Blueprint, jsonify, request, session
from app.models import db, CartItem, MenuItem
import uuid

cart_bp = Blueprint('cart', __name__)

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@cart_bp.route('/api/cart', methods=['GET'])
def get_cart():
    session_id = get_session_id()
    items = CartItem.query.filter_by(session_id=session_id).all()
    total = sum(item.menu_item.price * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })

@cart_bp.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    session_id = get_session_id()
    data = request.get_json()
    menu_item_id = data.get('menu_item_id')
    qty = data.get('qty', 1)

    if not menu_item_id:
        return jsonify({"error": "menu_item_id required"}), 400

    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404

    cart_item = CartItem.query.filter_by(
        session_id=session_id,
        menu_item_id=menu_item_id
    ).first()

    if cart_item:
        cart_item.qty = qty
        if cart_item.qty <= 0:
            db.session.delete(cart_item)
    else:
        if qty > 0:
            cart_item = CartItem(
                session_id=session_id,
                menu_item_id=menu_item_id,
                qty=qty
            )
            db.session.add(cart_item)

    db.session.commit()

    items = CartItem.query.filter_by(session_id=session_id).all()
    total = sum(item.menu_item.price * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })

@cart_bp.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    session_id = get_session_id()
    data = request.get_json()
    menu_item_id = data.get('menu_item_id')

    cart_item = CartItem.query.filter_by(
        session_id=session_id,
        menu_item_id=menu_item_id
    ).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    items = CartItem.query.filter_by(session_id=session_id).all()
    total = sum(item.menu_item.price * item.qty for item in items)
    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": float(total)
    })

@cart_bp.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    session_id = get_session_id()
    CartItem.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return jsonify({"success": True})