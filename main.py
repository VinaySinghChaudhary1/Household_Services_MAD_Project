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
def home():
    return render_template('home.html')

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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        # Query the user by username first
        user_record = User.query.filter_by(username=username).first()

        # Check if the user exists
        if not user_record:
            flash("Username does not exist. Please check and try again.", "warning")
            return redirect(url_for('login'))

        # Check if the email matches with the username
        if user_record.email != email:
            flash("Email does not match the username. Please check and try again.", "warning")
            return redirect(url_for('login'))

        # Check if the password matches
        if user_record.password != password:
            flash("Incorrect password. Please try again.", "warning")
            return redirect(url_for('login'))

        # Check if the role matches
        if user_record.role != role:
            flash("Role does not match with the user. Please check and try again.", "warning")
            return redirect(url_for('login'))

        # If all credentials are correct, save user information in the session
        session['user_id'] = user_record.user_id
        session['username'] = user_record.username
        session['role'] = user_record.role

        # Redirect to the appropriate dashboard based on the role with a success message
        if user_record.role == "customer":
            flash("Welcome, Customer!", "success")
            return redirect(url_for('customer_dashboard'))
        elif user_record.role == "supplier":
            flash("Welcome, Supplier!", "success")
            return redirect(url_for('supplier_dashboard'))
        elif user_record.role == "admin":
            flash("Welcome, Admin!", "success")
            return redirect(url_for('admin_dashboard'))

    # Render the login page for GET request
    return render_template('users/login.html')


@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation checks for password mismatch
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "warning")
            return redirect(url_for('register_customer'))

        # Check if email or username already exists in the database
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("Email or username already exists. Please choose another one.", "danger")
            return redirect(url_for('register_customer'))

        try:
            # Create a new customer user instance
            new_customer = User(
                full_name=full_name,
                username=username,
                email=email,
                password=password,  # Remember to hash the password
                address=address,
                pincode=pincode,
                role="customer"
            )
            
            # Add new customer to the database
            db.session.add(new_customer)
            db.session.commit()

            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect(url_for('register_customer'))

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
            flash("Passwords do not match", "warning")
            return redirect(url_for('register_supplier'))

        # Check if email or username already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("Email or username already exists", "danger")
            return redirect(url_for('register_supplier'))

        try:
            # Save the uploaded document
            document_filename = document.filename
            document.save(f'Static/Documents/{document_filename}')

            # Create a new supplier user instance
            new_supplier = User(
                full_name=full_name,
                username=username,
                email=email,
                password=password,  # Ideally, hash the password before saving
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

            # Successful registration flash message
            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            # Handle any errors during the registration process
            flash("Something went wrong during registration. Please try again.", "danger")
            return redirect(url_for('register_supplier'))

    # For GET request, render the registration page
    return render_template('users/register_supplier.html')
        
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session data to log out the user
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('home'))

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
