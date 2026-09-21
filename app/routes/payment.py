from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, CartItem, Order, OrderItem
import razorpay

payment_bp = Blueprint('payment', __name__)


def get_razorpay_client():
    return razorpay.Client(auth=(
        current_app.config['RAZORPAY_KEY_ID'],
        current_app.config['RAZORPAY_KEY_SECRET']
    ))


def _validate_tip(data):
    """Shared tip parsing/validation for both payment endpoints."""
    try:
        tip = float(data.get('tip', 0))
    except (TypeError, ValueError):
        return None, "tip must be a valid number"
    if tip < 0:
        return None, "tip cannot be negative"
    return tip, None


@payment_bp.route('/payment')
@login_required
def payment():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return redirect(url_for('menu.order'))

    subtotal = sum(item.menu_item.discounted_price() * item.qty for item in items)
    return render_template('payment.html',
        items=[item.to_dict() for item in items],
        subtotal=float(subtotal)
    )


@payment_bp.route('/api/payment/create-order', methods=['POST'])
@login_required
def create_order():
    """Step 1 of checkout: fix the charge amount server-side.

    The amount Razorpay will actually charge is computed here, from
    the user's real cart in the database -- never from anything the
    client sends. This is what the old single-step checkout() got
    wrong: it never involved Razorpay's Orders API at all, so nothing
    tied the amount shown in the widget to a value the server had
    actually verified.
    """
    data = request.get_json() or {}
    tip, error = _validate_tip(data)
    if error:
        return jsonify({"error": error}), 400

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    subtotal = float(sum(item.menu_item.discounted_price() * item.qty for item in cart_items))
    total = subtotal + tip
    amount_paise = round(total * 100)

    client = get_razorpay_client()
    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "key_id": current_app.config['RAZORPAY_KEY_ID'],
        "tip": tip
    })


@payment_bp.route('/api/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    """Step 2 of checkout: only mark an order 'paid' after Razorpay
    confirms the payment actually happened.

    This replaces the old checkout() route entirely. The old version
    created a 'paid' Order the moment the Pay Now button was clicked,
    before the Razorpay modal even opened -- meaning closing the
    modal without paying still left a paid order in the database.
    Nothing here is trusted until verify_payment_signature() confirms
    these three values were genuinely produced by Razorpay for a real
    completed payment.
    """
    data = request.get_json() or {}
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"error": "Missing payment verification fields"}), 400

    tip, error = _validate_tip(data)
    if error:
        return jsonify({"error": error}), 400

    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Payment verification failed"}), 400

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    subtotal = float(sum(item.menu_item.discounted_price() * item.qty for item in cart_items))
    total = subtotal + tip

    order = Order(
        user_id=current_user.id,
        subtotal=subtotal,
        tip=tip,
        total=total,
        status='paid',
        razorpay_payment_id=razorpay_payment_id
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            title=item.menu_item.title,
            price=item.menu_item.discounted_price(),
            qty=item.qty
        )
        db.session.add(order_item)

    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    return jsonify({"success": True, "order_id": order.id})