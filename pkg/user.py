import requests,json,random,os,secrets,uuid,math
import datetime
from flask import render_template,request,redirect,flash,session,url_for,jsonify
from flask_login import login_required, login_user, logout_user, current_user
from flask_wtf.csrf import CSRFProtect,CSRFError
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from pkg import app
from pkg.models import Customer, Product, Cart, State, Lga, db, Payment, Category, Admin,Order
from pkg.forms import LoginForm,SignUpForm
import random
from sqlalchemy.orm.exc import NoResultFound


@app.route('/')
def home():
    cus_id = session.get('cus_loggedin')
    admin_id = session.get('admin_loggin')

    cus_deets = None
    admin_deets = None
    cart_items = []
    cart_count = 0  
    category_ids = [1, 2, 3, 4, 5, 6]
    categories_products = {}
    categories = {}

    try:
        # Fetch logged-in customer details
        if cus_id:
            cus_deets = db.session.query(Customer).get(cus_id)

            # Fetch cart items from database
            cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
            cart_count = len(cart)

            if cart:  
                product_ids = [item.product_id for item in cart]
                products = db.session.query(Product).filter(Product.product_id.in_(product_ids)).all()
                product_map = {product.product_id: product for product in products}

                for item in cart:
                    product = product_map.get(item.product_id)
                    if product:
                        cart_items.append({
                            'product_id': item.product_id,
                            'cart_id': item.cart_id,
                            'pro_name': product.pro_name,
                            'quantity': item.cart_quantity,
                            'new_price': float(product.new_price),
                            'total_price': float(item.cart_quantity * product.new_price)
                        })

        else:
            # Guest users: Load cart from session
            if 'cart' in session:
                product_ids = [item['product_id'] for item in session['cart']]
                products = db.session.query(Product).filter(Product.product_id.in_(product_ids)).all()
                product_map = {product.product_id: product for product in products}

                for item in session['cart']:
                    product = product_map.get(item['product_id'])
                    if product:
                        cart_items.append({
                            'product_id': item['product_id'],
                            'pro_name': product.pro_name,
                            'quantity': item['quantity'],
                            'new_price': float(product.new_price),
                            'total_price': float(item['quantity'] * product.new_price)
                        })

                cart_count = len(session['cart'])

        # Admin logic
        if admin_id:
            admin_deets = db.session.query(Admin).get(admin_id)

        # Fetch category names and products for each category
        for category_id in category_ids:
            category = db.session.query(Category).get(category_id)
            if category:
                categories[category_id] = category.category_name
                products_in_category = db.session.query(Product).filter_by(pro_category_id=category_id).all()
                categories_products[category_id] = products_in_category

        # Select 5 random products from all categories
        all_products = [product for products in categories_products.values() for product in products]
        random_products = random.sample(all_products, min(len(all_products), 5)) if all_products else []

    except NoResultFound:
        return render_template('error.html', message="An error occurred while fetching data.")
    except Exception as e:
        return render_template('error.html', message=f"Unexpected error: {str(e)}")

    return render_template(
        'user/index.html',
        cus_deets=cus_deets,
        admin_deets=admin_deets,
        cart_items=cart_items,
        cart_count=cart_count,
        categories_products=categories_products,
        categories=categories,
        random_products=random_products
    )



@app.route('/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    
    if request.method == 'GET':
        return render_template('user/login.html', form=form)

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        record = db.session.query(Customer).filter_by(email=email).first()
        
        if record and check_password_hash(record.password, password):  
            session['cus_loggedin'] = record.id
            flash('successmsg', 'Login successful!')

            # Move guest cart to database
            if 'cart' in session:
                for item in session['cart']:
                    existing_cart_item = db.session.query(Cart).filter_by(
                        cus_id=record.id, product_id=item['product_id']
                    ).first()

                    if existing_cart_item:
                        existing_cart_item.cart_quantity += item['quantity']
                    else:
                        new_cart_item = Cart(
                            cus_id=record.id,
                            product_id=item['product_id'],
                            cart_quantity=item['quantity']
                        )
                        db.session.add(new_cart_item)

                db.session.commit()
                session.pop('cart', None)  # Clear session cart after merging

            return redirect('/cart/')  # Redirect to cart after login
        else:
            flash('errormsg', 'Invalid email or password')
            return redirect('/login/')

    return render_template('user/login.html', form=form)




@app.route('/register/', methods=['POST', 'GET'])
def user_register():
    form=SignUpForm()
    if request.method == 'GET':
        return render_template('user/register.html',form=form)
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        address = ""
        if password != cpassword:
            flash('errormsg', 'Password mismatch please try again')
            return redirect('/register/')
        else:
            hashed = generate_password_hash(password)
            b = Customer(fname=fname,lname=lname,address=address,
            password=hashed,email=email)
            db.session.add(b)
            db.session.commit()
            flash('feedback', 'An account has been created for you, please login')
            return redirect(url_for('user_login'))

@app.route('/logout/')
def logout():
    session.pop('cus_loggedin', None)
    return redirect('/')


@app.route('/profile/', methods=['GET', 'POST'])
def profile():
    cus_id = session.get('cus_loggedin') 

    if not cus_id:
        flash('You must be logged in', 'error')  
        return redirect('/login/')  

    # Fetch customer details
    cus_deets = db.session.get(Customer, cus_id)

    if not cus_deets:
        flash('Customer details not found', 'errormsg')
        return redirect('/login/')

    # Fetch cart count
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

    return render_template(
        'user/profile.html', 
        cus_deets=cus_deets,  # Pass customer details
        cart_count=cart_count  # Pass cart count for navbar
    )



@app.route('/profile/update/', methods=['GET', 'POST'])
def update_profile():
    cus_id = session.get('cus_loggedin')  
    if not cus_id:
        flash('You must be logged in to update your profile.', 'error')
        return redirect('/login/')
    
    
    cus_deets = db.session.query(Customer).get(cus_id)
    if not cus_deets:
        flash('Customer not found.', 'error')
        return redirect('/profile/')
    
    if request.method == 'POST':
        
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        address = request.form.get('address')
        
        
        cus_deets.fname = fname
        cus_deets.lname = lname
        cus_deets.email = email
        cus_deets.address = address

        
        db.session.commit()

        flash('Your profile has been updated successfully.', 'success')
        return redirect('/profile/')
    
    
    return render_template('user/update_profile.html', cus_deets=cus_deets)

@app.route('/details/<int:product_id>/', methods=['GET', 'POST'])
def product_details(product_id):
    cus_id = session.get('cus_loggedin')

    # Fetch the product details
    product = db.session.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        flash('Product not found.', 'danger')
        return redirect('/')

    cart_item = None
    cart_count = 0
    cus_deets = None

    if cus_id:
        # Fetch customer details if logged in
        cus_deets = db.session.query(Customer).get(cus_id)
        
        # Fetch cart items from database
        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()
        cart_item = db.session.query(Cart).filter_by(cus_id=cus_id, product_id=product_id).first()
    else:
        # Guest users: Get cart from session
        session_cart = session.get('cart', [])
        for item in session_cart:
            if item['product_id'] == product_id:
                cart_item = item
                break
        cart_count = len(session_cart)

    # Add product to recently viewed (limit to 6)
    recently_viewed = session.get('recently_viewed', [])

    if product_id in recently_viewed:
        recently_viewed.remove(product_id)
    recently_viewed.insert(0, product_id)
    
    session['recently_viewed'] = recently_viewed[:6]  # Store last 6 viewed

    # Fetch product details for recently viewed items
    recently_viewed_products = db.session.query(Product).filter(Product.product_id.in_(recently_viewed)).all()

    # Handle Add to Cart (Increment / Decrement Quantity)
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)

        if 'plus' in request.form:
            if cus_id:
                cart_item = db.session.query(Cart).filter_by(cus_id=cus_id, product_id=product_id).first()
                if cart_item:
                    cart_item.cart_quantity += 1
                    db.session.commit()
                    flash('Item quantity updated successfully!', 'success')
            else:
                session_cart = session.get('cart', [])
                for item in session_cart:
                    if item['product_id'] == product_id:
                        item['quantity'] += 1
                        break
                session['cart'] = session_cart
                session.modified = True
                flash('Item quantity updated successfully!', 'success')

        elif 'minus' in request.form:
            if cus_id:
                cart_item = db.session.query(Cart).filter_by(cus_id=cus_id, product_id=product_id).first()
                if cart_item:
                    cart_item.cart_quantity -= 1
                    db.session.commit()
                    if cart_item.cart_quantity == 0:
                        db.session.delete(cart_item)
                        db.session.commit()
                    flash('Item quantity decreased successfully!', 'success')
            else:
                session_cart = session.get('cart', [])
                for item in session_cart:
                    if item['product_id'] == product_id:
                        item['quantity'] -= 1
                        if item['quantity'] == 0:
                            session_cart.remove(item)
                        break
                session['cart'] = session_cart
                session.modified = True
                flash('Item quantity decreased successfully!', 'success')

        return redirect(f'/details/{product_id}/')

    return render_template(
        'user/details.html',
        product=product,
        cus_deets=cus_deets,
        cart_count=cart_count,
        cart_item=cart_item,
        recently_viewed_products=recently_viewed_products  # Pass recently viewed
    )


@app.route('/cart/add/', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)

    if not product_id:
        flash('Invalid product ID!', 'error')
        return redirect(request.referrer or '/')

    cus_id = session.get('cus_loggedin')

    if cus_id:
        # Logged-in user: Add to database
        cart_item = db.session.query(Cart).filter_by(cus_id=cus_id, product_id=product_id).first()

        if cart_item:
            flash('Item is already in your cart!', 'info')
        else:
            new_cart_item = Cart(cus_id=cus_id, product_id=product_id, cart_quantity=1)
            db.session.add(new_cart_item)
            db.session.commit()
            flash('Item added to cart successfully!', 'success')

    else:
        # Guest user: Add to session storage
        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']

        # Check if item already exists in the cart
        for item in cart:
            if item['product_id'] == product_id:
                flash('Item is already in your cart!', 'info')
                return redirect(request.referrer or '/')

        # Add new item to cart session
        cart.append({'product_id': product_id, 'quantity': 1})
        session['cart'] = cart  # Save cart back to session
        flash('Item added to cart successfully!', 'success')

    return redirect(request.referrer or '/')


@app.route('/cart/', methods=['GET'])
def get_cart():
    cus_id = session.get('cus_loggedin')  
    cart_items = []
    total_price = 0
    cus_deets = None

    if cus_id:
        cus_deets = db.session.query(Customer).filter_by(id=cus_id).first()
        cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
        print("Cart items fetched from DB:", cart)  # Debugging
    else:
        cart = session.get('cart', [])
        if not isinstance(cart, list):
            session['cart'] = []
            cart = []
        print("Cart items fetched from session:", cart)  # Debugging

    cart_count = len(cart)

    for item in cart:
        if cus_id:
            product = db.session.query(Product).filter_by(product_id=item.product_id).first()
            quantity = item.cart_quantity
        else:
            product = db.session.query(Product).filter_by(product_id=item['product_id']).first()
            quantity = item['quantity']

        if product:
            item_total_price = quantity * product.new_price
            total_price += item_total_price
            cart_items.append({
                'pro_id': product.product_id,
                'pro_picture': product.pro_picture,
                'cart_id': item.cart_id if cus_id else None,
                'product_name': product.pro_name,
                'quantity': quantity,
                'new_price': float(product.new_price),
                'total_price': float(item_total_price),
            })

    if request.is_json:
        return jsonify({
            'success': True,
            'cart_count': cart_count,
            'cart_items': cart_items,
            'total_price': float(total_price)
        })

    return render_template(
        'user/cart.html',
        cart_items=cart_items,
        total_price=float(total_price),
        cart_count=cart_count,
        cus_deets=cus_deets
    )




@app.route('/cart/plus/', methods=['POST'])
def plus_cart():
    cart_id = request.form.get('cart_id', type=int)
    product_id = request.form.get('product_id', type=int)
    cus_id = session.get('cus_loggedin')

    if cus_id:
        # Logged-in user: Update cart in database
        cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()
        if cart_item:
            cart_item.cart_quantity += 1
            db.session.commit()
            flash('Item quantity updated successfully!', 'success')
    else:
        # Guest user: Update cart in session
        if 'cart' in session:
            for item in session['cart']:
                if item['product_id'] == product_id:
                    item['quantity'] += 1
                    session.modified = True
                    flash('Item quantity updated!', 'success')
                    break

    return redirect('/cart/')
 

@app.route('/cart/minus/', methods=['POST'])
def minus_cart():
    cart_id = request.form.get('cart_id', type=int)
    product_id = request.form.get('product_id', type=int)
    cus_id = session.get('cus_loggedin')

    if cus_id:
        # Logged-in user: Update cart in database
        cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()
        if cart_item:
            cart_item.cart_quantity -= 1
            if cart_item.cart_quantity == 0:
                db.session.delete(cart_item)
            db.session.commit()
            flash('Item quantity updated!', 'success')
    else:
        # Guest user: Update cart in session
        if 'cart' in session:
            for item in session['cart']:
                if item['product_id'] == product_id:
                    item['quantity'] -= 1
                    if item['quantity'] == 0:
                        session['cart'].remove(item)
                    session.modified = True
                    flash('Item quantity updated!', 'success')
                    break

    return redirect('/cart/')



@app.route('/cart/remove/', methods=['POST'])
def remove_cart():
    cart_id = request.form.get('cart_id', type=int)
    product_id = request.form.get('product_id', type=int)
    cus_id = session.get('cus_loggedin')

    if cus_id:
        # Logged-in user: Remove item from database
        cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart!', 'success')
    else:
        # Guest user: Remove item from session
        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
            session.modified = True
            flash('Item removed from cart!', 'success')

    return redirect('/cart/')


 



@app.route('/search/', methods=['GET'])
def search():
    query = request.args.get('query')  
    if not query:
        flash('Please enter a search term.', 'warning')  
        return redirect('/')

    # Get logged-in user details for navbar
    cus_id = session.get('cus_loggedin')
    cus_deets = None
    cart_count = 0

    if cus_id:
        cus_deets = db.session.query(Customer).filter_by(id=cus_id).first()
        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

    # Perform case-insensitive search using LIKE on product name and category
    results = db.session.query(Product).filter(
        (func.lower(Product.pro_name).like(f"%{query.lower()}%")) |
        (func.lower(Product.category).like(f"%{query.lower()}%"))
    ).all()

    # If no results found, show a message
    if not results:
        flash('No results found for your search.', 'warning')

    return render_template(
        'user/search_result.html', 
        query=query, 
        results=results,
        cus_deets=cus_deets,  # Pass customer details for navbar
        cart_count=cart_count  # Pass cart count for navbar
    )



@app.route('/checkout/', methods=['GET', 'POST'])
def checkout():
    # Step 1: Ensure user is logged in
    if 'cus_loggedin' not in session or not session.get('cus_loggedin'):
        flash('You need to log in to proceed with checkout!', 'error')
        return redirect('/login/')

    cus_id = session['cus_loggedin']

    # Step 2: Transfer guest cart items to user database cart
    if 'cart' in session:
        guest_cart = session['cart']
        for item in guest_cart:
            existing_cart_item = db.session.query(Cart).filter_by(
                cus_id=cus_id, product_id=item['product_id']
            ).first()

            if existing_cart_item:
                existing_cart_item.cart_quantity += item['quantity']
            else:
                new_cart_item = Cart(
                    cus_id=cus_id,
                    product_id=item['product_id'],
                    cart_quantity=item['quantity']
                )
                db.session.add(new_cart_item)

        db.session.commit()
        session.pop('cart', None)  # Clear session cart after merging

    # Step 3: Fetch updated cart from DB
    cart_items = db.session.query(Cart).filter_by(cus_id=cus_id).all()
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect('/cart/')

    # Step 4: Handle checkout process
    if request.method == "GET":
        ref_no = session.get('refno')
        existing_order = db.session.query(Order).filter_by(order_reference=ref_no, cus_id=cus_id).first() if ref_no else None

        if not existing_order:
            flash('No existing order found. Redirecting to cart.', 'error')
            return redirect('/cart/')

        session['refno'] = existing_order.order_reference
        return redirect('/pay/')

    try:
        total_price = 0
        ref_no = str(random.randint(1000000000, 9999999999))

        for item in cart_items:
            product = db.session.query(Product).filter_by(product_id=item.product_id).first()
            if not product:
                flash(f"Product with ID {item.product_id} no longer exists.", "error")
                return redirect('/cart/')

            item_price = item.cart_quantity * product.new_price
            total_price += item_price

            order = Order(
                cus_id=cus_id,
                product_id=item.product_id,
                order_quantity=item.cart_quantity,
                order_price=item_price,
                order_status='Pending',
                payment_id='',
                order_reference=ref_no
            )
            db.session.add(order)

        db.session.commit()

        session['refno'] = ref_no
        flash('Order placed successfully!', 'success')
        return redirect('/pay/')

    except Exception as e:
        db.session.rollback()
        flash(f"Error during checkout: {str(e)}", 'error')
        return redirect('/cart/')



@app.route('/pay/', methods=['GET', 'POST'])
def payment():
    cus_id = session.get('cus_loggedin')
    ref_no = session.get('refno')  

    if not cus_id:
        flash('You need to log in to proceed with payment!', 'error')
        return redirect('/login/')

    if not ref_no:
        flash('Invalid transaction. Please start your transaction again.', 'error')
        return redirect('/')

    # Fetch customer and cart items
    customer = db.session.query(Customer).get(cus_id)
    cart_items = db.session.query(Cart).filter_by(cus_id=cus_id).all()

    if not cart_items:
        flash('Your cart is empty. Add items to proceed.', 'error')
        return redirect('/')

    # Calculate totals
    total_quantity = sum(item.cart_quantity for item in cart_items)
    total_price = sum(item.cart_quantity * item.product.new_price for item in cart_items)

    # Check or create orders associated with the reference number
    existing_orders = db.session.query(Order).filter_by(order_reference=ref_no).all()
    if not existing_orders:
        for item in cart_items:
            new_order = Order(
                order_quantity=item.cart_quantity,
                order_price=item.cart_quantity * item.product.new_price,
                order_status='pending',
                payment_id=None,
                order_reference=ref_no,
                cus_id=cus_id,
                product_id=item.product_id,
            )
            db.session.add(new_order)
        db.session.commit()
        existing_orders = db.session.query(Order).filter_by(order_reference=ref_no).all()

    if request.method == 'GET':
        return render_template(
            'user/pay.html',
            cus_deets=customer,
            cart_items=cart_items,
            total_quantity=total_quantity,
            total_price=total_price,
            trxdeets=existing_orders  # Pass all orders for the transaction
        )

    # Initialize payment via Paystack
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk_test_d00b0a56e63f787fedd0ec02d6bf4a5014f5ec11"
    }
    amt_kobo = int(total_price * 100)

    data = {
        "reference": ref_no,
        "amount": amt_kobo,
        "email": customer.email,
        "callback_url": "http://127.0.0.1:5000/payment_validate"
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_data = response.json()

    if response_data.get('status'):
        # Update payment ID for all orders tied to the reference number
        payment_id = response_data['data']['reference']
        for order in existing_orders:
            order.payment_id = payment_id
        db.session.commit()

        # Redirect to authorization URL
        auth_url = response_data['data']['authorization_url']
        return redirect(auth_url)

    # Flash error if payment initialization fails
    flash(f"Payment initialization failed: {response_data.get('message', 'Unknown error')}", 'error')
    return redirect('/')


@app.route('/payment_validate', methods=['GET'])
def payment_validate():
    ref_no = request.args.get('reference')  # Get the reference number from the URL
    cus_id = session.get('cus_loggedin')  # Get the logged-in customer ID

    # Ensure customer is logged in
    if not cus_id:
        flash('You need to log in to proceed.', 'error')
        return redirect('/login/')

    # Fetch all orders linked to the reference number and customer
    orders = db.session.query(Order).filter_by(order_reference=ref_no, cus_id=cus_id).all()

    if not orders:
        flash('No orders found for validation.', 'error')
        return redirect('/')

    # Verify payment with Paystack
    url = f"https://api.paystack.co/transaction/verify/{ref_no}"
    headers = {
        "Authorization": "Bearer sk_test_d00b0a56e63f787fedd0ec02d6bf4a5014f5ec11"  
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()

    # Check if payment is successful
    if response_data.get('status') and response_data['data']['status'] == 'success':
        # Extract payment details
        payment_id = response_data['data']['reference']
        payment_amount = response_data['data']['amount'] / 100  
        payment_status = response_data['data']['status']

        # Create a Payment record
        for order in orders:
            payment = Payment(
                payment_order_id=order.order_id,
                payment_custid=cus_id,
                payment_ref=payment_id,
                payment_amt=order.order_price,
                payment_status=payment_status,
                payment_data=json.dumps(response_data['data'])
            )
            db.session.add(payment)

            # Update the order status to 'Completed'
            order.order_status = 'Completed'

        db.session.commit()

        # Clear the customer's cart after successful payment
        db.session.query(Cart).filter_by(cus_id=cus_id).delete()
        db.session.commit()

        flash('Payment successful! Your orders have been placed.', 'success')
        return redirect('/')

    # If payment failed, update the status of all linked orders to 'Failed'
    for order in orders:
        order.order_status = 'Failed'
    db.session.commit()

    flash('Payment failed. Please try again.', 'error')
    return redirect('/cart/')


@app.route('/orders/', methods=['GET'])
def view_orders():
    try:
        # Check if customer is logged in
        cus_id = session.get('cus_loggedin')
        if not cus_id:
            flash('You need to log in to view your orders!', 'error')
            return redirect('/login/')

        # Fetch customer details (to be used in navbar)
        cus_deets = db.session.query(Customer).filter_by(id=cus_id).first()

        # Pagination setup
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page

        # Get total completed orders count
        total_orders = Order.query.filter_by(cus_id=cus_id, order_status='Completed').count()

        # Get paginated completed orders
        orders = (
            Order.query.filter_by(cus_id=cus_id, order_status='Completed')
            .order_by(Order.order_id.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Get cart count for navbar
        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

        # Calculate total pages for pagination
        total_pages = (total_orders + per_page - 1) // per_page

        return render_template(
            'user/orders.html',
            orders=orders,
            total_orders=total_orders,
            per_page=per_page,
            current_page=page,
            total_pages=total_pages,
            cus_deets=cus_deets,  # Pass customer details to template
            cart_count=cart_count  # Pass cart count for navbar
        )

    except Exception as e:
        app.logger.error(f"Error fetching orders: {e}")
        flash('An error occurred while fetching your orders. Please try again later.', 'error')
        return redirect('/')

        
@app.route('/fashion/')
def fashion():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Fashion").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/fashion.html', products=products, cart_count=cart_count)

@app.route('/supermarket/')
def supermarket():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Supermarket").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/supermarket.html', products=products, cart_count=cart_count)


@app.route('/beauty/')
def beauty():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Beauty").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/beauty.html', products=products, cart_count=cart_count)


@app.route('/appliance/')
def appliance():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Electronic & Appliance").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/appliance.html', products=products, cart_count=cart_count)

@app.route('/gadget/')
def gadget():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Computer & Gadget").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/gadget.html', products=products, cart_count=cart_count)


@app.route('/phone/')
def phone():
    
    cus_id = session.get('cus_loggedin')  

    
    category = db.session.query(Category).filter_by(category_name="Phones & Tablet").first()
    products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all() if category else []

    # Cart count (support guest users)
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count() if cus_id else len(session.get('cart', []))

    return render_template('user/phone.html', products=products, cart_count=cart_count)

@app.route('/sent/')
def sent():

    return render_template('user/sent.html')
@app.route('/se/')
def se():

    return render_template('user/se.html')
