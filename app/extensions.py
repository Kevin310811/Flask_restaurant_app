"""Shared Flask extension instances.

These live in their own module (instead of app/__init__.py) so that
route modules like auth.py can import them without a circular import:
app/__init__.py imports every blueprint at the top, so a blueprint that
did `from app import bcrypt` would run before bcrypt was defined.
Both app/__init__.py and auth.py import the SAME bcrypt object from
here, so the one init_app() call in create_app() configures it for both.
"""
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()