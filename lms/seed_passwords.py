"""
The schema.sql seed data inserts placeholder password hashes because MySQL
cannot compute Werkzeug's password hash function. Run this script ONCE after
loading schema.sql to set real, working passwords for the demo accounts.

Usage:
    python seed_passwords.py

Default password for every demo account: password123
"""
from app import create_app
from app.extensions import db
from app.models import User

DEFAULT_PASSWORD = "password123"

app = create_app()

with app.app_context():
    users = User.query.all()
    if not users:
        print("No users found. Did you load database/schema.sql into MySQL first?")
    for u in users:
        u.set_password(DEFAULT_PASSWORD)
    db.session.commit()
    print(f"Updated password for {len(users)} user(s). Default password: '{DEFAULT_PASSWORD}'")
