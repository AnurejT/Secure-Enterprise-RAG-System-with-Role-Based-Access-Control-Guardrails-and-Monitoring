"""
backend/core/extensions.py
Flask extension singletons — initialised here, bound to app in app.py
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()
