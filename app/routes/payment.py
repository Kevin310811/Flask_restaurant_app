from decimal import Decimal, ROUND_HALF_UP
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, CartItem, Order, OrderItem, Reservation
import razorpay

payment_bp = Blueprint('payment', __name__)

# Tips are capped so a stray microwave entry ("1000000000") can't be sent
# to the payment gateway. Anything larger than this is almost certainly
# an input error, not generosity.
MAX_TIP = Decimal('1000.00')
PAISA = Decimal('0.01')


def get_razorpay_client():
    return razorpay.Client(auth=(
        current_app.config['RAZORPAY_KEY_ID'],
        current_app.config['RAZORPAY_KEY_SECRET']
    ))


def _parse_decimal(value, field):
    try:
        return Decimal(str(value)), None
    except (TypeError, ValueError, ArithmeticError):
        return None, f"{field} must be a valid number"


def _validate_tip(data):
    """Shared tip parsing/validation for both payment endpoints.

    Returns a Decimal quantized to 2 places, capped by MAX_TIP, never
    negative. Everything downstream (charge, DB row) uses this exact
    value so the amount charged can never disagree with the amount stored.
    """
    tip, error = _parse_decimal(data.get('tip', 0), 'tip')
    if error:
        return None, error
    if tip < 0:
        return None, "tip cannot be negative"
    if tip > MAX_TIP:
        return None, f"tip cannot exceed {MAX_TIP:.2f}"
    return tip.quantize(PAISA, ROUND_HALF_UP), None


def _cart_totals(cart_items):
    """Server-side subtotal from the DB cart. Never trust the client."""
    subtotal = sum((item.menu_item.discounted_price() * item.qty for item in cart_items), Decimal('0.00'))
    return subtotal


@payment_bp.route('/payment')
@login_required
def payment():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return redirect(url_for('menu.order'))

    subtotal = _cart_totals(items)
    # Pre-fill the checkout contact from the latest reservation phone (if
    # any) so returning customers aren't asked to re-enter it.
    latest_reservation = Reservation.query.filter_by(
        user_id=current_user.id
    ).order_by(Reservation.created_at.desc()).first()
    contact = latest_reservation.phone if latest_reservation else ''

    return render_template('payment.html',
        items=[item.to_dict() for item in items],
        subtotal=float(subtotal),
        user=current_user,
        contact=contact
    )


@payment_bp.route('/api/payment/create-order', methods=['POST'])
@login_required
def create_order():
    """Step 1 of checkout: fix the charge amount server-side AND persist
    the order.

    The amount Razorpay will actually charge is computed here, from
    the user's real cart in the database -- never from anything the
    client sends. A pending Order (with line-item snapshots and the
    Razorpay order id) is committed in the same breath, so the charge
    is always tied to a concrete DB order and the tip can't drift
    between step 1 and step 2.
    """
    data = request.get_json(silent=True) or {}
    tip, error = _validate_tip(data)
    if error:
        return jsonify({"error": error}), 400

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    subtotal = _cart_totals(cart_items)
    total = (subtotal + tip).quantize(PAISA, ROUND_HALF_UP)
    amount_paise = int((total * 100).to_integral_value(rounding=ROUND_HALF_UP))

    try:
        client = get_razorpay_client()
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as exc:
        current_app.logger.error("Razorpay order create failed: %s", exc)
        return jsonify({"error": "Payment gateway is unavailable. Please try again."}), 502

    # Supersede: any older pending order from this user is now obsolete
    # -- this new charge is what they are actually paying for. They are
    # voided rather than deleted so an abandoned-order payment that
    # Razorpay later confirms as captured can still be reconciled (see
    # verify_payment's heal path). Orders already paid/cancelled are
    # untouched.
    Order.query.filter(
        Order.user_id == current_user.id,
        Order.status == 'pending'
    ).update({'status': 'void'}, synchronize_session=False)

    order = Order(
        user_id=current_user.id,
        subtotal=subtotal,
        tip=tip,
        total=total,
        amount_paise=amount_paise,
        status='pending',
        razorpay_order_id=razorpay_order["id"]
    )
    # Snapshot line items NOW -- a copy of the cart frozen at the moment
    # the order was created, so later cart edits can't rewrite history.
    for item in cart_items:
        order.items.append(OrderItem(
            menu_item_id=item.menu_item_id,
            title=item.menu_item.title,
            price=item.menu_item.discounted_price(),
            qty=item.qty
        ))
    db.session.add(order)
    db.session.commit()

    return jsonify({
        "order_id": razorpay_order["id"],
        "db_order_id": order.id,
        "amount": amount_paise,
        "key_id": current_app.config['RAZORPAY_KEY_ID'],
        "tip": float(tip)
    })


@payment_bp.route('/api/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    """Step 2 of checkout: only mark an order 'paid' after Razorpay
    confirms the payment actually happened, for the right amount, on
    the right order.

    1. Find the pending order created in step 1 by its razorpay_order_id,
       scoped to the logged-in user.
    2. verify_payment_signature() proves the three values were genuinely
       produced by Razorpay for a real payment.
    3. The payment is fetched from Razorpay's API and checked for
       order match, captured status, and the exact paise amount fixed
       in step 1.
    4. Replay protection: the unique razorpay_order_id means a second
       verify for the same payment finds the already-paid order and
       just returns success -- it can never mint a second paid order.
    5. Supersede-scenario: each new Pay Now click voids the user's
       older pendings, but a payment on a voided order is still real
       money. Verify therefore accepts 'void' orders too -- Razorpay's
       own confirmation (captured, matching amount) can heal them back
       to 'paid'. Nothing is trusted from the client; only Razorpay.
    """
    data = request.get_json(silent=True) or {}
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"error": "Missing payment verification fields"}), 400

    order = Order.query.filter_by(
        razorpay_order_id=razorpay_order_id,
        user_id=current_user.id
    ).first()

    if not order:
        # No pending order was created for this payment (or it belongs to
        # a different user). The charge never existed in the DB, so it is
        # not real for this user -- reject.
        return jsonify({"error": "No pending order found for this payment."}), 404

    if order.status == 'paid':
        # Idempotent: the checkout page can re-call verify (double click,
        # refresh) without consequence.
        return jsonify({"success": True, "order_id": order.id})

    # 'void' orders are allowed through: a payment on a superseded
    # pending order is still money that arrived, and Razorpay's own
    # checks below will heal it back to paid if it was really captured.
    if order.status not in ('pending', 'void'):
        return jsonify({"error": "This order can no longer be paid."}), 409

    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Payment verification failed"}), 400

    # Signature proves the payment came from Razorpay; the fetch proves
    # it's the payment for THIS pending order, actually captured, for the
    # exact amount fixed in step 1.
    try:
        payment = client.payment.fetch(razorpay_payment_id)
    except Exception as exc:
        current_app.logger.error("Razorpay payment fetch failed: %s", exc)
        return jsonify({"error": "Could not confirm payment status. Please try again."}), 502

    if payment.get("order_id") != razorpay_order_id:
        return jsonify({"error": "Payment does not match this order."}), 400
    if payment.get("status") != "captured":
        return jsonify({"error": "Payment is not complete."}), 400
    if payment.get("amount") != order.amount_paise:
        current_app.logger.error(
            "Amount mismatch on order %s: charged %s, DB says %s",
            order.id, payment.get("amount"), order.amount_paise
        )
        return jsonify({"error": "Charged amount does not match the order total."}), 400

    order.status = 'paid'
    order.razorpay_payment_id = razorpay_payment_id

    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    return jsonify({"success": True, "order_id": order.id})
