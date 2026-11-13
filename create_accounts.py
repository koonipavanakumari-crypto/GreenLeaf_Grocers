from app import app
from database.db import db
from database.models import User
from werkzeug.security import generate_password_hash

accounts = [
    ("admin", "admin123", "admin"),
    ("cashier1", "cashier123", "cashier"),
    ("cashier2", "cashier123", "cashier"),
    ("cashier3", "cashier123", "cashier"),
    ("cashier4", "cashier123", "cashier"),
    ("cashier5", "cashier123", "cashier"),
]

with app.app_context():
    for username, password, role in accounts:
        user = User.query.filter_by(username=username).first()

        if user:
            print(f"Already exists: {username}")
            continue

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)

    db.session.commit()
    print("Login accounts setup completed!")
