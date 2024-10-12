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

class Category(db.Model):
    __tablename__ = "category"
    category_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    category_name = db.Column(db.String, unique=True, nullable=False)
    category_description = db.Column(db.String, nullable=False)
    picture = db.Column(db.String)  # Path to the uploaded picture

    def __init__(self, category_name, category_description, picture):
        self.category_name = category_name
        self.category_description = category_description
        self.picture = picture

class Service(db.Model):
    __tablename__ = "service"
    service_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Link to the supplier
    service_name = db.Column(db.String, unique=True, nullable=False)
    service_description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    price = db.Column(db.Integer)
    image = db.Column(db.String)  # Path to the uploaded image

    # Establishing relationships
    supplier = db.relationship('User', backref='services')  # Relationship to supplier (User)

    def __init__(self, category_id, supplier_id, service_name, service_description, price, image):
        self.category_id = category_id
        self.supplier_id = supplier_id  # Assign the supplier_id
        self.service_name = service_name
        self.service_description = service_description
        self.price = price
        self.image = image
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class ServiceRequest(db.Model):
    __tablename__ = "service_requests"
    service_request_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Link to supplier (optional)
    service_description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    date_issued = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    date_returned = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default='pending')  # 'pending', 'accepted', 'rejected', 'completed', 'returned', 'cancelled'
    price = db.Column(db.Integer, nullable=False)  # Price associated with the service

    def __init__(self, service_id, user_id, service_description, price, supplier_id=None, date_requested=None, date_issued=None, date_completed=None, date_returned=None):
        self.service_id = service_id
        self.user_id = user_id
        self.supplier_id = supplier_id
        self.service_description = service_description
        self.price = price
        self.date_requested = date_requested or datetime.utcnow()
        self.date_issued = date_issued
        self.date_completed = date_completed
        self.date_returned = date_returned
        self.status = 'pending'