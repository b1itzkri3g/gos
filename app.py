from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import json
import datetime
import pytz
import random
from werkzeug.utils import secure_filename
from functools import wraps
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeField, Form
from wtforms.validators import DataRequired
import uuid
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images', 'products')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['VISITS_FILE'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'visits.json'))
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection

# CSRF protection removed
# csrf = CSRFProtect(app)

# Set timezone to Yangon
YANGON_TZ = pytz.timezone('Asia/Rangoon')  # Rangoon is the timezone name for Yangon

# Template filters
@app.template_filter('fromisoformat')
def fromisoformat_filter(value):
    """Convert ISO format date string to datetime object"""
    if not value:
        return datetime.datetime.now(YANGON_TZ)
    try:
        dt = datetime.datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=YANGON_TZ)
        return dt
    except (ValueError, TypeError):
        return datetime.datetime.now(YANGON_TZ)

@app.template_filter('datetimeformat')
def datetimeformat_filter(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object to a string"""
    if not value:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=YANGON_TZ)
    return value.strftime(format)

@app.template_filter('tojson')
def tojson_filter(obj):
    """Convert Python object to JSON string for use in HTML templates"""
    return json.dumps(obj)

# Form classes
class LoginForm(Form):  # Changed from FlaskForm to Form
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class GiftBoxForm(Form):  # Changed from FlaskForm to Form
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    gift_type = SelectField('Gift Type', choices=[
        ('discount', 'Discount Coupon'),
        ('free_product', 'Free Product'),
        ('bundle', 'Special Bundle')
    ], validators=[DataRequired()])
    discount_amount = StringField('Discount Amount (%)') 
    product_id = SelectField('Product', coerce=int)
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duration_hours = SelectField('Duration (hours)', choices=[
        ('1', '1 hour'), ('3', '3 hours'), ('6', '6 hours'), 
        ('12', '12 hours'), ('24', '24 hours'), ('48', '48 hours'),
        ('72', '3 days'), ('168', '7 days'), ('336', '14 days'), ('720', '30 days')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Gift Box')

# Global Constants
VISITS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'visits.json'))
PRODUCTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'products.json'))
GIFTBOXES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'giftboxes.json'))
SETTINGS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'settings.json'))

def get_products():
    """Load products from JSON file"""
    try:
        products_path = PRODUCTS_FILE  # Use the relative path directly
        if os.path.exists(products_path):
            with open(products_path, 'r') as f:
                return json.load(f)
        else:
            # Try alternative locations
            alt_paths = [
                os.path.join('gos', PRODUCTS_FILE),
                os.path.join(os.path.dirname(__file__), PRODUCTS_FILE)
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    print(f"Found products file at {path}")
                    with open(path, 'r') as f:
                        return json.load(f)
            
            # If we get here, no file was found
            print(f"Products file not found. Locations tried: {products_path}, {alt_paths}")
            empty_products = []
            save_products(empty_products)
            return empty_products
    except Exception as e:
        print(f"Error loading products: {e}")
        # Return empty list on error
        return []

def get_giftboxes():
    """Load gift boxes from JSON file"""
    try:
        # Try with the defined path
        giftboxes_path = GIFTBOXES_FILE
        if os.path.exists(giftboxes_path):
            with open(giftboxes_path, 'r') as f:
                return json.load(f)
        
        # Try alternative paths
        alt_paths = [
            os.path.join('gos', GIFTBOXES_FILE),
            os.path.join(os.path.dirname(__file__), 'giftboxes.json')
        ]
        
        for path in alt_paths:
            if os.path.exists(path):
                print(f"Found gift boxes file at {path}")
                with open(path, 'r') as f:
                    return json.load(f)
        
        # If we get here, no file was found, create an empty one
        print(f"Gift boxes file not found. Creating empty gift boxes list.")
        empty_giftboxes = []
        save_giftboxes(empty_giftboxes)
        return empty_giftboxes
    except Exception as e:
        print(f"Error loading gift boxes: {e}")
        return []

def save_products(products):
    """Save products to JSON file"""
    try:
        # Define products_path using the constant and ensure it has a value
        products_path = PRODUCTS_FILE
        
        # If the path is empty, use a default
        if not products_path:
            products_path = 'products.json'
            print(f"Warning: PRODUCTS_FILE was empty, using default path: {products_path}")
        
        # Resolve the path for better error messages
        resolved_path = os.path.abspath(products_path)
        
        # Check if the directory exists, and create it if it doesn't
        directory = os.path.dirname(resolved_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        
        # Save the products to the JSON file
        with open(resolved_path, 'w') as f:
            json.dump(products, f, indent=4)
        
        print(f"Products saved successfully to {resolved_path}")
        return True
    except Exception as e:
        print(f"Error saving products: {e}")
        return False

def save_giftboxes(giftboxes):
    """Save gift boxes to JSON file"""
    try:
        # Define giftboxes_path using the constant
        giftboxes_path = GIFTBOXES_FILE
        
        # If the path is empty, use a default
        if not giftboxes_path:
            giftboxes_path = 'giftboxes.json'
            print(f"Warning: GIFTBOXES_FILE was empty, using default path: {giftboxes_path}")
        
        # Resolve the path for better error messages
        resolved_path = os.path.abspath(giftboxes_path)
        
        # Check if the directory exists, and create it if it doesn't
        directory = os.path.dirname(resolved_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        
        # Save the giftboxes to the JSON file
        with open(resolved_path, 'w') as f:
            json.dump(giftboxes, f, indent=4)
        
        print(f"Gift boxes saved successfully to {resolved_path}")
        return True
    except Exception as e:
        print(f"Error saving gift boxes: {e}")
        return False

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page"""
    products = get_products()
    active_giftbox = get_active_giftbox()
    now = datetime.datetime.now(YANGON_TZ)
    
    # Get settings to pass to the template
    settings = get_settings()
    
    # Track this visit
    track_visit('home')
    
    return render_template('index.html', 
                          products=products, 
                          active_giftbox=active_giftbox, 
                          now=now,
                          settings=settings)

@app.route('/api/products')
def api_products():
    """API endpoint to get all products"""
    products = get_products()
    # Track this API call
    track_visit('api_products')
    return jsonify(products)

@app.route('/api/products/<int:product_id>')
def api_product(product_id):
    """API endpoint to get a specific product"""
    products = get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    # Track this product view
    track_visit(f'product_{product_id}')
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    form = LoginForm(request.form)
    
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        
        # Get settings to check the admin credentials
        settings = get_settings()
        admin_username = settings['security']['admin_username']
        admin_password = settings['security']['admin_password']
        
        # Simple authentication - in production use a secure method
        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            # Track successful login
            track_visit('admin_login_success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Track failed login
            track_visit('admin_login_failed')
            flash('Invalid credentials', 'danger')
    else:
        # Track login page view
        track_visit('admin_login_page')
    
    # Pass settings to template for consistent branding
    settings = get_settings()
    now = datetime.datetime.now(YANGON_TZ)
    
    return render_template('admin/login.html', form=form, settings=settings, now=now)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard page"""
    products = get_products()
    giftboxes = get_giftboxes()
    now = datetime.datetime.now(YANGON_TZ)
    
    # Get settings to pass to the template
    settings = get_settings()
    
    # Track this visit
    track_visit('admin_dashboard')
    
    return render_template('admin/dashboard.html', 
                          products=products, 
                          giftboxes=giftboxes, 
                          now=now,
                          settings=settings)

@app.route('/admin/product/add', methods=['POST'])
@login_required
def add_product():
    """Add a new product"""
    try:
        products = get_products()
        
        # Generate a new ID
        new_id = max([p['id'] for p in products], default=0) + 1
        
        # Get form data
        product = {
            'id': new_id,
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'thc': request.form.get('thc'),
            'price': request.form.get('price'),
            'status': request.form.get('status'),
            'description': request.form.get('description'),
            'rating': float(request.form.get('rating', 0)),
            'effects': []
        }
        
        # Handle effects
        effects = request.form.get('effects', '')
        if effects:
            effect_list = [e.strip() for e in effects.split(',')]
            product['effects'] = [{'name': e, 'icon': get_effect_icon(e)} for e in effect_list if e]
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create the directory if it doesn't exist
                os.makedirs(os.path.join('static', 'images', 'products'), exist_ok=True)
                # Save the file to the static directory
                file_path = os.path.join('static', 'images', 'products', filename)
                file.save(file_path)
                # Store the path relative to static directory
                product['image'] = os.path.join('images', 'products', filename)
            else:
                product['image'] = 'images/products/default.jpg'
        else:
            product['image'] = 'images/products/default.jpg'
        
        # Track this action
        track_visit(f'add_product_{new_id}')
        
        products.append(product)
        if save_products(products):
            return jsonify({"success": True, "product": product})
        else:
            return jsonify({"success": False, "error": "Failed to save product data"}), 500
            
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/product/edit/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    try:
        products = get_products()
        product_index = next((i for i, p in enumerate(products) if p['id'] == product_id), None)
        
        if product_index is None:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        # Update product fields
        product = products[product_index]
        product['name'] = request.form.get('name', product['name'])
        product['type'] = request.form.get('type', product['type'])
        product['thc'] = request.form.get('thc', product['thc'])
        product['price'] = request.form.get('price', product['price'])
        product['status'] = request.form.get('status', product['status'])
        product['description'] = request.form.get('description', product['description'])
        
        try:
            rating = request.form.get('rating')
            if rating:
                product['rating'] = float(rating)
        except ValueError:
            # If rating is not a valid float, keep the existing value
            pass
        
        # Handle effects
        effects = request.form.get('effects', '')
        if effects:
            effect_list = [e.strip() for e in effects.split(',')]
            product['effects'] = [{'name': e, 'icon': get_effect_icon(e)} for e in effect_list if e]
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create the directory if it doesn't exist
                os.makedirs(os.path.join('static', 'images', 'products'), exist_ok=True)
                # Save the file to the static directory
                file_path = os.path.join('static', 'images', 'products', filename)
                file.save(file_path)
                # Store the path relative to static directory
                product['image'] = os.path.join('images', 'products', filename)
        
        # Track this action
        track_visit(f'edit_product_{product_id}')
        
        products[product_index] = product
        if save_products(products):
            return jsonify({"success": True, "product": product})
        else:
            return jsonify({"success": False, "error": "Failed to save product data"}), 500
            
    except Exception as e:
        print(f"Error editing product: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/get_product/<int:product_id>')
@login_required
def get_product(product_id):
    """Get product data for editing"""
    products = get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if product:
        # Track this view
        track_visit(f'get_product_{product_id}')
        return jsonify(product)
    
    return jsonify({"error": "Product not found"}), 404

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    try:
        products = get_products()
        original_count = len(products)
        products = [p for p in products if p['id'] != product_id]
        
        # Check if any product was actually deleted
        if len(products) == original_count:
            return jsonify({"success": False, "error": "Product not found"}), 404
            
        # Track this action
        track_visit(f'delete_product_{product_id}')
        
        if save_products(products):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to save product data"}), 500
            
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Admin analytics page"""
    products = get_products()
    now = datetime.datetime.now(YANGON_TZ)
    
    # Get settings to pass to the template
    settings = get_settings()
    
    # Get visit data
    visits = get_visits()
    
    # Generate visitor analytics
    last_30_days = []
    today = datetime.datetime.now(YANGON_TZ).date()
    
    # Initialize the last 30 days with zero counts
    for i in range(30):
        day = today - datetime.timedelta(days=i)
        last_30_days.append({
            'date': day.strftime('%Y-%m-%d'),
            'display_date': day.strftime('%b %d'),
            'count': 0
        })
    
    # Count visits for the last 30 days
    unique_visitors = set()
    page_views = {}
    
    for visit in visits:
        try:
            visit_date = datetime.datetime.fromisoformat(visit['timestamp']).date()
            days_ago = (today - visit_date).days
            
            # Count for daily visits chart (last 30 days)
            if days_ago < 30:
                last_30_days[days_ago]['count'] += 1
            
            # Count unique visitors (overall)
            if visit.get('visitor_id'):
                unique_visitors.add(visit['visitor_id'])
            
            # Count page views by route
            route = visit.get('path', 'unknown')
            if route in page_views:
                page_views[route] += 1
            else:
                page_views[route] = 1
                
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error processing visit: {e}")
            continue
    
    # Reverse the days list to show chronological order
    last_30_days.reverse()
    
    # Sort page views by count (descending)
    sorted_page_views = sorted(
        [{'page': k, 'views': v} for k, v in page_views.items()],
        key=lambda x: x['views'],
        reverse=True
    )[:5]  # Top 5 pages
    
    # Prepare analytics data
    analytics = {
        'total_products': len(products),
        'product_types': {
            'sativa': len([p for p in products if p['type'].lower() == 'sativa']),
            'indica': len([p for p in products if p['type'].lower() == 'indica']),
            'hybrid': len([p for p in products if p['type'].lower() == 'hybrid'])
        },
        'availability': {
            'in_stock': len([p for p in products if p['status'] == 'Active']),
            'low_stock': len([p for p in products if p['status'] == 'Low Stock']),
            'out_of_stock': len([p for p in products if p['status'] == 'Out of Stock'])
        },
        'visits': {
            'total': len(visits),
            'unique_visitors': len(unique_visitors),
            'last_30_days': last_30_days,
            'top_pages': sorted_page_views
        }
    }
    
    # Calculate average product rating
    if products:
        avg_rating = sum(float(p.get('rating', 0)) for p in products) / len(products)
        analytics['avg_rating'] = round(avg_rating, 1)
    else:
        analytics['avg_rating'] = 0
    
    return render_template('admin/analytics.html', analytics=analytics, now=now, settings=settings)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin settings page"""
    # Track this visit
    track_visit('admin_settings')
    
    # Load current settings
    current_settings = get_settings()
    
    if request.method == 'POST':
        # Determine which form was submitted based on form fields
        if 'site_name' in request.form:
            # General settings form
            current_settings['general']['site_name'] = request.form.get('site_name', 'Gift of Shiva')
            current_settings['general']['theme_color'] = request.form.get('theme_color', '#16a34a')
            
            # Save settings
            if save_settings(current_settings):
                flash('General settings updated successfully', 'success')
            else:
                flash('Error updating general settings', 'danger')
                
        elif 'contact_email' in request.form:
            # Contact information form
            current_settings['contact']['contact_email'] = request.form.get('contact_email', 'info@giftofshiva.com')
            current_settings['contact']['contact_phone'] = request.form.get('contact_phone', '(555) 123-4567')
            current_settings['contact']['contact_address'] = request.form.get('contact_address', '123 Cannabis Street, WeedTown, 98765')
            
            # Handle telegram username (ensure it starts with @)
            telegram = request.form.get('telegram_username', 'GiftOfShivaOfficial')
            if not telegram.startswith('@'):
                telegram = '@' + telegram
            current_settings['contact']['telegram_username'] = telegram
            
            # Process delivery fees if they're included in the form
            if 'township[]' in request.form:
                townships = request.form.getlist('township[]')
                fees = request.form.getlist('fee[]')
                
                delivery_fees = []
                for i in range(len(townships)):
                    if townships[i].strip() and fees[i].strip():
                        delivery_fees.append({
                            'township': townships[i].strip(),
                            'fee': fees[i].strip()
                        })
                
                current_settings['contact']['delivery_fees'] = delivery_fees
            
            # Save settings
            if save_settings(current_settings):
                flash('Contact information updated successfully', 'success')
            else:
                flash('Error updating contact information', 'danger')
                
        elif 'current_password' in request.form:
            # Security settings form
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate password change
            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required', 'danger')
            elif current_password != current_settings['security']['admin_password']:
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            else:
                # Update password
                current_settings['security']['admin_password'] = new_password
                
                # Save settings
                if save_settings(current_settings):
                    flash('Password updated successfully', 'success')
                else:
                    flash('Error updating password', 'danger')
        
        return redirect(url_for('admin_settings'))
    
    # Prepare settings for the template
    settings = {
        'site_name': current_settings['general']['site_name'],
        'theme_color': current_settings['general'].get('theme_color', '#16a34a'),
        'contact_email': current_settings['contact']['contact_email'],
        'contact_phone': current_settings['contact']['contact_phone'],
        'contact_address': current_settings['contact']['contact_address'],
        'telegram_username': current_settings['contact']['telegram_username'],
        'delivery_fees': current_settings['contact'].get('delivery_fees', [])
    }
    
    now = datetime.datetime.now(YANGON_TZ)
    return render_template('admin/settings.html', settings=settings, now=now)

@app.route('/admin/giftboxes', methods=['GET', 'POST'])
@login_required
def admin_giftboxes():
    """Admin gift boxes management page"""
    # Track this visit
    track_visit('admin_giftboxes')
    
    products = get_products()
    form = GiftBoxForm(request.form)
    settings = get_settings()
    
    # Populate product choices
    product_choices = [(p['id'], p['name']) for p in products]
    form.product_id.choices = product_choices
    
    if request.method == 'POST':
        # Get form data manually to handle datetime properly
        title = request.form.get('title')
        description = request.form.get('description')
        gift_type = request.form.get('gift_type')
        discount_amount = request.form.get('discount_amount')
        product_id = request.form.get('product_id')
        start_time_str = request.form.get('start_time')
        start_date = request.form.get('start_date')
        start_time_input = request.form.get('start_time_input')
        duration_hours = request.form.get('duration_hours')
        
        # Check if we have separate date and time inputs or a combined value
        if start_date and start_time_input and not start_time_str:
            # Combine the separate date and time inputs
            start_time_str = f"{start_date}T{start_time_input}"
        
        # Validate required fields
        if title and description and gift_type and (start_time_str or (start_date and start_time_input)) and duration_hours:
            giftboxes = get_giftboxes()
            
            # Parse start_time
            try:
                # Handle different datetime formats
                if start_time_str and 'T' in start_time_str:
                    # Standard format: 2023-04-15T14:30
                    start_time = datetime.datetime.fromisoformat(start_time_str)
                elif start_time_str and ' ' in start_time_str:
                    # Alternative format: 2023-04-15 14:30
                    start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
                elif start_date and start_time_input:
                    # Separate date and time fields
                    start_time = datetime.datetime.strptime(f"{start_date} {start_time_input}", '%Y-%m-%d %H:%M')
                else:
                    # Date only: 2023-04-15
                    start_time = datetime.datetime.strptime(start_date or start_time_str, '%Y-%m-%d')
                    # Set a default time (noon)
                    start_time = start_time.replace(hour=12, minute=0)
                
                # Make sure it has Yangon timezone
                if start_time.tzinfo is None:
                    start_time = YANGON_TZ.localize(start_time)
                
                # Verify the start time is not in the past
                now = datetime.datetime.now(YANGON_TZ)
                if start_time < now:
                    flash('Start time cannot be in the past. Please choose a future time.', 'danger')
                    return render_template('admin/giftboxes.html', form=form, giftboxes=giftboxes, products=products, datetime=datetime, now=now, settings=settings)
                
            except (ValueError, TypeError) as e:
                flash(f'Invalid start time format: {e}. Please use the date picker.', 'danger')
                return render_template('admin/giftboxes.html', form=form, giftboxes=giftboxes, products=products, datetime=datetime, now=now, settings=settings)
            
            # Create new gift box
            new_giftbox = {
                'id': str(uuid.uuid4()),
                'title': title,
                'description': description,
                'gift_type': gift_type,
                'discount_amount': discount_amount if gift_type == 'discount' else None,
                'product_id': int(product_id) if gift_type in ['free_product', 'bundle'] and product_id else None,
                'start_time': start_time.isoformat(),
                'duration_hours': duration_hours,
                'claimed': False,
                'claimed_by': None,
                'claimed_at': None
            }
            
            giftboxes.append(new_giftbox)
            save_giftboxes(giftboxes)
            
            flash('Gift box created successfully!', 'success')
            return redirect(url_for('admin_giftboxes'))
        else:
            flash('Please fill in all required fields.', 'danger')
    
    # Get all gift boxes for listing
    giftboxes = get_giftboxes()
    now = datetime.datetime.now(YANGON_TZ)
    
    return render_template('admin/giftboxes.html', form=form, giftboxes=giftboxes, products=products, datetime=datetime, now=now, settings=settings)

@app.route('/admin/giftbox/delete/<string:giftbox_id>', methods=['POST'])
@login_required
def delete_giftbox(giftbox_id):
    """Delete a gift box"""
    giftboxes = get_giftboxes()
    giftboxes = [box for box in giftboxes if box['id'] != giftbox_id]
    save_giftboxes(giftboxes)
    
    flash('Gift box deleted successfully!', 'success')
    return redirect(url_for('admin_giftboxes'))

@app.route('/api/claim-giftbox/<string:giftbox_id>', methods=['POST'])
def claim_giftbox(giftbox_id):
    """API endpoint to claim a gift box"""
    # Track this visit
    track_visit(f'claim_giftbox_{giftbox_id}')
    
    giftboxes = get_giftboxes()
    
    # Find the gift box by ID
    for i, box in enumerate(giftboxes):
        if box['id'] == giftbox_id:
            # Check if it's already claimed
            if box['claimed']:
                return jsonify({
                    "success": False,
                    "message": "This gift has already been claimed!"
                })
            
            # Mark as claimed
            giftboxes[i]['claimed'] = True
            giftboxes[i]['claimed_by'] = request.remote_addr  # In a real app, use user ID
            giftboxes[i]['claimed_at'] = datetime.datetime.now(YANGON_TZ).isoformat()
            
            save_giftboxes(giftboxes)
            
            # Return gift details based on type
            if box['gift_type'] == 'discount':
                return jsonify({
                    "success": True,
                    "message": f"Congratulations! You've received a {box['discount_amount']}% discount coupon!",
                    "gift_type": "discount",
                    "discount_code": f"SHIVA{giftbox_id[:8].upper()}",
                    "discount_amount": box['discount_amount']
                })
            elif box['gift_type'] == 'free_product':
                product = next((p for p in get_products() if p['id'] == box['product_id']), None)
                return jsonify({
                    "success": True,
                    "message": f"Congratulations! You've won a free {product['name'] if product else 'product'}!",
                    "gift_type": "free_product",
                    "product": product
                })
            else:  # bundle
                product = next((p for p in get_products() if p['id'] == box['product_id']), None)
                return jsonify({
                    "success": True,
                    "message": f"Congratulations! You've won a special bundle featuring {product['name'] if product else 'product'}!",
                    "gift_type": "bundle",
                    "product": product
                })
    
    return jsonify({"success": False, "message": "Gift not found!"}), 404

@app.route('/api/active-giftbox')
def api_active_giftbox():
    """API endpoint to get currently active gift box"""
    # Track this visit
    track_visit('api_active_giftbox')
    
    active_box = get_active_giftbox()
    if active_box:
        return jsonify({
            "active": True,
            "giftbox": active_box
        })
    else:
        return jsonify({"active": False})

@app.route('/api/analytics/<int:days>')
@login_required
def api_analytics(days):
    """API endpoint to get analytics data for a specific time range"""
    # Validate days parameter
    if days not in [7, 30, 90, 365]:
        days = 30  # Default to 30 days
    
    visits = get_visits()
    today = datetime.datetime.now(YANGON_TZ).date()
    
    # Initialize the specified days with zero counts
    time_range_data = []
    for i in range(days):
        day = today - datetime.timedelta(days=i)
        time_range_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'display_date': day.strftime('%b %d'),
            'count': 0
        })
    
    # Count unique visitors for the time range
    unique_visitors_period = set()
    page_views_period = {}
    total_views_period = 0
    
    for visit in visits:
        try:
            visit_date = datetime.datetime.fromisoformat(visit['timestamp']).date()
            days_ago = (today - visit_date).days
            
            # Count for daily visits chart
            if days_ago < days:
                time_range_data[days_ago]['count'] += 1
                total_views_period += 1
                
                # Count unique visitors for the period
                if visit.get('visitor_id'):
                    unique_visitors_period.add(visit['visitor_id'])
                
                # Count page views by route for the period
                route = visit.get('path', 'unknown')
                if route in page_views_period:
                    page_views_period[route] += 1
                else:
                    page_views_period[route] = 1
                
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error processing visit: {e}")
            continue
    
    # Reverse the days list to show chronological order
    time_range_data.reverse()
    
    # Sort page views by count (descending)
    sorted_page_views = sorted(
        [{'page': k, 'views': v} for k, v in page_views_period.items()],
        key=lambda x: x['views'],
        reverse=True
    )[:5]  # Top 5 pages
    
    return jsonify({
        'time_range': {
            'days': days,
            'data': time_range_data
        },
        'unique_visitors': len(unique_visitors_period),
        'total_views': total_views_period,
        'top_pages': sorted_page_views
    })

def get_effect_icon(effect_name):
    """Helper function to get appropriate icon for effect"""
    effect_icons = {
        'relaxed': 'fas fa-couch',
        'happy': 'fas fa-smile',
        'euphoric': 'fas fa-grin-stars',
        'uplifted': 'fas fa-cloud',
        'creative': 'fas fa-paint-brush',
        'energetic': 'fas fa-bolt',
        'focused': 'fas fa-bullseye',
        'sleepy': 'fas fa-bed',
        'hungry': 'fas fa-utensils',
        'talkative': 'fas fa-comments'
    }
    
    return effect_icons.get(effect_name.lower(), 'fas fa-cannabis')

def get_active_giftbox():
    """Get currently active gift box if any"""
    giftboxes = get_giftboxes()
    now = datetime.datetime.now(YANGON_TZ)
    
    for box in giftboxes:
        start_time = datetime.datetime.fromisoformat(box['start_time'])
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=YANGON_TZ)
        end_time = start_time + datetime.timedelta(hours=int(box['duration_hours']))
        
        if start_time <= now <= end_time and not box['claimed']:
            return box
    
    return None

def get_visits():
    """Load visits from JSON file"""
    try:
        if os.path.exists(app.config['VISITS_FILE']):
            with open(app.config['VISITS_FILE'], 'r') as f:
                return json.load(f)
        else:
            # Return empty list if file doesn't exist
            return []
    except Exception as e:
        print(f"Error loading visits: {e}")
        return []

def save_visits(visits):
    """Save visits to JSON file"""
    try:
        with open(app.config['VISITS_FILE'], 'w') as f:
            json.dump(visits, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving visits: {e}")
        return False

def track_visit(route):
    """Track a page visit"""
    visits = get_visits()
    
    # Generate a visitor ID based on IP + user agent (anonymized with a hash)
    visitor_id = None
    if request.remote_addr and request.user_agent.string:
        # Create a hash of IP address and user agent to anonymize the data but keep it consistent
        visitor_data = f"{request.remote_addr}|{request.user_agent.string}"
        visitor_id = hashlib.md5(visitor_data.encode()).hexdigest()
    
    # Add new visit
    new_visit = {
        'timestamp': datetime.datetime.now(YANGON_TZ).isoformat(),
        'path': route,
        'visitor_id': visitor_id,
        'referrer': request.referrer or 'direct'
    }
    
    visits.append(new_visit)
    
    # Keep only the last 5000 visits to avoid massive files
    if len(visits) > 5000:
        visits = visits[-5000:]
    
    save_visits(visits)
    return new_visit

@app.route('/admin/generate-demo-analytics', methods=['POST'])
@login_required
def generate_demo_analytics():
    """Generate and save demo analytics data for testing"""
    try:
        # Get current date
        now = datetime.datetime.now(YANGON_TZ)
        today = now.date()
        
        # List of routes to generate data for
        routes = ['home', 'product_1', 'product_2', 'admin_dashboard', 'admin_analytics', 
                 'admin_settings', 'admin_giftboxes', 'admin_login_page', 
                 'admin_login_success', 'admin_login_failed', 'api_products']
        
        # Generate visitor IDs
        visitor_ids = [str(uuid.uuid4())[:8] for _ in range(50)]
        
        # Generate demo data
        visits = []
        
        # Generate data for the last 60 days
        for day_offset in range(60, -1, -1):
            # Date for this set of data
            current_date = today - datetime.timedelta(days=day_offset)
            
            # Base number of visits - more recent days have more visits
            base_visits = 10 + int((60 - day_offset) / 5)
            
            # Weekend boost (more traffic on weekends)
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                base_visits = int(base_visits * 1.5)
                
            # Generate visits for this day
            for _ in range(base_visits):
                # Random time during the day
                hour = random.randint(8, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = datetime.datetime(
                    current_date.year, 
                    current_date.month, 
                    current_date.day,
                    hour, minute, second,
                    tzinfo=YANGON_TZ
                )
                
                # Random visitor
                visitor_id = random.choice(visitor_ids)
                
                # Random route
                route = random.choice(routes)
                
                # Add visit
                visits.append({
                    'timestamp': timestamp.isoformat(),
                    'path': route,
                    'visitor_id': visitor_id,
                    'referrer': 'direct'
                })
        
        # Save the demo data
        save_visits(visits)
        
        flash('Demo analytics data generated successfully!', 'success')
        return redirect(url_for('admin_analytics'))
    
    except Exception as e:
        flash(f'Error generating demo data: {str(e)}', 'danger')
        return redirect(url_for('admin_analytics'))

def get_settings():
    """Load settings from JSON file"""
    try:
        # Use a full path to ensure we're looking in the right location
        settings_path = os.path.join(os.path.dirname(__file__), SETTINGS_FILE)
        
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                return json.load(f)
        else:
            # Try alternative locations
            alt_paths = [
                SETTINGS_FILE,
                os.path.join('gos', SETTINGS_FILE)
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    print(f"Found settings file at {path}")
                    with open(path, 'r') as f:
                        return json.load(f)
            
            # If we get here, no file was found, use default settings
            print(f"Settings file not found. Using default settings.")
            default_settings = {
                'general': {
                    'site_name': 'Gift of Shiva',
                    'theme_color': '#16a34a'
                },
                'contact': {
                    'contact_email': 'info@giftofshiva.com',
                    'contact_phone': '(555) 123-4567',
                    'contact_address': '123 Cannabis Street, WeedTown, 98765',
                    'telegram_username': '@GiftOfShivaOfficial',
                    'delivery_fees': [
                        {'township': 'Downtown', 'fee': '$5.00'},
                        {'township': 'North District', 'fee': '$7.50'},
                        {'township': 'East Village', 'fee': '$6.00'},
                        {'township': 'South Side', 'fee': '$8.00'},
                        {'township': 'West End', 'fee': '$7.00'}
                    ]
                },
                'security': {
                    'admin_username': 'admin',
                    'admin_password': 'password'  # In production, this should be hashed
                }
            }
            save_settings(default_settings)
            return default_settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        # Return default settings on error
        return {
            'general': {
                'site_name': 'Gift of Shiva',
                'theme_color': '#16a34a'
            },
            'contact': {
                'contact_email': 'info@giftofshiva.com',
                'contact_phone': '(555) 123-4567',
                'contact_address': '123 Cannabis Street, WeedTown, 98765',
                'telegram_username': '@GiftOfShivaOfficial',
                'delivery_fees': [
                    {'township': 'Downtown', 'fee': '$5.00'},
                    {'township': 'North District', 'fee': '$7.50'},
                    {'township': 'East Village', 'fee': '$6.00'},
                    {'township': 'South Side', 'fee': '$8.00'},
                    {'township': 'West End', 'fee': '$7.00'}
                ]
            },
            'security': {
                'admin_username': 'admin',
                'admin_password': 'password'  # In production, this should be hashed
            }
        }

def save_settings(settings):
    """Save settings to JSON file"""
    try:
        # Define settings_path using the constant
        settings_path = SETTINGS_FILE
        
        # If the path is empty, use a default
        if not settings_path:
            settings_path = 'settings.json'
            print(f"Warning: SETTINGS_FILE was empty, using default path: {settings_path}")
        
        # Resolve the path for better error messages
        resolved_path = os.path.abspath(settings_path)
        
        # Check if the directory exists, and create it if it doesn't
        directory = os.path.dirname(resolved_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        
        # Save the settings to the JSON file
        with open(resolved_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print(f"Settings saved successfully to {resolved_path}")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True) 