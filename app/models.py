from decimal import Decimal, ROUND_HALF_UP
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

def utcnow():
    """Naive UTC now (db.DateTime stores naive values; utcnow is deprecated in 3.12+)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    created_at = db.Column(db.DateTime, default=utcnow)

    cart_items = db.relationship('CartItem', backref='user', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat()
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))
    flavour = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False, server_default='true')
    discount_percent = db.Column(db.Numeric(5, 2), default=0, nullable=False, server_default='0')

    def discounted_price(self):
        """Effective price as Decimal, rounded to 2 places (half-up)."""
        price = Decimal(self.price)
        discount = Decimal(self.discount_percent or 0)
        if discount > 0:
            return (price * (1 - discount / 100)).quantize(Decimal('0.01'), ROUND_HALF_UP)
        return price

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "desc": self.desc,
            "type": self.type,
            "flavour": self.flavour,
            "category": self.category,
            "price": float(self.price),
            "discounted_price": float(self.discounted_price()),
            "discount_percent": float(self.discount_percent),
            "image": self.image,
            "is_available": self.is_available
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False, index=True)
    qty = db.Column(db.Integer, nullable=False, default=1)

    menu_item = db.relationship('MenuItem')

    def to_dict(self):
        item = self.menu_item
        effective_price = item.discounted_price()
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "title": item.title,
            "price": float(effective_price),
            "original_price": float(item.price),
            "discount_percent": float(item.discount_percent),
            "qty": self.qty,
            "subtotal": float(effective_price * self.qty)
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tip = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    # Razorpay charges in paise; store the exact integer amount fixed at
    # create-order time so verify can compare it against what Razorpay
    # reports the payment to be, instead of re-deriving it and hoping
    # the cart/tip hasn't changed in between.
    amount_paise = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    # The Razorpay Orders API id for this order. Unique + non-null once
    # a payment is attempted, which makes one payment -> one order
    # guaranteed at the schema level.
    razorpay_order_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "subtotal": float(self.subtotal),
            "tip": float(self.tip),
            "total": float(self.total),
            "status": self.status,
            "razorpay_order_id": self.razorpay_order_id,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    # menu_item_id is nullable: deleting a menu item from the admin panel
    # must not break past orders. OrderItem snapshots title/price/qty at
    # purchase time, so history stays intact when the FK is set NULL.
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id', ondelete='SET NULL'), nullable=True, index=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "title": self.title,
            "price": float(self.price),
            "qty": self.qty,
            "subtotal": float(self.price) * self.qty
        }


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    people = db.Column(db.Integer, nullable=False)
    slot_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='confirmed')
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "email": self.email,
            "people": self.people,
            "slot_time": self.slot_time.strftime('%d %b %Y, %I:%M %p'),
            "status": self.status
        }


class Expense(db.Model):
    """Operating expense recorded by an admin for the analytics page.

    The site never had an expense model; this is the minimal table the
    analytics Expense Overview needs. spent_on is a plain date (not a
    timestamp): expenses are booked for a whole calendar day, which is
    also what makes day/week/month bucketing exact and timezone-safe.
    created_by is SET NULL so removing an admin does not delete their
    recorded expenses.
    """
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    spent_on = db.Column(db.Date, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "amount": float(self.amount),
            "spent_on": self.spent_on.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }