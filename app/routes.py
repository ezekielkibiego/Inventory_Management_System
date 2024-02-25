from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from app.models import Inventory, Category, User, db
from flask import request, jsonify
import pdfkit
from sqlalchemy import func
from io import BytesIO
import plotly.graph_objs as go

bp = Blueprint('main', __name__)


@bp.route('/search')
def search_inventory():
    search_query = request.args.get('query')
    sort_option = request.args.get('sort')

    # Query database based on search query and sort option
    query = Inventory.query

    if search_query:
        query = query.filter(
            Inventory.name.ilike(f'%{search_query}%') |
            Inventory.description.ilike(f'%{search_query}%')
        )

    if sort_option:
        if sort_option == 'name':
            query = query.order_by(Inventory.name)
        elif sort_option == 'quantity':
            query = query.order_by(Inventory.quantity)
        elif sort_option == 'price':
            query = query.order_by(Inventory.price)
        elif sort_option == 'date_added':
            query = query.order_by(Inventory.date_added)
        else:
            # Handle invalid sort options
            return render_template('error.html', message='Invalid sort option'), 400

    # Execute the query and retrieve the results
    inventory_items = query.all()

    # Render the template with the search results
    return render_template('search_results.html', inventory_items=inventory_items)

@bp.route('/')
def index():
    inventory_items = Inventory.query.all()
    return render_template('index.html', inventory_items=inventory_items)

@bp.route('/add', methods=['GET', 'POST'])
def add_item():
    categories = Category.query.all()

    if request.method == 'POST':
        try:
            # Retrieve form data
            name = request.form['name']
            quantity = int(request.form['quantity'])
            price = float(request.form['price']) if request.form.get('price') else None
            description = request.form.get('description')
            image_url = request.form.get('image_url')
            category_id = int(request.form['category_id']) if request.form.get('category_id') else None
            supplier = request.form.get('supplier')

            # Create and add item to the database
            item = Inventory(name=name, quantity=quantity, price=price, description=description,
                             image_url=image_url, category_id=category_id, supplier=supplier)
            db.session.add(item)
            db.session.commit()

            # Redirect with success message
            flash('Item added successfully!', 'success')
            return redirect('/')
        except Exception as e:
            # Handle any exceptions or errors during form data retrieval or item creation
            db.session.rollback()
            error_message = str(e) if str(e) != '' else 'An error occurred while adding the item.'
            flash(error_message, 'error')
            return redirect(url_for('main.add_item'))

    # If the request method is GET, render the add_item.html template
    return render_template('add_item.html', categories=categories)

@bp.route('/update/<int:id>', methods=['POST', 'GET'])
def update_item(id):
    item = Inventory.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == 'POST':
        try:
            # Update item fields
            item.name = request.form['name']
            item.quantity = int(request.form['quantity'])
            item.price = float(request.form['price']) if request.form.get('price') else None
            item.description = request.form.get('description')
            item.image_url = request.form.get('image_url')
            item.category_id = int(request.form['category_id']) if request.form.get('category_id') else None
            item.supplier = request.form.get('supplier')
            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            error_message = str(e) if str(e) != '' else 'An error occurred while updating the item.'
            flash(error_message, 'error')
            return redirect(url_for('main.update_item', id=id))
    else:
        return render_template('update_item.html', item=item, categories=categories)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect('/')

@bp.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@bp.route('/categories/add', methods=['POST'])
def add_category():
    name = request.form['name']
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return redirect(url_for('main.categories'))

@bp.route('/categories/update/<int:id>', methods=['POST'])
def update_category(id):
    category = Category.query.get_or_404(id)
    category.name = request.form['name']
    db.session.commit()
    return redirect(url_for('main.categories'))

@bp.route('/categories/delete/<int:id>')
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('main.categories'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error='Invalid username/email or password')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('register.html', error='Username or email already exists')

        # Create new user
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.login'))

    return render_template('register.html')

# Middleware to check if user is logged in
@bp.before_request
def require_login():
    if 'user_id' not in session and request.endpoint not in ['main.login', 'main.register']:
        return redirect(url_for('main.login'))


def calculate_inventory_value():
    total_value = db.session.query(db.func.sum(Inventory.quantity * Inventory.price)).scalar()
    return total_value

# Function to generate sales trends (dummy implementation)
def get_sales_trends():
    # Dummy implementation, replace with actual logic based on your sales data
    return [('January', 1000), ('February', 1500), ('March', 2000)]


def query_inventory_data():
    # Query inventory data from the database
    inventory_data = Inventory.query.all()
    return inventory_data

# Function to prepare data for plotting
def prepare_data(inventory_data):
    # Extract relevant data from inventory records
    dates = [item.date_added for item in inventory_data]
    quantities = [item.quantity for item in inventory_data]
    prices = [item.price for item in inventory_data]

    return dates, quantities, prices

# Route to render the inventory chart
@bp.route('/inventory_chart')
def inventory_chart():
    # Query inventory data from the database
    inventory_items = Inventory.query.all()
    inventory_value = calculate_inventory_value()

    # Prepare data for the chart
    chart_data = {
        'data': [
            {'x': [item.date_added.strftime('%Y-%m-%d') for item in inventory_items], 'y': [item.quantity for item in inventory_items], 'type': 'bar', 'name': 'Quantity'},
            {'x': [item.date_added.strftime('%Y-%m-%d') for item in inventory_items], 'y': [item.price for item in inventory_items], 'type': 'line', 'name': 'Price'}
        ],
        'layout': {
            'title': 'Inventory Data',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Quantity/Price'}
        }
    }

    # Render the template and pass the chart data
    return render_template('inventory_chart.html', chart_json=chart_data,  inventory_value=inventory_value)

    
from app import app
app.register_blueprint(bp)