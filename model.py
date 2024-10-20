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

    # Fields specific to suppliers, make them nullable
    service_name = db.Column(db.String, nullable=True)  # Nullable for customers
    experience_years = db.Column(db.Integer, nullable=True)  # Nullable for customers
    document = db.Column(db.String, nullable=True)  # Nullable for customers

    is_verified = db.Column(db.Boolean, default=False)  # For supplier verification
    is_blocked = db.Column(db.Boolean, default=False)  # For blocking/unblocking users

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
        self.is_verified = False  # New suppliers are not verified by default
        self.is_blocked = False  # New users are not blocked by default



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
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)  # Link to Category model
    supplier_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)  # Link to the supplier with cascade delete
    service_name = db.Column(db.String, unique=True, nullable=False)
    service_description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    price = db.Column(db.Integer)
    image = db.Column(db.String)  # Path to the uploaded image

    # Establishing relationships
    supplier = db.relationship('User', backref='services')  # Relationship to supplier (User)
    category = db.relationship('Category', backref='services')  # Relationship to Category
    
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
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Link to supplier (optional)
    service_description = db.Column(db.String, nullable=False)
    experience_years = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    date_issued = db.Column(db.DateTime, nullable=True)  #accepted date
    date_completed = db.Column(db.DateTime, nullable=True)
    date_returned = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default='pending')  # 'pending', 'accepted', 'rejected', 'completed', 'returned', 'cancelled'
    price = db.Column(db.Integer, nullable=False)  # Price associated with the service

    # Relationships
    customer = db.relationship('User', foreign_keys=[user_id], backref='customer_requests')
    supplier = db.relationship('User', foreign_keys=[supplier_id], backref='supplier_requests')
    service = db.relationship('Service', backref='requests')

    def __init__(self, service_id, user_id, service_description, experience_years, price, supplier_id=None, date_requested=None, date_issued=None, date_completed=None, date_returned=None):
        self.service_id = service_id
        self.user_id = user_id
        self.supplier_id = supplier_id
        self.service_description = service_description
        self.experience_years = experience_years
        self.price = price
        self.date_requested = date_requested or datetime.utcnow()
        self.date_issued = date_issued
        self.date_completed = date_completed
        self.date_returned = date_returned
        self.status = 'pending'


class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.service_request_id'), nullable=False)  # Link to the specific service request
    customer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating from 1 to 5
    comment = db.Column(db.String(500))  # Optional comment for the review
    reply = db.Column(db.String(500))  # Supplier/Admin reply to the review
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    service = db.relationship('Service', backref='reviews')
    service_request = db.relationship('ServiceRequest', backref='reviews')  # Relationship to service request
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_reviews')
    supplier = db.relationship('User', foreign_keys=[supplier_id], backref='supplier_reviews')

    def __init__(self, service_id, service_request_id, customer_id, supplier_id, rating, comment=None, reply=None):
        self.service_id = service_id
        self.service_request_id = service_request_id  # Assign the service_request_id
        self.customer_id = customer_id
        self.supplier_id = supplier_id
        self.rating = rating
        self.comment = comment
        self.reply = reply
        self.created_at = datetime.utcnow()

