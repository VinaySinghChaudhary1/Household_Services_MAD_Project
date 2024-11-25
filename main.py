from flask import Flask, render_template, request, redirect, url_for, flash, session    # for flask
from flask_session import Session   # for session
from werkzeug.security import check_password_hash, generate_password_hash # for hashing
from werkzeug.utils import secure_filename     # for uploading
from datetime import datetime    # for Datetime
from collections import defaultdict  # for defaultdict
import os  # for path
from db import db    # for db
from model import User, Category, Service, ServiceRequest, Review , ContactMessage     # for models
from functools import wraps  # for login_required


app = Flask(__name__)

#.....connect app and db.........
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db.init_app(app)

app.app_context().push()

# -- Login Required Decorator --
def login_required(roles):
    def wrapper(original):
        @wraps(original)
        def inner(*args, **kwargs):
            # Convert the roles argument to a list by splitting the string by commas
            role_list = roles.split(', ')
            
            # Check if the session has a valid user and if the user's role is in the allowed roles
            if session.get("username") and session.get("role") in role_list:
                return original(*args, **kwargs)
            else:
                flash(f"You need to login as one of the following roles: {', '.join(role_list)}", "warning")
                return redirect(url_for("login"))

        return inner

    return wrapper


# -- Picture Upload  --
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'doc', 'docx'}
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

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Validate form data
        if not name or not email or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for('contact'))

        # Save message to the database
        contact_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(contact_message)
        db.session.commit()

        flash("Your message has been submitted successfully!", "success")
        return redirect(url_for('contact'))

    # Render the contact page template
    return render_template('contact/contact.html')

@app.route('/admin/contact_messages', methods=['GET'])
@login_required("admin")
def view_contact_messages():
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    # Fetch all messages from the database
    messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    return render_template('contact/view_contact_messages.html', messages=messages)



# -- Base Pages --
@app.route('/base')
@login_required("admin") # Add this line to ensure admin as decorator
def base():
    return render_template('base_users.html')

@app.route('/base_dashboard')
@login_required("admin")
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

        # Check if the user is blocked
        if user_record.is_blocked:
            flash("Your account has been blocked by the admin. Please contact support for more information.", "danger")
            return redirect(url_for('login'))

        # If the user is a supplier, check if they are verified
        if user_record.role == "supplier" and not user_record.is_verified:
            flash("Your account is awaiting approval from the admin. You cannot log in until verified.", "warning")
            return redirect(url_for('login'))

        # If all credentials are correct and user is not blocked/verified (if supplier), save user info in the session
        session['user_id'] = user_record.user_id
        session['username'] = user_record.username
        session['role'] = user_record.role

        # Double check that user_id is properly set in the session
        if 'user_id' in session:
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
        else:
            # If user_id is not set, flash an error message and redirect to login
            flash("An error occurred while setting session data. Please try again.", "danger")
            return redirect(url_for('login'))

    # Render the login page for GET request
    return render_template('users/login.html')

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        try:
            # Retrieve form data
            full_name = request.form.get('fullname')
            username = request.form.get('username')
            email = request.form.get('email')
            address = request.form.get('address')
            pincode = request.form.get('pincode')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Debug print statements for form data
            # print(f"Full name: {full_name}, Username: {username}, Email: {email}, Address: {address}, Pincode: {pincode}")

            # Validation checks
            if password != confirm_password:
                flash("Passwords do not match. Please try again.", "warning")
                return redirect(url_for('register_customer'))

            # Check if email or username already exists in the database
            existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
            if existing_user:
                flash("Email or username already exists. Please choose another one.", "danger")
                return redirect(url_for('register_customer'))

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create a new customer user instance
            new_customer = User(
                full_name=full_name,
                username=username,
                email=email,
                password=hashed_password,  # Hashed password
                address=address,
                pincode=pincode,
                role="customer"  # Role is set to 'customer'
            )

            # Add new customer to the database
            db.session.add(new_customer)
            db.session.commit()

            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            # Log the error for debugging
            print(f"Error during registration: {e}")
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect(url_for('register_customer'))

    # For GET request, render the registration page
    return render_template('users/register_customer.html')


@app.route('/register_supplier', methods=['GET', 'POST'])
def register_supplier():
    # Fetch all existing categories for the dropdown
    categories = Category.query.all()

    if request.method == 'POST':
        try:
            # Retrieve form data using .get() to avoid KeyError
            full_name = request.form.get('fullname')
            username = request.form.get('username')
            email = request.form.get('email')
            service_name = request.form.get('service_name')  # Use .get() to safely access the form field
            new_service_name = request.form.get('new_service_name')
            experience_years = request.form.get('experience')
            address = request.form.get('address')
            pincode = request.form.get('pincode')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            document = request.files.get('document')

            # Ensure at least one service name is provided
            if not service_name and not new_service_name:
                flash("Please select a service or type a new service name.", "warning")
                return redirect(url_for('register_supplier'))

            if service_name and new_service_name:
                flash("Please either select a service or type a new service name, not both.", "warning")
                return redirect(url_for('register_supplier'))

            # Use the appropriate service name
            final_service_name = new_service_name if new_service_name else service_name

            # Validation checks
            if password != confirm_password:
                flash("Passwords do not match", "warning")
                return redirect(url_for('register_supplier'))

            # Check if email or username already exists
            existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
            if existing_user:
                flash("Email or username already exists", "danger")
                return redirect(url_for('register_supplier'))

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Save the uploaded document
            document_filename = secure_filename(document.filename) if document else None
            if document:
                document.save(os.path.join('static/Documents', document_filename))

            # Create a new supplier user instance
            new_supplier = User(
                full_name=full_name,
                username=username,
                email=email,
                password=hashed_password,  # Store the hashed password
                address=address,
                pincode=pincode,
                role="supplier",
                service_name=final_service_name,
                experience_years=int(experience_years) if experience_years else None,
                document=document_filename
            )
            
            # Add the new supplier to the database
            db.session.add(new_supplier)

            # We DO NOT create a new category here; the category will be created upon admin approval.

            db.session.commit()

            # Successful registration flash message
            flash("Registration successful! Your account will be verified by an admin.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            # Handle errors during registration and provide debug information for the exception
            print(f"Error during supplier registration: {e}")
            flash("Something went wrong during registration. Please try again.", "danger")
            return redirect(url_for('register_supplier'))

    # For GET request, render the registration page with existing categories
    return render_template('users/register_supplier.html', categories=categories)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session data to log out the user
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))



# -- Search route --
@app.route('/search', methods=['GET'])
def search():
    # Get the search term from the request
    query = request.args.get('query', '').strip()
    if not query:
        flash("Please provide a keyword to search.", "info")
        return redirect(url_for('category_dashboard'))

    # Perform case-insensitive search in categories, services, and user details (name, address, pincode)
    matched_categories = Category.query.filter(
        (Category.category_name.ilike(f'%{query}%')) |   # Searching by category name
        (Category.category_description.ilike(f'%{query}%'))  # Searching by category description
    ).all()

    matched_services = Service.query.join(User).filter(
        (Service.service_name.ilike(f'%{query}%')) |   # Searching by service name
        (Service.service_description.ilike(f'%{query}%')) |    # Searching by service description
        (User.full_name.ilike(f'%{query}%')) |  # Searching by supplier's name
        (User.address.ilike(f'%{query}%')) |  # Searching by address
        (User.pincode.ilike(f'%{query}%'))  # Searching by pincode
    ).all()

    # Perform search for users by full name, username, and role
    matched_users = User.query.filter(
        (User.full_name.ilike(f'%{query}%')) |  # Searching by full name
        (User.username.ilike(f'%{query}%'))  # Searching by username
    ).all()

    # Search users by their name or username for admin purposes
    if session.get('role') == 'admin':
        matched_users = User.query.filter(
            (User.full_name.ilike(f'%{query}%')) | 
            (User.username.ilike(f'%{query}%'))
        ).all()
    else:
        matched_users = []  # Non-admins cannot see user search results

    # Render the search results template and pass the matches
    return render_template(
        'search_results.html',
        query=query,
        categories=matched_categories,
        services=matched_services,
        users=matched_users  # Pass user matches for admin
    )

    # Render the search results template and pass the matches
    return render_template('search_results.html', query=query, categories=matched_categories, services=matched_services, users=matched_users)



# -- Users Dashboards --
@app.route('/customer_dashboard', methods=['GET'])
@login_required("customer")
def customer_dashboard():
    user_id = session.get('user_id')
    
    # Fetch ongoing service requests (pending and accepted)
    service_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()

    # Fetch service history (completed, rejected, returned, and cancelled)
    history_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])).all()

    return render_template('dashboard/customer_dashboard.html', 
                           service_requests=service_requests, 
                           history_requests=history_requests)

@app.route('/supplier_dashboard', methods=['GET'])
@login_required("supplier")
def supplier_dashboard():
    user_id = session.get('user_id')
    
    # Get all services where the logged-in supplier is the owner (supplier_id)
    services = Service.query.filter_by(supplier_id=user_id).all()
    
    # Fetch ongoing service requests related to the supplier's services (pending and accepted)
    service_requests = ServiceRequest.query.filter(
        ServiceRequest.service_id.in_([service.service_id for service in services]),
        ServiceRequest.status.in_(['pending', 'accepted'])
    ).all()
    
    # Fetch service history (completed, returned, rejected, and cancelled)
    history_requests = ServiceRequest.query.filter(
        ServiceRequest.service_id.in_([service.service_id for service in services]),
        ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])
    ).all()

    return render_template('dashboard/supplier_dashboard.html', 
                           service_requests=service_requests,
                           history_requests=history_requests)

@app.route('/admin_dashboard', methods=['GET'])
@login_required("admin")
def admin_dashboard():
    # Fetch ongoing service requests (pending and accepted)
    service_requests = ServiceRequest.query.filter(
        ServiceRequest.status.in_(['pending', 'accepted'])
    ).all()
    
    # Fetch service history (completed, returned, rejected and cancelled)
    history_requests = ServiceRequest.query.filter(
        ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])
    ).all()

    return render_template('dashboard/admin_dashboard.html', 
                           service_requests=service_requests, 
                           history_requests=history_requests)




# -- Profile - Edit, Delete --
@app.route('/profile/<int:user_id>', methods=['GET'])
@login_required("admin, supplier, customer")
def profile(user_id):
    # Fetch the user by user_id
    user = User.query.get_or_404(user_id)
    # Admin can view any profile; non-admins can only view their own profile
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash("You do not have permission to view this profile.", "danger")
        return redirect(url_for('profile', user_id=session.get('user_id')))
    # Render the profile template with the user details
    return render_template('profile/profile.html', user=user)

@app.route('/edit_profile/<int:user_id>/', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Check if the logged-in user is allowed to edit this profile
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash("You do not have permission to edit this profile.", "danger")
        return redirect(url_for('profile', user_id=session.get('user_id')))
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.address = request.form.get('address')
        user.pincode = request.form.get('pincode')

        # Optional password update
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)

        # Only for suppliers: Update service-related fields
        if user.role == 'supplier':
            user.service_name = request.form.get('service_name')
            user.experience_years = request.form.get('experience_years')

            # Handle document upload
            document = request.files.get('document')
            if document:
                filename = secure_filename(document.filename)
                document.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.document = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        # Redirect to the profile page with user_id
        return redirect(url_for('profile', user_id=user_id))
    
    return render_template('profile/edit_profile.html', user=user)

@app.route('/delete_profile/<int:user_id>/', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def delete_profile(user_id):
    user = User.query.get_or_404(user_id)

    # Check if the logged-in user is allowed to delete this profile
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash("You do not have permission to delete this profile.", "danger")
        return redirect(url_for('profile', user_id=session.get('user_id')))

    if request.method == 'POST':
        # Delete all services associated with the supplier if the user is a supplier
        if user.role == 'supplier':
            services = Service.query.filter_by(supplier_id=user.user_id).all()
            for service in services:
                db.session.delete(service)
        
        # Delete the user (supplier or admin)
        db.session.delete(user)
        db.session.commit()
        flash("Profile and associated services deleted successfully!", "success")
        
        # If the admin deletes a profile, redirect back to the member list; otherwise, redirect to login
        if session.get('role') == 'admin':
            return redirect(url_for('member_list'))
        else:
            return redirect(url_for('login'))

    return render_template('profile/delete_profile.html', user=user)




# -- Admin - approval, block, unblock --
@app.route('/admin/members')
@login_required("admin")
def member_list():
    customers = User.query.filter_by(role='customer').all()
    suppliers = User.query.filter_by(role='supplier').all()
    waiting_approval = User.query.filter_by(role='supplier', is_verified=False).all()
    return render_template('admin/member_list.html', customers=customers, suppliers=suppliers, waiting_approval=waiting_approval)

@app.route('/admin/verify_supplier/<int:user_id>', methods=['POST'])
@login_required("admin")
def verify_supplier(user_id):
    supplier = User.query.get_or_404(user_id)

    # Verify if the user is a supplier and not already verified
    if supplier.role == 'supplier' and not supplier.is_verified:
        supplier.is_verified = True

        # Check if the supplier's service name should be added as a new category
        if supplier.service_name and not Category.query.filter_by(category_name=supplier.service_name).first():
            # Create a new category based on the supplier's service name
            new_category = Category(
                category_name=supplier.service_name,
                category_description="Automatically added by supplier registration",
                picture=None  # No picture initially, can be added later
            )
            db.session.add(new_category)

        # Commit changes to the database
        db.session.commit()

        flash(f'Supplier {supplier.full_name} has been verified, and the service "{supplier.service_name}" has been added as a category.', 'success')
    
    return redirect(url_for('member_list'))

@app.route('/admin/block_user/<int:user_id>', methods=['POST', 'GET'])
@login_required("admin")
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    # Toggle the blocked status
    user.is_blocked = not user.is_blocked
    db.session.commit()
    # Determine if user is blocked or unblocked
    status = "blocked" if user.is_blocked else "unblocked"
    flash(f'User {user.full_name} has been {status}.', 'success')
    # Redirect back to the appropriate view depending on where the request came from
    # If the user was searched from the search, redirect back to the search results
    # Otherwise, redirect to the member list
    if 'search' in request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('member_list'))

@app.route('/admin/unblock_user/<int:user_id>', methods=['POST', 'GET'])
@login_required("admin")
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    # Set the blocked status to False (unblock the user)
    if user.is_blocked:
        user.is_blocked = False
        db.session.commit()
        flash(f'User {user.full_name} has been unblocked.', 'success')
    else:
        flash(f'User {user.full_name} is already unblocked.', 'info')
    # Redirect back to the appropriate view depending on where the request came from
    if 'search' in request.referrer:
        return redirect(request.referrer)  # Redirect back to search results if action initiated from there
    else:
        return redirect(url_for('member_list'))  # Otherwise, redirect back to member list




# -- Manage Categories (Dashboard, Create, Edit, Delete) --
@app.route('/category_dashboard', methods=['GET'])
def category_dashboard():
    # Fetch all categories
    categories = Category.query.all()
    # Fetch all suppliers
    users = User.query.filter_by(role='supplier').all()
    # Fetch the currently logged-in user's details, if any
    current_user = None
    if 'user_id' in session:
        current_user = User.query.filter_by(user_id=session['user_id']).first()

    return render_template('category/category_dashboard.html', categories=categories, users=users, current_user=current_user)

@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    # Ensure the user is logged in and is an admin
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You must be logged in as an admin to create a category.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Admin can create a new category
        category_name = request.form.get('category_name')
        category_description = request.form.get('category_description')
        picture = request.files.get('picture')

        # Check if a valid category name was provided
        if not category_name:
            flash("Please enter a valid category name.", "warning")
            return redirect(url_for('create_category'))

        # Check if the category already exists
        existing_category = Category.query.filter_by(category_name=category_name).first()
        if existing_category:
            flash("Category already exists.", "warning")
            return redirect(url_for('create_category'))

        # Validate the picture file
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)
        else:
            filename = None  # No picture uploaded or invalid file format

        # Create a new category
        new_category = Category(category_name, category_description, filename)
        db.session.add(new_category)
        db.session.commit()

        flash("Category created successfully.", "success")
        return redirect(url_for('category_dashboard'))

    # Render the create category template for admin
    return render_template('category/create_category.html')

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    existing_category = Category.query.get(category_id)

    # Redirect if the category is not found
    if not existing_category:
        flash("The requested category does not exist.", "warning")
        return redirect(url_for('category_dashboard'))

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to edit a category.', 'danger')
        return redirect(url_for('login'))

    # If the user is a supplier, ensure they can only edit categories matching their service name
    if session.get('role') == 'supplier':
        # Get the supplier's registered service name
        supplier = User.query.filter_by(user_id=session.get('user_id')).first()
        if supplier and existing_category.category_name != supplier.service_name:
            flash("You can only edit your own service category.", "danger")
            return redirect(url_for('category_dashboard'))

    if request.method == 'POST':
        # Update category fields
        if session.get('role') == 'admin':
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
    existing_category = Category.query.get(category_id)

    # Redirect if the category is not found
    if not existing_category:
        flash("The requested category does not exist.", "warning")
        return redirect(url_for('category_dashboard'))

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to delete a category.', 'danger')
        return redirect(url_for('login'))

    # Role-based check for category deletion permissions
    if session.get('role') == 'supplier':
        # Get the supplier's registered service name
        supplier = User.query.filter_by(user_id=session.get('user_id')).first()
        if supplier and existing_category.category_name != supplier.service_name:
            flash("You can only delete your own service category.", "danger")
            return redirect(url_for('category_dashboard'))

    if request.method == 'POST':
        # Delete the category from the database
        db.session.delete(existing_category)
        db.session.commit()
        flash("Category deleted successfully.", "success")
        return redirect(url_for('category_dashboard'))

    # Render the delete confirmation template
    return render_template('category/delete_category.html', category=existing_category)




# -- Manage Services (Dashboard, Create, Edit, Delete) --
@app.route('/service_dashboard/<int:category_id>', methods=['GET'])
def service_dashboard(category_id):
    # Check if the category exists
    category = Category.query.get(category_id)
    if not category:
        flash('The requested category does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to category dashboard if category doesn't exist

    # Fetch services for the given category
    services = Service.query.filter_by(category_id=category_id).all()

    # Calculate the average rating for each supplier
    for service in services:
        reviews = Review.query.filter_by(supplier_id=service.supplier_id).all()
        if reviews:
            avg_rating = sum(review.rating for review in reviews) / len(reviews)
        else:
            avg_rating = 0  # No reviews, default to 0
        service.supplier.avg_rating = round(avg_rating, 1)  # Assign avg_rating to supplier dynamically

    return render_template('service/service_dashboard.html', services=services, category=category)

@app.route('/create_service/<int:category_id>', methods=['GET', 'POST'])
def create_service(category_id):
    # Check if the category exists, if not, redirect to the category dashboard
    category = Category.query.get(category_id)
    if not category:
        flash('The requested category does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to create a service.', 'danger')
        return redirect(url_for('login'))  # Redirect to login if not authorized

    # If the user is a supplier, ensure they can only create services in their own category (service_name)
    if session.get('role') == 'supplier':
        supplier = User.query.filter_by(user_id=session.get('user_id')).first()
        if supplier and supplier.service_name != category.category_name:
            flash("You can only create services in your own service category.", 'danger')
            return redirect(url_for('category_dashboard'))

    if request.method == 'POST':
        # Extract form data
        service_name = request.form['service_name']
        service_description = request.form['service_description']
        price = request.form['price']
        image = request.files['image']
        supplier_id = session['user_id']  # Use the logged-in user's ID (admin or supplier)

        # Handle file upload (image)
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Create a new service
            new_service = Service(
                category_id=category_id,
                supplier_id=supplier_id,  # Link to the logged-in supplier or admin
                service_name=service_name,
                service_description=service_description,
                price=price,
                image=filename
            )
            db.session.add(new_service)
            db.session.commit()

            flash('Service created successfully!', 'success')
            return redirect(url_for('service_dashboard', category_id=category_id))
        else:
            flash('Invalid image file. Please upload a valid image file.', 'danger')

    return render_template('service/create_service.html', category_id=category_id)

@app.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    # Fetch the service
    service = Service.query.get(service_id)
    if not service:
        flash('The requested service does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to the category dashboard

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to edit this service.', 'danger')
        return redirect(url_for('login'))

    # If the user is a supplier, ensure they can only edit services they own (check full_name and username)
    if session.get('role') == 'supplier':
        supplier = User.query.filter_by(user_id=session.get('user_id')).first()
        if supplier and (supplier.full_name != service.supplier.full_name or supplier.username != service.supplier.username):
            flash("You can only edit your own services.", 'danger')
            return redirect(url_for('service_dashboard', category_id=service.category_id))

    if request.method == 'POST':
        service.service_name = request.form['service_name']
        service.service_description = request.form['service_description']
        service.price = request.form['price']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            service.image = filename

        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('service_dashboard', category_id=service.category_id))

    return render_template('service/edit_service.html', service=service)

@app.route('/confirm_delete_service/<int:service_id>', methods=['GET', 'POST'])
def confirm_delete_service(service_id):
    # Fetch the service
    service = Service.query.get(service_id)
    if not service:
        flash('The requested service does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to a default category service dashboard

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to delete this service.', 'danger')
        return redirect(url_for('login'))

    # If the user is a supplier, ensure they can only delete services they own (check full_name and username)
    if session.get('role') == 'supplier':
        supplier = User.query.filter_by(user_id=session.get('user_id')).first()
        if supplier and (supplier.full_name != service.supplier.full_name or supplier.username != service.supplier.username):
            flash("You can only delete your own services.", 'danger')
            return redirect(url_for('service_dashboard', category_id=service.category_id))

    if request.method == 'POST':
        if request.form.get("confirm") == "yes":
            # Perform the delete operation
            db.session.delete(service)
            db.session.commit()
            flash('Service deleted successfully!', 'success')
            return redirect(url_for('service_dashboard', category_id=service.category_id))
        else:
            # If "No" is selected, cancel the deletion and return to the dashboard
            flash('Service deletion canceled.', 'info')
            return redirect(url_for('service_dashboard', category_id=service.category_id))

    return render_template('service/delete_service.html', service=service)







# -- Service Requests (Dashboard, Create, Edit, Delete) --
@app.route('/service_requests', methods=['GET'])
@login_required("admin, supplier, customer")
def view_service_requests():
    user_id = session.get('user_id')
    role = session.get('role')
    if role == 'customer':
        # Fetch ongoing service requests and service history for the customer
        service_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])).all()
    elif role == 'supplier':
        # Fetch ongoing service requests and service history for the supplier
        service_requests = ServiceRequest.query.join(Service).filter(Service.supplier_id == user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.join(Service).filter(Service.supplier_id == user_id).filter(ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])).all()
    else:
        # Admin view: Fetch all ongoing service requests and service history
        service_requests = ServiceRequest.query.filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.filter(ServiceRequest.status.in_(['completed', 'returned', 'rejected', 'cancelled'])).all()
    return render_template('service_requests/service_requests.html', service_requests=service_requests, service_history=service_history)

@app.route('/service_requests/create/<int:service_id>', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def create_service_request(service_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in to create a service request.', 'warning')
        return redirect(url_for('login'))

    # Check if the service exists
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        # Capture data from the form
        service_description = request.form['service_description']
        price = request.form['price']
        user_id = session['user_id']

        # Optional experience years field
        experience_years = request.form.get('experience_years', None)  # Fetch experience_years if provided

        # Create a new service request
        new_request = ServiceRequest(
            service_id=service_id,
            user_id=user_id,
            service_description=service_description,
            price=price,
            experience_years=experience_years  # Optional field passed here
        )
        db.session.add(new_request)
        db.session.commit()

        flash('Service request created successfully!', 'success')
        return redirect(url_for('view_service_requests'))

    # Pass the service object to the template for pre-populating the form
    return render_template('service_requests/create_service_request.html', service_id=service_id, service=service)

@app.route('/service_requests/update/<int:service_request_id>', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def update_service_request(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    
    if request.method == 'POST':
        status = request.form['status']
        if status in ['accepted', 'rejected', 'completed', 'returned', 'cancelled']:
            service_request.status = status
            if status == 'accepted':
                service_request.date_issued = datetime.utcnow()
            elif status == 'completed':
                service_request.date_completed = datetime.utcnow()
            elif status == 'returned':
                service_request.date_returned = datetime.utcnow()
            elif status == 'cancelled':
                pass
            db.session.commit()
            flash('Service request updated successfully!', 'success')
        else:
            flash('Invalid status!', 'danger')
        return redirect(url_for('view_service_requests'))

    # Render the update form
    return render_template('service_requests/update_service_request.html', service_request=service_request)

@app.route('/service_requests/delete/<int:service_request_id>', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def delete_service_request(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)

    if request.method == 'POST':
        db.session.delete(service_request)
        db.session.commit()
        flash('Service request deleted successfully!', 'success')
        return redirect(url_for('view_service_requests'))

    # Render confirmation page for deletion
    return render_template('service_requests/delete_service_request.html', service_request_id=service_request_id)




# -- Reviews (Leave Review) --
@app.route('/leave_review/<int:service_request_id>', methods=['GET', 'POST'])
@login_required("admin, supplier, customer")
def leave_review(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)

    # Allow review for completed, returned, rejected and cancelled services only
    if session.get('user_id') != service_request.user_id or service_request.status.strip().lower() not in ['completed', 'returned', 'rejected', 'cancelled']:
        flash('You are not authorized to leave a review for this service.', 'danger')
        return redirect(url_for('customer_dashboard'))


    # Fetch the review history for this service request
    review_history = Review.query.filter_by(service_request_id=service_request_id, customer_id=session.get('user_id')).all()

    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        # Create the review and store it in the database
        new_review = Review(
            service_id=service_request.service_id,
            service_request_id=service_request_id,
            customer_id=service_request.user_id,
            supplier_id=service_request.service.supplier_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()

        flash('Your review has been submitted!', 'success')
        return redirect(url_for('customer_dashboard'))

    return render_template('reviews/leave_review.html', 
                           service_request=service_request, 
                           review_history=review_history)

@app.route('/reviews/<int:service_request_id>', methods=['GET'])
@login_required("admin, supplier, customer")
def view_reviews(service_request_id):
    # Fetch all reviews for the given service request
    reviews = Review.query.filter_by(service_request_id=service_request_id).all()

    if not reviews:
        # Redirect based on user role
        if session.get('role') == 'admin':
            flash("No reviews found for this service request.", "info")
            return redirect(url_for('admin_dashboard'))
        elif session.get('role') == 'supplier':
            flash("No reviews found for this service request.", "info")
            return redirect(url_for('supplier_dashboard'))

    return render_template('reviews/view_reviews.html', reviews=reviews)

@app.route('/reply_to_review/<int:review_id>', methods=['POST'])
@login_required("admin, supplier, customer")
def reply_to_review(review_id):
    review = Review.query.get_or_404(review_id)

    # Check if the logged-in user is allowed to reply (must be the supplier or an admin)
    if session.get('role') not in ['supplier', 'admin'] or (session.get('role') == 'supplier' and session.get('user_id') != review.supplier_id):
        flash('You are not authorized to reply to this review.', 'danger')
        return redirect(url_for('view_reviews', service_request_id=review.service_request_id))

    # Save the reply
    review.reply = request.form.get('reply')
    db.session.commit()

    flash('Your reply has been submitted!', 'success')
    return redirect(url_for('view_reviews', service_request_id=review.service_request_id))



# -- Order Details --
@app.route('/order_details/<int:service_request_id>')
@login_required("admin, supplier, customer")
def order_details(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    return render_template('service_requests/order_details.html', service_request=service_request)



# -- Summary -- customer, admin, supplier

@app.route('/summary/customer/<int:user_id>')
@login_required("admin, customer")
def customer_summary(user_id):
    # Check if the logged-in user is an admin
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash("Unauthorized access to the customer summary.", "danger")
        return redirect(url_for('login'))

    # Fetch data for the specified customer
    service_requests = ServiceRequest.query.filter_by(user_id=user_id).all()
    pending_count = sum(1 for req in service_requests if req.status == 'pending')
    accepted_count = sum(1 for req in service_requests if req.status == 'accepted')
    rejected_count = sum(1 for req in service_requests if req.status == 'rejected')
    completed_count = sum(1 for req in service_requests if req.status == 'completed')
    returned_count = sum(1 for req in service_requests if req.status == 'returned')
    cancelled_count = sum(1 for req in service_requests if req.status == 'cancelled')  # Added Cancelled Count

    # Render the customer summary template
    return render_template('summary/customer_summary.html', 
                           service_requests=service_requests, 
                           pending_count=pending_count, 
                           accepted_count=accepted_count,
                           rejected_count=rejected_count,
                           completed_count=completed_count,
                           returned_count=returned_count,
                           cancelled_count=cancelled_count)  # Pass Cancelled Count

@app.route('/summary/supplier/<int:user_id>')
@login_required("admin, supplier, customer")
def supplier_summary(user_id):
    # Check if the logged-in user is an admin
    if session.get('role') != 'admin' and session.get('role') != 'supplier':
        flash("Unauthorized access to the supplier summary.", "danger")
        return redirect(url_for('login'))

    # Fetch data for the specified supplier by joining with the Service model
    service_requests = ServiceRequest.query.join(Service).filter(Service.supplier_id == user_id).all()

    # Calculate counts for each status
    pending_count = sum(1 for req in service_requests if req.status == 'pending')
    accepted_count = sum(1 for req in service_requests if req.status == 'accepted')
    rejected_count = sum(1 for req in service_requests if req.status == 'rejected')
    completed_count = sum(1 for req in service_requests if req.status == 'completed')
    returned_count = sum(1 for req in service_requests if req.status == 'returned')
    cancelled_count = sum(1 for req in service_requests if req.status == 'cancelled')

    # Calculate average rating for the supplier
    reviews = Review.query.filter_by(supplier_id=user_id).all()
    avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0

    # Render the supplier summary template
    return render_template('summary/supplier_summary.html', 
                           service_requests=service_requests,
                           pending_count=pending_count, 
                           accepted_count=accepted_count,
                           rejected_count=rejected_count,
                           completed_count=completed_count,
                           returned_count=returned_count,
                           cancelled_count=cancelled_count,
                           avg_rating=avg_rating)

@app.route('/summary/admin')
@login_required("admin")
def admin_summary():
    if session.get('role') != 'admin':
        flash("Unauthorized access to the admin summary.", "danger")
        return redirect(url_for('login'))

    # Fetch data for the admin summary
    total_requests = ServiceRequest.query.count()
    pending_count = ServiceRequest.query.filter_by(status='pending').count()
    accepted_count = ServiceRequest.query.filter_by(status='accepted').count()
    rejected_count = ServiceRequest.query.filter_by(status='rejected').count()
    completed_count = ServiceRequest.query.filter_by(status='completed').count()
    returned_count = ServiceRequest.query.filter_by(status='returned').count()
    cancelled_count = ServiceRequest.query.filter_by(status='cancelled').count()

    # Calculate average rating for all suppliers
    reviews = Review.query.all()
    avg_rating = round(sum(review.rating for review in reviews) / len(reviews), 1) if reviews else 0

    # Fetch counts of customers and suppliers
    customer_count = User.query.filter_by(role='customer').count()
    supplier_count = User.query.filter_by(role='supplier').count()

    return render_template('summary/admin_summary.html', 
                           total_requests=total_requests, 
                           pending_count=pending_count, 
                           accepted_count=accepted_count,
                           rejected_count=rejected_count,
                           completed_count=completed_count,
                           returned_count=returned_count,
                           avg_rating=avg_rating,
                           customer_count=customer_count,
                           cancelled_count=cancelled_count,
                           supplier_count=supplier_count)



#-- Run the app --
if __name__ == '__main__':
    with app.app_context():   #to connect app and db
        db.create_all()       #to create db
    app.run(debug=True)
