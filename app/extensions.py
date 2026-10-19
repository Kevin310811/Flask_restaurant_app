"""Shared Flask extension instances.

These live in their own module (instead of app/__init__.py) so that
route modules like auth.py can import them without a circular import:
app/__init__.py imports every blueprint at the top, so a blueprint that
did `from app import bcrypt` would run before bcrypt was defined.
Both app/__init__.py and auth.py import the SAME instances from here,
so the one init_app() call in create_app() configures them all.
"""
import os
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

bcrypt = Bcrypt()

# In-memory rate limiting: per-worker, resets on restart. Sufficient to
# blunt brute-force attempts; point RATELIMIT_STORAGE_URI at a Redis
# instance if this ever scales to multiple workers/instances.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://'),
    default_limits=[],
)