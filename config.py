import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    raw_url = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant.db'
    # Fix Render's postgres:// prefix
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