import os
from dotenv import load_dotenv

load_dotenv()

def _env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')

class Config:
    # The secret key signs Flask's session cookies. A known constant here
    # would let anyone forge cookies -- including Flask-Login's user id --
    # and impersonate any user or admin. Fail loudly instead.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Add it to your .env file (local dev) "
            "or the hosting environment. Sessions cannot be signed safely "
            "without it."
        )

    # Cookie hardening. SameSite=Lax is safe for the login flow; the
    # Secure flag is off here because local dev runs plain http://127.0.0.1,
    # and stays off unless SESSION_COOKIE_SECURE is set (enable it if you
    # ever run the app behind HTTPS).
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', default=False)
    # Don't accept giant request bodies (DoS guard); there is no upload feature.
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    raw_url = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant.db'
    # Older URLs use postgres://; modern tooling needs postgresql://
    if raw_url.startswith('postgres://'):
        raw_url = raw_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = raw_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Razorpay: key_id is not secret (it's sent to the browser to open
    # the checkout widget), but key_secret must never leave the server
    # -- it's what verify_payment_signature() uses to confirm a payment
    # actually came from Razorpay and wasn't forged client-side.
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')