import re
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import bcrypt, limiter
from app.models import db, User, Order, Reservation

auth_bp = Blueprint('auth', __name__)

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# A throwaway hash so a login attempt for a non-existent email still runs
# one full bcrypt check -- otherwise the fast "user not found" path is
# measurably quicker than the slow "wrong password" path, which is a
# cheap way for an attacker to find out who has an account.
# Generated lazily (cached per process) because Flask-Bcrypt needs an
# active app context to read BCRYPT_LOG_ROUNDS.
_dummy_hash = None


def _get_dummy_hash():
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = bcrypt.generate_password_hash('timing-equalizer').decode('utf-8')
    return _dummy_hash


def is_safe_redirect_url(target):
    """Only allow redirecting to a path on this same site.

    Without this, a login link like /login?next=https://evil.com sends
    a successfully-authenticated user straight to an attacker's site --
    a classic open redirect, often used in phishing (the link looks
    like it points at your real domain, so it's more likely to be
    clicked, then silently forwards the victim elsewhere right after
    they've just typed in their password).
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([first_name, last_name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if not EMAIL_PATTERN.match(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('main.index'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        # Always run one bcrypt check, even when the email is unknown, so
        # response timing doesn't reveal whether an account exists.
        if user:
            password_ok = bcrypt.check_password_hash(user.password_hash, password)
        else:
            bcrypt.check_password_hash(_get_dummy_hash(), password)
            password_ok = False

        if not password_ok:
            flash('Invalid email or password.', 'error')
            return render_template('login.html', email=email)

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not is_safe_redirect_url(next_page):
            next_page = None
        return redirect(next_page or url_for('main.index'))

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # POST-only so a cross-site <img src="/logout"> or <a> can't silently
    # log a user out (GET requests can't be CSRF-protected).
    logout_user()
    return redirect(url_for('main.index'))


def _ordinal(n):
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', 21 -> '21st'..."""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_name':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()

            if not first_name or not last_name:
                flash('Name fields cannot be empty.', 'error')
            else:
                current_user.first_name = first_name
                current_user.last_name = last_name
                db.session.commit()
                flash('Name updated successfully.', 'success')

        elif action == 'delete_account':
            user_id = current_user.id
            logout_user()
            user = db.session.get(User, user_id)
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('main.index'))

    orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.created_at.desc()).all()

    # Display counters for the order-history cards. Both count
    # chronologically (oldest first) and are computed fresh -- the
    # raw id column is NOT used, because database ids accumulate
    # gaps from other users' orders and deletions.
    #   my_n / my_total  -> this user's n-th order of their M orders
    #   global_label     -> the k-th order ever placed here, of T total
    all_rows = (
        db.session.query(Order.id, Order.created_at)
        .order_by(Order.created_at.asc(), Order.id.asc())
        .all()
    )
    all_rank = {order_id: i + 1 for i, (order_id, _created) in enumerate(all_rows)}
    all_total = len(all_rows)

    mine_sorted = sorted(orders, key=lambda o: (o.created_at, o.id))
    my_rank = {o.id: i + 1 for i, o in enumerate(mine_sorted)}
    my_total = len(mine_sorted)

    for o in orders:
        my_n = my_rank[o.id]
        global_n = all_rank[o.id]
        o.my_n = my_n
        o.my_total = my_total
        o.my_title = (
            f"Your {_ordinal(my_n)} placed order (this account)"
            if my_total else "No orders yet"
        )
        o.global_label = f"{_ordinal(global_n)} of {all_total}"
        o.global_title = (
            f"The {_ordinal(global_n)} order placed in total "
            f"(of {all_total} in the database)"
        )

    return render_template('profile.html', orders=orders)