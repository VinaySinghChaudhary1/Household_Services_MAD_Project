from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session

from db import db
from model import User


app = Flask(__name__)

#.....connect app and db.........
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db.init_app(app)

app.app_context().push()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about/<user_name>')
def about(user_name):
    return render_template('about.html', name=user_name)

# @app.route('/contact')

@app.route('/base')
def base():
    return render_template('base_users.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Query the user from the database
        user_record = User.query.filter_by(username=username, email=email, password=password, role=role).first()
        if user_record:
            # Save user information in the session
            session['user_id'] = user_record.user_id
            session['username'] = user_record.username
            session['role'] = user_record.role

            # Redirect to the appropriate dashboard based on the role
            if user_record.role == "customer":
                return redirect(url_for('customer_dashboard'))
            elif user_record.role == "supplier":
                return redirect(url_for('supplier_dashboard'))
            elif user_record.role == "admin":
                return redirect(url_for('admin_dashboard'))

        else:
            # Return login page with an error message if credentials are invalid
            return render_template('users/login.html', error="Invalid credentials or role")

    # Render the login page for GET request
    return render_template('users/login.html')


@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        address = request.form['address']
        pincode = request.form['pincode']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation checks
        if password != confirm_password:
            # Handle password mismatch
            return render_template('users/register_customer.html', error="Passwords do not match")

        # Check if email or username already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            return render_template('users/register_customer.html', error="Email or username already exists")

        # Create a new customer user instance
        new_customer = User(
            full_name=full_name,
            username=username,
            email=email,
            password=password,
            address=address,
            pincode=pincode,
            role="customer"
        )
        
        # Add new customer to the database
        db.session.add(new_customer)
        db.session.commit()

        # Debug print to verify this point is reached
        print("Registration successful, redirecting to login")

        # Redirect to the login page after successful registration
        return redirect(url_for('login'))

    # For GET request, render the registration page
    return render_template('users/register_customer.html')


@app.route('/register_supplier', methods=['GET', 'POST'])
def register_supplier():
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        service_name = request.form['service_name']
        experience_years = request.form['experience']
        address = request.form['address']
        pincode = request.form['pincode']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        document = request.files['document']  # For file upload

        # Validation checks
        if password != confirm_password:
            # Handle password mismatch
            return render_template('users/register_supplier.html', error="Passwords do not match")

        # Check if email or username already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            return render_template('register_supplier.html', error="Email or username already exists")

        # Save the uploaded document if necessary (file storage logic can be implemented as needed)
        document_filename = document.filename
        document.save(f'Static/Documents/{document_filename}')

        # Create a new supplier user instance
        new_supplier = User(
            full_name=full_name,
            username=username,
            email=email,
            password=password,
            address=address,
            pincode=pincode,
            role="supplier",
            service_name=service_name,
            experience_years=int(experience_years),
            document=document_filename
        )
        
        # Add new supplier to the database
        db.session.add(new_supplier)
        db.session.commit()

        # Redirect to the login page after successful registration
        return redirect(url_for('login'))

    # For GET request, render the registration page
    return render_template('users/register_supplier.html')
        

# @app.route('/logout')

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer_dashboard.html')


@app.route('/supplier_dashboard')
def supplier_dashboard():
    return render_template('supplier_dashboard.html')


@app.route('/admin_dashboard')
def Admin_dashboard():
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    with app.app_context():   #to connect app and db
        db.create_all()       #to create db
    app.run(debug=True)
