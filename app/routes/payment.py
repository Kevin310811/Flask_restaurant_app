from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from app.models import db, CartItem, Order, OrderItem

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/payment')
def payment():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('menu.order'))

    items = CartItem.query.filter_by(session_id=session_id).all()
    if not items:
        return redirect(url_for('menu.order'))

    subtotal = sum(item.menu_item.price * item.qty for item in items)
    return render_template('payment.html',
        items=[item.to_dict() for item in items],
        subtotal=float(subtotal)
    )

@payment_bp.route('/api/checkout', methods=['POST'])
def checkout():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({"error": "No session"}), 400

    data = request.get_json()
    tip = float(data.get('tip', 0))

    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    subtotal = float(sum(item.menu_item.price * item.qty for item in cart_items))
    total = subtotal + tip

    order = Order(
        session_id=session_id,
        subtotal=subtotal,
        tip=tip,
        total=total,
        status='paid'  # placeholder until proper Razorpay webhook verification
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            title=item.menu_item.title,
            price=float(item.menu_item.price),
            qty=item.qty
        )
        db.session.add(order_item)

    CartItem.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    return jsonify({"success": True, "order_id": order.id})