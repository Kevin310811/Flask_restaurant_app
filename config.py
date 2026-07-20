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