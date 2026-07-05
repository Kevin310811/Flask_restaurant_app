from flask import Blueprint, render_template, request, jsonify, session
from app.models import db, Reservation
from datetime import datetime, timedelta
import uuid

main_bp = Blueprint('main', __name__)

SLOT_INTERVAL_MINUTES = 20
MAX_RESERVATIONS_PER_SLOT = 2
MAX_PEOPLE_PER_SLOT = 10
OPENING_HOUR = 8
OPENING_MINUTE = 40
CLOSING_HOUR = 23

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def snap_to_slot(dt):
    minutes = (dt.minute // SLOT_INTERVAL_MINUTES) * SLOT_INTERVAL_MINUTES
    return dt.replace(minute=minutes, second=0, microsecond=0)

def is_slot_available(slot_time, people):
    existing = Reservation.query.filter_by(
        slot_time=slot_time,
        status='confirmed'
    ).all()

    if len(existing) >= MAX_RESERVATIONS_PER_SLOT:
        return False, "This time slot is fully booked. Please choose another time."

    total_people = sum(r.people for r in existing) + people
    if total_people > MAX_PEOPLE_PER_SLOT:
        return False, f"This time slot can only accommodate {MAX_PEOPLE_PER_SLOT - sum(r.people for r in existing)} more people."

    return True, None

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

    while current < end:
        existing = Reservation.query.filter_by(
            slot_time=current,
            status='confirmed'
        ).all()

        total_people = sum(r.people for r in existing)
        reservations_count = len(existing)

        available = (
            reservations_count < MAX_RESERVATIONS_PER_SLOT and
            total_people < MAX_PEOPLE_PER_SLOT
        )

        slots.append({
            "time": current.strftime('%H:%M'),
            "display": current.strftime('%I:%M %p'),
            "available": available,
            "spots_left": MAX_PEOPLE_PER_SLOT - total_people
        })

        current += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    return jsonify(slots)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/gallery')
def gallery():
    return render_template('gallery.html')

@main_bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        data = request.get_json()

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

        people = int(data.get('people', 1))
        if people < 1 or people > 12:
            return jsonify({"success": False, "error": "Party size must be between 1 and 12."}), 400

        available, error = is_slot_available(slot_time, people)
        if not available:
            return jsonify({"success": False, "error": error}), 409

        reservation = Reservation(
            session_id=get_session_id(),
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            phone=data.get('phone', '').strip(),
            email=data.get('email', '').strip(),
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

    session_id = get_session_id()
    existing_reservations = Reservation.query.filter_by(
        session_id=session_id,
        status='confirmed'
    ).order_by(Reservation.slot_time).all()

    return render_template('reservations.html',
        reservations=[r.to_dict() for r in existing_reservations]
    )