from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from db import db
from model import User, Category

app = Flask(__name__)

#.....connect app and db.........
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db.init_app(app)

app.app_context().push()

# -- Picture Upload  --
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -- Home, About and Contact --
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# -- Base Pages --
@app.route('/base')
def base():
    return render_template('base_users.html')

@app.route('/base_dashboard')
def base_dashboard():
    return render_template('base_dashboard.html')


# -- Login, Register and Logout --
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

        # Check if the password matches (using hashed password check)
        if not check_password_hash(user_record.password, password):
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
                password=generate_password_hash(password),  # Remember to hash the password
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
            document.save(f'static/Documents/{document_filename}')

            # Create a new supplier user instance
            new_supplier = User(
                full_name=full_name,
                username=username,
                email=email,
                password=generate_password_hash(password),  # Remember to hash the password
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


# -- Dashboards --

@app.route('/supplier_dashboard')
def supplier_dashboard():
    return render_template('supplier_dashboard.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer_dashboard.html')

@app.route('/admin_dashboard')
def Admin_dashboard():
    return render_template('admin_dashboard.html')

# -- Manage Categories --


@app.route('/category/category_dashboard.html', methods=['GET'])
def category_dashboard():
    categories = Category.query.all()
    return render_template('category/category_dashboard.html', categories=categories)


@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        category_description = request.form.get('category_description')
        picture = request.files.get('picture')

        # Check if the category already exists
        existing_category = Category.query.filter_by(category_name=category_name).first()
        if existing_category:
            flash("Category already exists.", "warning")
            return redirect(url_for('create_category'))

        # Validate the file
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)

            new_category = Category(category_name, category_description, filename)
            db.session.add(new_category)
            db.session.commit()
            flash("Category created successfully.", "success")
            return redirect(url_for('category_dashboard'))
        else:
            flash("Invalid picture format. Please upload an image file.", "warning")
            return redirect(url_for('create_category'))

    return render_template('category/create_category.html')

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    existing_category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        existing_category.category_name = request.form.get('category_name')
        existing_category.category_description = request.form.get('category_description')
        
        picture = request.files.get('picture')
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)
            existing_category.picture = filename
        
        db.session.commit()
        flash("Category updated successfully.", "success")
        return redirect(url_for('category_dashboard'))

    return render_template('category/edit_category.html', category=existing_category)

@app.route('/delete_category/<int:category_id>', methods=['GET', 'POST'])
def delete_category(category_id):
    existing_category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        db.session.delete(existing_category)
        db.session.commit()
        flash("Category deleted successfully.", "success")
        return redirect(url_for('category_dashboard'))

    return render_template('category/delete_category.html', category=existing_category)

#-- Run the app --
if __name__ == '__main__':
    with app.app_context():   #to connect app and db
        db.create_all()       #to create db
    app.run(debug=True)
