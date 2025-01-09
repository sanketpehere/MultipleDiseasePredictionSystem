from app import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.current_timestamp())

    def __repr__(self):
        return f'<User {self.email}>'
