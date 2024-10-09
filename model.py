from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

from db import db

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    pincode = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # 'customer' or 'supplier'
    service_name = db.Column(db.String)  # Only applicable if the user is a supplier
    experience_years = db.Column(db.Integer)  # Only applicable if the user is a supplier
    document = db.Column(db.String)  # Path or name of the uploaded document, only for suppliers

    def __init__(self, full_name, username, email, password, address, pincode, role, service_name=None, experience_years=None, document=None):
        self.full_name = full_name
        self.username = username
        self.email = email
        self.password = password
        self.address = address
        self.pincode = pincode
        self.role = role
        self.service_name = service_name
        self.experience_years = experience_years
        self.document = document

