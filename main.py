from flask import Flask, render_template, request, redirect, url_for, flash, session    # for flask
from flask_session import Session   # for session
from werkzeug.security import check_password_hash, generate_password_hash # for hashing
from werkzeug.utils import secure_filename     # for uploading
from datetime import datetime    # for Datetime
import os  # for path
from db import db    # for db
from model import User, Category, Service, ServiceRequest, Review       # for models
from functools import wraps  # for login_required


app = Flask(__name__)

#.....connect app and db.........
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'

db.init_app(app)

app.app_context().push()

# -- Login Required Decorator --
def login_required(role):
    def wrapper(original):
        @wraps(original)
        def inner(*args, **kwargs):  # *args = list of arguments, **kwargs = key word arguments 
            if session.get("username") and session.get("role") == role:
                return original(*args, **kwargs)
            else:
                flash(f"You need to login as {role}", "warning")
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

@app.route('/contact')
def contact():
    return render_template('contact.html')



# -- Base Pages --
@app.route('/base')
@login_required(role="admin") # Add this line to ensure admin as decorator
def base():
    return render_template('base_users.html')

@app.route('/base_dashboard')
@login_required(role="admin")
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
    return redirect(url_for('login'))



# -- Search route --
@app.route('/search', methods=['GET'])
def search():
    # Get the search term from the request
    query = request.args.get('query', '').strip()
    if not query:
        flash("Please provide a keyword to search.", "info")
        return redirect(url_for('category_dashboard'))
    # Perform case-insensitive search in categories and services
    matched_categories = Category.query.filter(
        (Category.category_name.ilike(f'%{query}%')) | (Category.category_description.ilike(f'%{query}%'))
    ).all()
    matched_services = Service.query.filter(
        (Service.service_name.ilike(f'%{query}%')) | (Service.service_description.ilike(f'%{query}%'))
    ).all()
    # Render a search results template and pass the matches
    return render_template('search_results.html', query=query, categories=matched_categories, services=matched_services)



# -- Users Dashboards --
@app.route('/customer_dashboard', methods=['GET'])
@login_required(role="customer")
def customer_dashboard():
    user_id = session.get('user_id')
    
    # Fetch ongoing service requests (pending and accepted)
    service_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()

    # Fetch service history (completed or returned)
    history_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['completed', 'returned'])).all()

    return render_template('dashboard/customer_dashboard.html', 
                           service_requests=service_requests, 
                           history_requests=history_requests)

@app.route('/supplier_dashboard', methods=['GET'])
@login_required(role="supplier")
def supplier_dashboard():
    user_id = session.get('user_id')
    # Get all services where the logged-in supplier is the owner (supplier_id)
    services = Service.query.filter_by(supplier_id=user_id).all()
    # Fetch ongoing service requests related to the supplier's services
    service_requests = ServiceRequest.query.filter(ServiceRequest.service_id.in_([service.service_id for service in services]),
                                                   ServiceRequest.status.in_(['pending', 'accepted'])).all()
    # Fetch completed or returned service requests
    history_requests = ServiceRequest.query.filter(ServiceRequest.service_id.in_([service.service_id for service in services]),
                                                   ServiceRequest.status.in_(['completed', 'returned'])).all()
    return render_template('dashboard/supplier_dashboard.html', 
                           service_requests=service_requests,
                           history_requests=history_requests)

@app.route('/admin_dashboard', methods=['GET'])
@login_required(role="admin")
def admin_dashboard():
    # Fetch ongoing service requests
    service_requests = ServiceRequest.query.filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
    
    # Fetch completed or returned service requests
    history_requests = ServiceRequest.query.filter(ServiceRequest.status.in_(['completed', 'returned'])).all()

    return render_template('dashboard/admin_dashboard.html', 
                           service_requests=service_requests, 
                           history_requests=history_requests)



# -- Profile - Edit, Delete --
@app.route('/profile', methods=['GET'])
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    return render_template('profile/profile.html', user=user)

@app.route('/edit_profile/<int:user_id>/', methods=['GET', 'POST'])
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
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
        return redirect(url_for('profile'))
    
    return render_template('profile/edit_profile.html', user=user)

@app.route('/delete_profile/<int:user_id>/', methods=['GET', 'POST'])
def delete_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Only allow deleting if the logged-in user matches the user_id in the URL
    if user_id != session.get('user_id'):
        flash("You do not have permission to delete this profile.", "danger")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash("Profile deleted successfully!", "success")
        return redirect(url_for('login'))
    
    return render_template('profile/delete_profile.html', user=user)




# -- Manage Categories (Dashboard, Create, Edit, Delete) --
@app.route('/category/category_dashboard.html', methods=['GET'])
def category_dashboard():
    categories = Category.query.all()
    return render_template('category/category_dashboard.html', categories=categories)

@app.route('/create_category', methods=['GET', 'POST'])
# @login_required(role="admin, supplier")  # Add this line to ensure admin or supplier as decorator
def create_category():
    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to create a category.', 'danger')
        return redirect(url_for('login'))

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
# @login_required(role="admin, supplier")
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
# @login_required(role="admin, supplier")
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

    if request.method == 'POST':
        db.session.delete(existing_category)
        db.session.commit()
        flash("Category deleted successfully.", "success")
        return redirect(url_for('category_dashboard'))

    return render_template('category/delete_category.html', category=existing_category)




# -- Manage Services (Dashboard, Create, Edit, Delete) --
@app.route('/service_dashboard/<int:category_id>', methods=['GET'])
def service_dashboard(category_id):
    # Check if the category exists
    category = Category.query.get(category_id)
    if not category:
        flash('The requested category does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to home if category doesn't exist
    # Fetch services for the given category
    services = Service.query.filter_by(category_id=category_id).all()
    return render_template('service/service_dashboard.html', services=services, category=category)

@app.route('/create_service/<int:category_id>', methods=['GET', 'POST'])
# @login_required(role="admin, supplier")
def create_service(category_id):
    # Check if the category exists, if not, redirect to home
    category = Category.query.get(category_id)
    if not category:
        flash('The requested category does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to create a service.', 'danger')
        return redirect(url_for('login'))  # Redirect to login if not authorized

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
# @login_required(role="admin, supplier")
def edit_service(service_id):
    # Manually check if the service exists
    service = Service.query.get(service_id)
    if not service:
        flash('The requested service does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to service dashboard (use a default category ID)

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to edit this service.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        service.service_name = request.form['service_name']
        service.service_description = request.form['service_description']
        service.price = request.form['price']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            service.image = filename

        # Supplier ID remains unchanged
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('service_dashboard', category_id=service.category_id))

    return render_template('service/edit_service.html', service=service)

@app.route('/confirm_delete_service/<int:service_id>', methods=['GET', 'POST'])
# @login_required(role="admin, supplier")
def confirm_delete_service(service_id):
    # Manually check if the service exists
    service = Service.query.get(service_id)
    if not service:
        flash('The requested service does not exist.', 'warning')
        return redirect(url_for('category_dashboard'))  # Redirect to a default category service dashboard (you can modify category_id)

    # Ensure the user is logged in and is either an admin or supplier
    if 'user_id' not in session or session.get('role') not in ['admin', 'supplier']:
        flash('You must be logged in as an admin or supplier to delete this service.', 'danger')
        return redirect(url_for('login'))

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
def view_service_requests():
    user_id = session.get('user_id')
    role = session.get('role')
    if role == 'customer':
        # Fetch ongoing service requests and service history for the customer
        service_requests = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.filter_by(user_id=user_id).filter(ServiceRequest.status.in_(['completed', 'returned'])).all()
    elif role == 'supplier':
        # Fetch ongoing service requests and service history for the supplier
        service_requests = ServiceRequest.query.join(Service).filter(Service.supplier_id == user_id).filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.join(Service).filter(Service.supplier_id == user_id).filter(ServiceRequest.status.in_(['completed', 'returned'])).all()
    else:
        # Admin view: Fetch all ongoing service requests and service history
        service_requests = ServiceRequest.query.filter(ServiceRequest.status.in_(['pending', 'accepted'])).all()
        service_history = ServiceRequest.query.filter(ServiceRequest.status.in_(['completed', 'returned'])).all()
    return render_template('service_requests/service_requests.html', service_requests=service_requests, service_history=service_history)

@app.route('/service_requests/create/<int:service_id>', methods=['GET', 'POST'])
def create_service_request(service_id):
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
def update_service_request(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    
    if request.method == 'POST':
        status = request.form['status']
        if status in ['accepted', 'rejected', 'completed', 'returned']:
            service_request.status = status
            if status == 'accepted':
                service_request.date_issued = datetime.utcnow()
            elif status == 'completed':
                service_request.date_completed = datetime.utcnow()
            elif status == 'returned':
                service_request.date_returned = datetime.utcnow()
            db.session.commit()
            flash('Service request updated successfully!', 'success')
        else:
            flash('Invalid status!', 'danger')
        return redirect(url_for('view_service_requests'))

    # Render the update form
    return render_template('service_requests/update_service_request.html', service_request=service_request)

@app.route('/service_requests/delete/<int:service_request_id>', methods=['GET', 'POST'])
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
def leave_review(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)

    # Allow review for completed, returned, or rejected services only
    if session.get('user_id') != service_request.user_id or service_request.status not in ['completed', 'returned', 'rejected']:
        flash('You are not authorized to leave a review for this service.', 'danger')
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        # Create the review and store it in the database
        new_review = Review(
            service_id=service_request.service_id,
            service_request_id=service_request_id,  # Add service_request_id to the review
            customer_id=service_request.user_id,
            supplier_id=service_request.service.supplier_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()

        flash('Your review has been submitted!', 'success')
        return redirect(url_for('customer_dashboard'))

    return render_template('reviews/leave_review.html', service_request=service_request)

@app.route('/reviews/<int:service_request_id>', methods=['GET'])
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



# -- Order Details --
@app.route('/order_details/<int:service_request_id>')
def order_details(service_request_id):
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    return render_template('service_requests/order_details.html', service_request=service_request)



#-- Run the app --
if __name__ == '__main__':
    with app.app_context():   #to connect app and db
        db.create_all()       #to create db
    app.run(debug=True)
