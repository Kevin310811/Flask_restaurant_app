"""Admin analytics: page, JSON data endpoint, and expense management.

Design decisions (matching the existing app's rules):

- The DB stores naive UTC timestamps (see utcnow() in models.py). The
  restaurant operates in India, whose zone is a fixed UTC+05:30 with
  no DST, so filters like "this month" are computed on the IST wall
  clock and shifted back to UTC for querying. The app has no timezone
  setting; RESTAURANT_TZ_OFFSET is the single place to change if one
  is ever added. Expenses carry a plain calendar date, so their series
  buckets use IST dates directly.

- Revenue follows the dashboard's established rule: only orders with
  status='paid' count towards money. Pending / cancelled / void orders
  are excluded from sums but still appear in order counts and the
  status breakdown.

- "Total lifetime orders" counts every order row ever created (the
  same number the dashboard card shows); the page shows the split by
  status. Keep lifetime totals range-independent (KPI 1 / accounts).

- Series are fetched as small, window-bounded row-tuples (one row per
  order / account / expense / order-item inside the selected range)
  and bucketed into day/week/month groups in Python. This is portable
  across SQLite/Postgres and exact for IST boundaries; the row count
  is bounded by the window, never the whole table, and the DB still
  does the heavy aggregates (COUNT / SUM / GROUP BY).
"""

import calendar
from bisect import bisect_right
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app.models import db, Expense, MenuItem, Order, OrderItem, User
from app.routes.admin import admin_required

# India Standard Time: UTC+05:30, fixed all year (no DST).
RESTAURANT_TZ_OFFSET = timedelta(hours=5, minutes=30)
MONEY_QUANTUM = Decimal('0.01')
MAX_EXPENSE_AMOUNT = Decimal('10000000')  # sanity ceiling: one crore

analytics_bp = Blueprint('analytics', __name__)

EXPENSE_CATEGORIES = (
    'Produce', 'Dairy', 'Meat & Seafood', 'Groceries', 'Beverages',
    'Staff', 'Rent', 'Utilities', 'Marketing', 'Equipment', 'Other',
)

RANGE_LABELS = {
    '7': 'Last 7 days',
    '30': 'Last 30 days',
    '90': 'Last 90 days',
    'month': 'This month',
    'last_month': 'Last month',
    'year': 'This year',
    'all': 'All time',
}


# --------------------------------------------------------------------------
# Time helpers
# --------------------------------------------------------------------------

def _now_utc():
    """Naive UTC now, matching utcnow() in models.py."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ist_now():
    """Naive IST wall-clock now (UTC + 05:30)."""
    return _now_utc() + RESTAURANT_TZ_OFFSET


def _add_months(d, n):
    """A date shifted n calendar months, clamped to the month length."""
    m0 = d.month - 1 + n
    year = d.year + m0 // 12
    month = m0 % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _ist_midnight_utc(d):
    """Naive-UTC datetime of IST midnight for IST calendar date d."""
    return datetime.combine(d, time.min) - RESTAURANT_TZ_OFFSET


def _round2(value):
    """Number -> float at 2dp, None-safe (missing sums read as 0.00)."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value if value is not None else 0))
    return float(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP))


def _pct_change(cur, prev):
    """Percentage change, only when the denominator is real data.

    Returns None for an empty previous period so the UI can show "new"
    or "no change" instead of an invented number.
    """
    if prev is None or prev == 0:
        return None
    return round((cur - prev) / prev * 100, 1)


# --------------------------------------------------------------------------
# Range / interval resolution
# --------------------------------------------------------------------------

def _resolve_range(key):
    """Turn a range key into [start, end) windows in naive UTC.

    Day-based ranges use full IST calendar days (the current day is
    partially elapsed); month/year ranges use real calendar bounds.
    Every window also yields the previous equivalent window for the
    period-over-period comparisons. All-time has no previous window.
    """
    ist_today = _ist_now().date()

    if key == 'all':
        return dict(start=None, end=None, prev_start=None, prev_end=None,
                    prev_label=None, start_ist_date=None, end_ist_date=None)

    if key in ('7', '30', '90'):
        days = int(key)
        start_date = ist_today - timedelta(days=days - 1)
        end_date = ist_today + timedelta(days=1)
        prev_start_date = start_date - timedelta(days=days)
        prev_label = f'previous {days} days'
    elif key == 'month':
        start_date = ist_today.replace(day=1)
        end_date = _add_months(start_date, 1)
        prev_start_date = _add_months(start_date, -1)
        prev_label = 'previous calendar month'
    elif key == 'last_month':
        start_date = _add_months(ist_today.replace(day=1), -1)
        end_date = ist_today.replace(day=1)
        prev_start_date = _add_months(start_date, -1)
        prev_label = 'month before last'
    elif key == 'year':
        start_date = date(ist_today.year, 1, 1)
        end_date = date(ist_today.year + 1, 1, 1)
        prev_start_date = date(ist_today.year - 1, 1, 1)
        prev_label = 'previous calendar year'
    else:  # caller validates against RANGE_LABELS
        raise ValueError(f'unknown range key: {key}')

    return dict(
        start=_ist_midnight_utc(start_date),
        end=_ist_midnight_utc(end_date),
        prev_start=_ist_midnight_utc(prev_start_date),
        prev_end=_ist_midnight_utc(start_date),
        prev_label=prev_label,
        start_ist_date=start_date,
        end_ist_date=end_date,
    )


def _auto_interval(window_days):
    """Sensible aggregation when the visitor hasn't picked one."""
    if window_days <= 45:
        return 'day'
    if window_days <= 130:
        return 'week'
    return 'month'


def _maybe_coerce(interval, window_days):
    """Guard against absurd bucket counts (e.g. a manual 'daily' over years).

    Returns (interval, note). The note is only set when the interval had
    to be downgraded — the UI surfaces it as a caption.
    """
    if interval == 'day' and window_days > 400:
        return 'week', 'Too many days to plot one bar each — switched to weekly.'
    if interval == 'week' and window_days > 1400:
        return 'month', 'Too many weeks to plot one bar each — switched to monthly.'
    return interval, None


class _Bucket:
    """One time-series bucket: [start, end) as naive IST datetimes."""
    __slots__ = ('start', 'end', 'label')

    def __init__(self, start, end, label):
        self.start = start
        self.end = end
        self.label = label


def _build_buckets(interval, start_ist_date, end_ist_date):
    """Ordered buckets covering [start_ist_date, end_ist_date)."""
    buckets = []
    if interval == 'day':
        d = start_ist_date
        while d < end_ist_date:
            mid = datetime.combine(d, time.min)
            buckets.append(_Bucket(mid, mid + timedelta(days=1), f'{d.day} {d.strftime("%b")}'))
            d += timedelta(days=1)
    elif interval == 'week':
        # Monday-anchored weeks; the first bucket may begin before the
        # window start so it still covers the window's first days.
        cur = start_ist_date - timedelta(days=start_ist_date.weekday())
        while cur < end_ist_date:
            mid = datetime.combine(cur, time.min)
            buckets.append(_Bucket(mid, mid + timedelta(days=7), f'wk of {cur.day} {cur.strftime("%b")}'))
            cur += timedelta(days=7)
    else:  # month
        y, m = start_ist_date.year, start_ist_date.month
        while date(y, m, 1) < end_ist_date:
            nxt = _add_months(date(y, m, 1), 1)
            buckets.append(_Bucket(datetime(y, m, 1), datetime.combine(nxt, time.min),
                                   f'{calendar.month_abbr[m]} {y}'))
            y, m = nxt.year, nxt.month
    return buckets


def _bucket_index(buckets, ts_ist):
    """Index of the bucket containing ts_ist, or -1 if before the first."""
    return bisect_right([b.start for b in buckets], ts_ist) - 1


def _zero_series(n):
    """[paid, other, revenue, expenses, accounts] zeros for n buckets."""
    return [[0] * n, [0] * n, [0] * n, [0] * n, [0] * n]


# --------------------------------------------------------------------------
# Row fetchers (window-bounded; the DB filters, Python buckets)
# --------------------------------------------------------------------------

def _earliest_record_date():
    """Earliest date any order / account / expense exists (for All time)."""
    values = [
        db.session.query(func.min(Order.created_at)).scalar(),
        db.session.query(func.min(User.created_at)).scalar(),
        db.session.query(func.min(Expense.spent_on)).scalar(),
    ]
    dates = [v.date() if isinstance(v, datetime) else v for v in values if v is not None]
    return min(dates) if dates else None


def _order_rows(fetch_from, end):
    """(created_at, status, total, tip, user_id) tuples inside the window.

    fetch_from may reach further back than the current window so the
    previous period can be derived by partitioning in Python — one
    query serves both.
    """
    q = db.session.query(Order.created_at, Order.status, Order.total, Order.tip, Order.user_id)
    if fetch_from is not None:
        q = q.filter(Order.created_at >= fetch_from)
    if end is not None:
        q = q.filter(Order.created_at < end)
    return q.all()


def _split_periods(rows, window):
    """Partition rows into (current, previous) by created_at (naive UTC)."""
    cur, prev = [], []
    start, prev_start = window['start'], window['prev_start']
    for row in rows:
        ts = row[0] + RESTAURANT_TZ_OFFSET
        if start is None or ts >= start:
            cur.append(row)
        elif prev_start is not None and ts >= prev_start:
            prev.append(row)
    return cur, prev


def _paid_money(rows):
    """(revenue, tips, paid_order_count) for a set of order tuples."""
    revenue = Decimal('0')
    tips = Decimal('0')
    orders = 0
    for _ts, status, total, tip, _user in rows:
        if status == 'paid':
            orders += 1
            revenue += total or Decimal('0')
            tips += tip or Decimal('0')
    return revenue, tips, orders


# --------------------------------------------------------------------------
# Series bucketing
# --------------------------------------------------------------------------

def _series_block(window, interval, orders, account_rows, expense_rows):
    """Bucket every series for the chart panel in one pass."""
    start_ist, end_ist = window['start_ist_date'], window['end_ist_date']
    buckets = _build_buckets(interval, start_ist, end_ist)
    starts = [b.start for b in buckets]
    paid, other, revenue, expenses, accounts = _zero_series(len(buckets))

    for created_at, status, total, _tip, _user in orders:
        idx = bisect_right(starts, created_at + RESTAURANT_TZ_OFFSET) - 1
        if idx < 0:
            continue
        if status == 'paid':
            paid[idx] += 1
            revenue[idx] += float(total or 0)
        else:
            other[idx] += 1

    for (created_at,) in account_rows:
        idx = bisect_right(starts, created_at + RESTAURANT_TZ_OFFSET) - 1
        if idx >= 0:
            accounts[idx] += 1

    for spent_on, amount in expense_rows:
        ts = datetime.combine(spent_on, time.min)
        idx = bisect_right(starts, ts) - 1
        if idx >= 0:
            expenses[idx] += float(amount or 0)

    return {
        'interval': interval,
        'labels': [b.label for b in buckets],
        'orders_paid': paid,
        'orders_other': other,
        'revenue': [float(_round2(Decimal(str(v)))) for v in revenue],
        'expenses': [float(_round2(Decimal(str(v)))) for v in expenses],
        'new_accounts': accounts,
    }, len(buckets)


# --------------------------------------------------------------------------
# KPI assembly
# --------------------------------------------------------------------------

def _kpi_block(window, cur_rows, prev_rows):
    """KPI card values + period-over-period comparisons."""
    lifetime_status = dict(
        db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all())
    lifetime_orders = sum(lifetime_status.values())

    account_total = db.session.query(func.count(User.id)).scalar() or 0
    admin_total = db.session.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0

    cur_rev, cur_tips, cur_paid = _paid_money(cur_rows)
    prev_rev, _prev_tips, _prev_paid = _paid_money(prev_rows)

    cur_users = {r[4] for r in cur_rows if r[4] is not None}
    prev_users = {r[4] for r in prev_rows if r[4] is not None}
    paid_user_counts = Counter(r[4] for r in cur_rows if r[1] == 'paid' and r[4] is not None)
    repeat_customers = sum(1 for count in paid_user_counts.values() if count >= 2)

    aov = None
    if cur_paid > 0:
        aov = _round2(cur_rev / cur_paid)

    prev_label = window['prev_label']
    return {
        'lifetime_orders': {
            'count': lifetime_orders,
            'status': lifetime_status,
        },
        'orders_period': {
            'count': len(cur_rows),
            'prev': len(prev_rows) if prev_label else None,
            'prev_label': prev_label,
            'pct': _pct_change(len(cur_rows), len(prev_rows) if prev_label else None),
        },
        'customers_period': {
            'count': len(cur_users),
            'prev': len(prev_users) if prev_label else None,
            'prev_label': prev_label,
            'pct': _pct_change(len(cur_users), len(prev_users) if prev_label else None),
            'repeat': repeat_customers,
        },
        'accounts': {
            'total': account_total,
            'admins': admin_total,
            'customers': account_total - admin_total,
        },
        'revenue': {
            'total': _round2(cur_rev),
            'tips': _round2(cur_tips),
            'orders': cur_paid,
            'prev': _round2(prev_rev) if prev_label else None,
            'prev_label': prev_label,
            'pct': _pct_change(float(_round2(cur_rev)), float(_round2(prev_rev)) if prev_label else None),
        },
        'aov': {
            'value': aov,
            'orders': cur_paid,
        },
    }


# --------------------------------------------------------------------------
# Trending items
# --------------------------------------------------------------------------

def _trending_rows(start, end):
    """Order-item lines of PAID orders inside the window.

    Snapshots (title/price/qty) are read off OrderItem so deleted menu
    items still appear; menu_item_id is NULL for them (ON DELETE SET NULL)
    and they are grouped by the snapshot title.
    """
    q = (db.session.query(OrderItem.menu_item_id, OrderItem.title, OrderItem.qty,
                          OrderItem.price, Order.id)
         .join(Order, OrderItem.order_id == Order.id)
         .filter(Order.status == 'paid'))
    if start is not None:
        q = q.filter(Order.created_at >= start)
    if end is not None:
        q = q.filter(Order.created_at < end)
    return q.all()


def _trending_block(rows, metric):
    groups = {}
    for mid, title, qty, price, order_id in rows:
        qty = qty or 0
        price = price or Decimal('0')
        key = (mid, title)
        g = groups.setdefault(key, {
            'title': title, 'menu_item_id': mid,
            'qty': 0, 'revenue': Decimal('0'), 'order_ids': set(),
        })
        g['qty'] += qty
        g['revenue'] += price * qty
        g['order_ids'].add(order_id)

    total_qty = sum(g['qty'] for g in groups.values())
    total_revenue = sum((g['revenue'] for g in groups.values()), Decimal('0'))

    # One query for every referenced item's image (no N+1). Deleted
    # items have menu_item_id NULL and simply render without a photo.
    ids = {g['menu_item_id'] for g in groups.values() if g['menu_item_id'] is not None}
    images = {}
    if ids:
        image_rows = db.session.query(MenuItem.id, MenuItem.image).filter(MenuItem.id.in_(ids)).all()
        images = {r[0]: r[1] for r in image_rows}

    rank_key = (lambda g: (g['qty'], g['revenue'])) if metric == 'qty' \
        else (lambda g: (g['revenue'], g['qty']))
    ranked = sorted(groups.values(), key=rank_key, reverse=True)[:8]

    denominator = total_qty if metric == 'qty' else total_revenue
    items = []
    for g in ranked:
        if metric == 'qty':
            share = (g['qty'] / total_qty * 100) if total_qty else 0
        else:
            share = (g['revenue'] / total_revenue * 100) if total_revenue else 0
        items.append({
            'title': g['title'],
            'image': images.get(g['menu_item_id']),
            'orders': len(g['order_ids']),
            'qty': g['qty'],
            'revenue': _round2(g['revenue']),
            'share': round(share, 1),
        })

    return {
        'metric': metric,
        'total_qty': total_qty,
        'total_revenue': _round2(total_revenue),
        'items': items,
    }


# --------------------------------------------------------------------------
# Expenses
# --------------------------------------------------------------------------

def _expense_summary(start_ist, end_ist):
    """Totals, category breakdown and the recent list for the window."""
    q = db.session.query(Expense.category, func.sum(Expense.amount)) \
        .group_by(Expense.category)
    if start_ist is not None:
        q = q.filter(Expense.spent_on >= start_ist)
    if end_ist is not None:
        q = q.filter(Expense.spent_on < end_ist)
    by_category = {cat: _round2(total) for cat, total in q.all()}

    count_q = db.session.query(func.count(Expense.id))
    if start_ist is not None:
        count_q = count_q.filter(Expense.spent_on >= start_ist)
    if end_ist is not None:
        count_q = count_q.filter(Expense.spent_on < end_ist)

    recent_q = Expense.query.order_by(Expense.spent_on.desc(), Expense.id.desc())
    if start_ist is not None:
        recent_q = recent_q.filter(Expense.spent_on >= start_ist)
    if end_ist is not None:
        recent_q = recent_q.filter(Expense.spent_on < end_ist)

    return {
        'categories': list(EXPENSE_CATEGORIES),
        'total': _round2(sum(by_category.values())),
        'count': count_q.scalar() or 0,
        'by_category': by_category,
        'recent': [e.to_dict() for e in recent_q.limit(8)],
    }


def _authorize_admin():
    """JSON-safe admin gate for the /api/admin/* routes.

    admin_required redirects, which turns a fetch into an HTML 200 of
    the homepage — JSON callers need JSON status codes instead.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Please log in.'}), 401
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required.'}), 403
    return None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@analytics_bp.route('/admin/analytics', endpoint='page')
@login_required
@admin_required
def analytics_page():
    return render_template('admin/analytics.html',
                           expense_categories=EXPENSE_CATEGORIES,
                           today_iso=_ist_now().date().isoformat())


@analytics_bp.route('/api/admin/analytics', endpoint='data')
@login_required
def analytics_data():
    denied = _authorize_admin()
    if denied:
        return denied

    range_key = request.args.get('range', '30')
    if range_key not in RANGE_LABELS:
        return jsonify({'error': f'Unknown range "{range_key}".'}), 400

    metric = request.args.get('metric', 'qty')
    if metric not in ('qty', 'revenue'):
        return jsonify({'error': f'Unknown metric "{metric}".'}), 400

    requested_interval = request.args.get('interval')
    if requested_interval is not None and requested_interval not in ('day', 'week', 'month'):
        return jsonify({'error': f'Unknown interval "{requested_interval}".'}), 400

    window = _resolve_range(range_key)

    # All time: anchor the buckets at the earliest record.
    if window['start_ist_date'] is None:
        earliest = _earliest_record_date()
        window['start_ist_date'] = earliest or _ist_now().date()
        window['end_ist_date'] = _ist_now().date() + timedelta(days=1)

    days = max(1, (window['end_ist_date'] - window['start_ist_date']).days)
    interval = requested_interval or _auto_interval(days)
    interval, coerce_note = _maybe_coerce(interval, days)

    # One query serves the current AND previous window (see _order_rows).
    fetch_from = window['prev_start'] if window['prev_start'] is not None else window['start']
    orders = _order_rows(fetch_from, window['end'])
    cur_rows, prev_rows = _split_periods(orders, window)

    acct_q = db.session.query(User.created_at)
    if window['start'] is not None:
        acct_q = acct_q.filter(User.created_at >= window['start'])
    if window['end'] is not None:
        acct_q = acct_q.filter(User.created_at < window['end'])
    account_rows = acct_q.all()

    exp_q = db.session.query(Expense.spent_on, Expense.amount)
    if window['start_ist_date'] is not None:
        exp_q = exp_q.filter(Expense.spent_on >= window['start_ist_date'])
    if window['end_ist_date'] is not None:
        exp_q = exp_q.filter(Expense.spent_on < window['end_ist_date'])
    expense_rows = exp_q.all()

    series, bucket_count = _series_block(window, interval, cur_rows,
                                         account_rows, expense_rows)

    kpis = _kpi_block(window, cur_rows, prev_rows)
    trending = _trending_block(_trending_rows(window['start'], window['end']), metric)
    expense_summary = _expense_summary(window['start_ist_date'], window['end_ist_date'])

    # Orders by status inside the window (doughnut), most-first.
    status_counts = dict(Counter(r[1] for r in cur_rows))
    status_counts = dict(sorted(status_counts.items(), key=lambda kv: -kv[1]))

    return jsonify({
        'range': range_key,
        'range_label': RANGE_LABELS[range_key],
        'interval': interval,
        'coerced_note': coerce_note,
        'metric': metric,
        'generated_at': _ist_now().isoformat(timespec='seconds'),
        'kpis': kpis,
        'series': series,
        'bucket_count': bucket_count,
        'status_counts': status_counts,
        'trending': trending,
        'expenses': expense_summary,
    })


@analytics_bp.route('/api/admin/expenses', methods=['POST'], endpoint='add_expense')
@login_required
def add_expense():
    denied = _authorize_admin()
    if denied:
        return denied

    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Expense title is required.'}), 400
    if len(title) > 100:
        return jsonify({'error': 'Expense title must be 100 characters or fewer.'}), 400

    category = data.get('category')
    if category not in EXPENSE_CATEGORIES:
        return jsonify({'error': 'Choose a valid expense category.'}), 400

    try:
        amount = Decimal(str(data.get('amount', '')))
    except (InvalidOperation, ValueError):
        return jsonify({'error': 'Amount must be a valid number.'}), 400
    if amount <= 0:
        return jsonify({'error': 'Amount must be greater than zero.'}), 400
    if amount > MAX_EXPENSE_AMOUNT:
        return jsonify({'error': 'Amount is too large.'}), 400

    raw_date = data.get('spent_on')
    if not raw_date:
        return jsonify({'error': 'Expense date is required.'}), 400
    try:
        spent_on = date.fromisoformat(str(raw_date))
    except ValueError:
        return jsonify({'error': 'Expense date must be YYYY-MM-DD.'}), 400
    if spent_on > _ist_now().date():
        return jsonify({'error': 'Expense date cannot be in the future.'}), 400

    expense = Expense(
        title=title,
        category=category,
        amount=amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
        spent_on=spent_on,
        created_by=current_user.id,
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201


@analytics_bp.route('/api/admin/expenses/<int:expense_id>/delete', methods=['POST'],
                    endpoint='delete_expense')
@login_required
def delete_expense(expense_id):
    denied = _authorize_admin()
    if denied:
        return denied

    expense = db.session.get(Expense, expense_id)
    if expense is None:
        return jsonify({'error': 'Expense not found.'}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({'ok': True})
