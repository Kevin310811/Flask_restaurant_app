import re
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Reservation
from datetime import datetime, timedelta
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

SLOT_INTERVAL_MINUTES = 20
MAX_RESERVATIONS_PER_SLOT = 2
MAX_PEOPLE_PER_SLOT = 10
MAX_PARTY_SIZE = 12
OPENING_HOUR = 8
OPENING_MINUTE = 40
CLOSING_HOUR = 23

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_PATTERN = re.compile(r'^[+\d][\d\s\-\(\)]{5,19}$')


def snap_to_slot(dt):
    minutes = (dt.minute // SLOT_INTERVAL_MINUTES) * SLOT_INTERVAL_MINUTES
    return dt.replace(minute=minutes, second=0, microsecond=0)


def get_slot_status(slot_time):
    """Single source of truth for a slot's current booking state.

    Both is_slot_available() (used when someone submits a reservation)
    and get_slots() (used to render the picker UI) call this, so the
    two can never disagree about what "available" means.
    """
    existing = Reservation.query.filter_by(
        slot_time=slot_time,
        status='confirmed'
    ).all()

    reservations_count = len(existing)
    total_people = sum(r.people for r in existing)

    return {
        "reservations_count": reservations_count,
        "total_people": total_people,
        "spots_left": MAX_PEOPLE_PER_SLOT - total_people,
        "has_room_for_new_booking": reservations_count < MAX_RESERVATIONS_PER_SLOT,
    }


def slot_statuses_for_window(start, end):
    """Per-slot booking state for every confirmed reservation in [start, end).

    The slot picker renders one row per 20-minute slot; querying each
    slot separately made the PM grid cost one SELECT per slot. This
    fetches the whole window once and groups it in Python — the exact
    same rows get_slot_status() would have returned per slot, so the
    rendered availability is unchanged.
    """
    rows = Reservation.query.filter(
        Reservation.slot_time >= start,
        Reservation.slot_time < end,
        Reservation.status == 'confirmed',
    ).all()

    by_slot = {}
    for r in rows:
        by_slot.setdefault(r.slot_time, []).append(r)

    out = {}
    for slot_time, existing in by_slot.items():
        reservations_count = len(existing)
        total_people = sum(r.people for r in existing)
        out[slot_time] = {
            "reservations_count": reservations_count,
            "total_people": total_people,
            "spots_left": MAX_PEOPLE_PER_SLOT - total_people,
            "has_room_for_new_booking": reservations_count < MAX_RESERVATIONS_PER_SLOT,
        }
    return out


def is_slot_available(slot_time, people):
    status = get_slot_status(slot_time)

    if not status["has_room_for_new_booking"]:
        return False, "This time slot is fully booked. Please choose another time."

    if status["total_people"] + people > MAX_PEOPLE_PER_SLOT:
        return False, f"This time slot can only accommodate {status['spots_left']} more people."

    return True, None


def acquire_slot_lock(slot_time):
    """Serialize all reservation attempts for one exact slot_time.

    Without this, two requests booking the same slot at the same
    instant can both read "there's room" via get_slot_status() before
    either has committed, and both succeed -- overbooking the slot.

    A row lock (SELECT ... FOR UPDATE) on existing reservations doesn't
    fully close this: if this is the very first booking for a brand
    new slot_time, there are no existing rows to lock yet, so two
    "first" bookings for that slot could still race past each other.

    A Postgres advisory lock sidesteps that because it locks an
    arbitrary integer we choose, not rows that may not exist yet. We
    derive that integer from the slot's timestamp, so every request
    for the same slot_time contends for the same lock. It's scoped to
    the current transaction and is released automatically on commit
    or rollback -- no manual unlock needed.

    The advisory lock is Postgres-only. SQLite (the local dev fallback)
    serializes writes at the database level, so the same guard call is
    a no-op there -- dev-only risk accepted in exchange for not 500ing
    every reservation attempt without a Postgres server running.
    """
    if db.engine.dialect.name != 'postgresql':
        return
    slot_key = int(slot_time.timestamp())
    db.session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": slot_key})


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/gallery')
def gallery():
    return render_template('gallery.html')


@main_bp.route('/api/slots')
def get_slots():
    date_str = request.args.get('date')
    period = request.args.get('period', 'AM')

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date"}), 400

    if period == 'AM':
        start = selected_date.replace(hour=8, minute=40, second=0, microsecond=0)
        end = selected_date.replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        start = selected_date.replace(hour=12, minute=0, second=0, microsecond=0)
        end = selected_date.replace(hour=23, minute=0, second=0, microsecond=0)

    slots = []
    current = start
    statuses = slot_statuses_for_window(start, end)

    while current < end:
        status = statuses.get(current) or {
            "reservations_count": 0,
            "total_people": 0,
            "spots_left": MAX_PEOPLE_PER_SLOT,
            "has_room_for_new_booking": True,
        }

        available = status["has_room_for_new_booking"] and status["spots_left"] > 0

        slots.append({
            "time": current.strftime('%H:%M'),
            "display": current.strftime('%I:%M %p'),
            "available": available,
            "spots_left": status["spots_left"]
        })

        current += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    return jsonify(slots)


@main_bp.route('/reservations', methods=['GET', 'POST'])
@login_required
def reservations():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"success": False, "error": "Invalid or missing JSON body."}), 400

        try:
            raw_time = datetime.fromisoformat(data.get('time'))
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid date format."}), 400

        slot_time = snap_to_slot(raw_time)

        slot_minutes = slot_time.hour * 60 + slot_time.minute
        opening_minutes = OPENING_HOUR * 60 + OPENING_MINUTE
        closing_minutes = CLOSING_HOUR * 60

        if slot_minutes < opening_minutes or slot_minutes >= closing_minutes:
            return jsonify({"success": False, "error": "Reservations are only available between 8:40 AM and 11:00 PM."}), 400

        if slot_time < datetime.now():
            return jsonify({"success": False, "error": "Please select a future date and time."}), 400

        # int() used to run unguarded here: a body with people="abc"
        # crashed the request with a 500.
        try:
            people = int(str(data.get('people', 1)).strip())
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Party size must be a whole number."}), 400
        if people < 1 or people > MAX_PARTY_SIZE:
            return jsonify({"success": False, "error": f"Party size must be between 1 and {MAX_PARTY_SIZE}."}), 400

        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        email = (data.get('email') or '').strip().lower()

        if not first_name or not last_name:
            return jsonify({"success": False, "error": "First and last name are required."}), 400
        if len(first_name) > 50 or len(last_name) > 50:
            return jsonify({"success": False, "error": "Name is too long."}), 400
        if not PHONE_PATTERN.match(phone):
            return jsonify({"success": False, "error": "Please enter a valid phone number."}), 400
        if len(email) > 100 or not EMAIL_PATTERN.match(email):
            return jsonify({"success": False, "error": "Please enter a valid email address."}), 400

        # Everything above is cheap, request-only validation -- no need
        # to touch the lock for a request that's going to fail anyway.
        # From here on we're checking shared state, so lock this exact
        # slot for the rest of the transaction before reading it.
        acquire_slot_lock(slot_time)

        available, error = is_slot_available(slot_time, people)
        if not available:
            return jsonify({"success": False, "error": error}), 409

        reservation = Reservation(
            user_id=current_user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            people=people,
            slot_time=slot_time,
            status='confirmed'
        )

        db.session.add(reservation)
        db.session.commit()

        return jsonify({
            "success": True,
            "reservation": reservation.to_dict()
        })

    existing_reservations = Reservation.query.filter_by(
        user_id=current_user.id,
        status='confirmed'
    ).order_by(Reservation.slot_time).all()

    return render_template('reservations.html',
        reservations=[r.to_dict() for r in existing_reservations]
    )