import requests,json,random,os,secrets,uuid
import datetime
from flask import render_template,request,redirect,flash,session,url_for,jsonify
from flask_login import login_required, login_user, logout_user, current_user
from flask_wtf.csrf import CSRFProtect,CSRFError
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from pkg import app
from pkg.models import Customer, Product, Cart, State, Lga, db, Payment, Category, Admin,Order
from pkg.forms import LoginForm,SignUpForm
import random


import random

@app.route('/')
def home():
    cus_id = session.get('cus_loggedin')
    admin_id = session.get('admin_loggin')

    cus_deets = None
    admin_deets = None
    cart_items = []
    cart_count = 0  # Initialize cart count

    # Categories list (adjust this to match your category IDs or names)
    category_ids = [1, 2, 3, 4, 5, 6]  # Example: category IDs for 6 categories
    categories_products = {}
    categories = {}  # Dictionary to hold category names

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

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

    if admin_id:
        admin_deets = db.session.query(Admin).get(admin_id)

    # Fetch products from each category and category names
    for category_id in category_ids:
        # Fetch category name (assuming you have a `Category` table with `category_name`)
        category = db.session.query(Category).get(category_id)  # Get the category name from the Category table
        if category:
            categories[category_id] = category.category_name  # Assuming the category name is in `name`
        
        products_in_category = db.session.query(Product).filter_by(pro_category_id=category_id).all()
        categories_products[category_id] = products_in_category

    # Flatten the products into one list and limit to 5 random items
    all_products = []
    for products in categories_products.values():
        all_products.extend(products)

    # Limit the products to 5 random items
    random_products = random.sample(all_products, min(len(all_products), 5))

    return render_template(
        'user/index.html',
        cus_deets=cus_deets,
        admin_deets=admin_deets,
        cart_items=cart_items,
        cart_count=cart_count,
        categories_products=categories_products,
        categories=categories,  # Pass categories to the template
        random_products=random_products  # Pass the limited random products
    )


@app.route('/login/', methods=['GET','POST'])
def user_login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('user/login.html', form=form)
    else:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            record = db.session.query(Customer).filter(Customer.email==email).first()
            if record: 
                hashed_password = record.password
                chk = check_password_hash(hashed_password,password)
                if chk:
                    session['cus_loggedin'] = record.id
                    return redirect('/')
                else:
                    flash('errormsg', 'Invalid Password')
                    return redirect ('/login/')
            else:
                flash('errormsg', 'Invalid Email')
                return 'Invalid Email'
        else:
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
    flash('feedback', 'You have logged out..')
    return redirect('/login/')


@app.route('/profile/', methods=['GET','POST'])
def profile():
    cus_id = session['cus_loggedin'] 
    
    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        return render_template('user/profile.html',cus_deets=cus_deets)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')

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

@app.route('/details/<int:product_id>/')
def product_details(product_id):
    cus_id = session.get('cus_loggedin')
    product = db.session.query(Product).filter(Product.product_id==product_id).first()
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()
    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        
        if not product:
            flash('errormsg', 'Product not found')
            return redirect('/')
        return render_template('user/details.html', product=product, cus_deets=cus_deets,cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')

@app.route('/cart/add/', methods=['POST'])
def add_to_cart():
    cus_id = session.get('cus_loggedin')
    if not cus_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    product_id = data.get("product_id")

    if not product_id:
        return jsonify({"error": "Product ID is missing"}), 400

    
    product = db.session.query(Product).filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"error": "Product does not exist"}), 404

    
    cart_item = db.session.query(Cart).filter_by(cus_id=cus_id, product_id=product_id).first()
    if cart_item:
        cart_item.cart_quantity += 1
    else:
    
        new_cart_item = Cart(cus_id=cus_id, product_id=product_id, cart_quantity=1)
        db.session.add(new_cart_item)

    db.session.commit()

    
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

    return jsonify({"message": "Product added to cart", "cart_count": cart_count})


@app.route('/cart/', methods=['GET'])
def get_cart():
    cus_id = session.get('cus_loggedin')  
    if not cus_id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'You must be logged in to view your cart.'}), 401
        flash('You must be logged in to view your cart.', 'error')
        return redirect('/login/')

    cus_deets = db.session.query(Customer).filter(Customer.id == cus_id).first()
    cart_items = []
    total_price = 0
    cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
    cart_count = len(cart)

    for item in cart:
        product = db.session.query(Product).filter_by(product_id=item.product_id).first()
        if product:
            item_total_price = item.cart_quantity * product.new_price
            total_price += item_total_price
            cart_items.append({
                'pro_id': item.product_id,
                'pro_picture': product.pro_picture,
                'cart_id': item.cart_id,
                'product_name': product.pro_name,
                'quantity': item.cart_quantity,
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
        cus_deets=cus_deets,
        cart_items=cart_items,
        total_price=float(total_price),
        cart_count=cart_count
    )

@app.route('/cart/plus/', methods=['POST'])
def plus_cart():
    if 'cus_loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'You need to log in to update your cart!'}), 401

    cus_id = session.get('cus_loggedin')
    cart_id = request.form.get('cart_id', type=int)
    cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()

    if cart_item:
        cart_item.cart_quantity += 1  
        db.session.commit()
        flash('Item quantity updated successfully!', 'success')
    else:
        flash('Cart item not found.', 'error')

    return redirect('/cart/')  

@app.route('/cart/minus/', methods=['POST'])
def minus_cart():
    if 'cus_loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'You need to log in to update your cart!'}), 401

    cus_id = session.get('cus_loggedin')
    cart_id = request.form.get('cart_id', type=int)
    cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()

    if cart_item:
        cart_item.cart_quantity -= 1  
        db.session.commit()
        flash('Item quantity decreased successfully!', 'success')

        if cart_item.cart_quantity == 0:
            db.session.delete(cart_item)
            db.session.commit()
        
    else:
        flash('Cart item not found.', 'error')

    return redirect('/cart/')  

@app.route('/cart/remove/', methods=['POST'])
def remove_cart():
    if 'cus_loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'You need to log in to update your cart!'}), 401

    cus_id = session.get('cus_loggedin')
    cart_id = request.form.get('cart_id', type=int)
    cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()

    if cart_item:
        db.session.delete(cart_item)  
        db.session.commit()
        flash('Item removed from cart!', 'success')
    else:
        flash('Cart item not found.', 'error')

    return redirect('/cart/')  

 



@app.route('/search/', methods=['GET'])
def search():
   
    query = request.args.get('query')  
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect('/')

    
    results = db.session.query(Product).filter(
        (func.lower(Product.pro_name).like(f"%{query.lower()}%")) | 
        (func.lower(Product.category).like(f"%{query.lower()}%"))
    ).all()

    return render_template('user/search_result.html', query=query, results=results)


@app.route('/checkout/', methods=['GET', 'POST'])
def checkout():
    
    if 'cus_loggedin' not in session or not session.get('cus_loggedin'):
        flash('You need to log in to proceed with checkout!', 'error')
        return redirect('/login/')

    cus_id = session['cus_loggedin']

    
    cart_items = db.session.query(Cart).filter_by(cus_id=cus_id).all()
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect('/cart/')

    if request.method == "GET":
        
        ref_no = session.get('refno')
        existing_order = None
        if ref_no:
            existing_order = db.session.query(Order).filter_by(order_reference=ref_no, cus_id=cus_id).first()

        
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
    ref_no = request.args.get('reference')  
    cus_id = session.get('cus_loggedin')  

    if not cus_id:
        flash('You need to log in to proceed.', 'error')
        return redirect('/login/')

    
    order = db.session.query(Order).filter_by(order_reference=ref_no, cus_id=cus_id).first()

    if not order:
        flash('Order not found for validation.', 'error')
        return redirect('/')

    
    url = f"https://api.paystack.co/transaction/verify/{ref_no}"
    headers = {
        "Authorization": "Bearer sk_test_d00b0a56e63f787fedd0ec02d6bf4a5014f5ec11"  
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()

    if response_data.get('status') and response_data['data']['status'] == 'success':
    
        payment = Payment(
            payment_order_id=order.order_id,
            payment_custid=cus_id,
            payment_ref=ref_no,
            payment_amt=order.order_price,
            payment_status='paid',
            payment_data=json.dumps(response_data['data'])
        )
        db.session.add(payment)

        order.order_status = 'Completed'
        db.session.commit()

        
        db.session.query(Cart).filter_by(cus_id=cus_id).delete()
        db.session.commit()

        flash('Payment successful! Your order has been placed.', 'success')
        return redirect('/') 


    order.order_status = 'Failed'
    db.session.commit()

    flash('Payment failed. Please try again.', 'error')
    return redirect('/cart/')


@app.route('/orders/', methods=['GET'])
def view_orders():
    
    cus_id = session.get('cus_loggedin')
    if not cus_id:
        flash('You need to log in to view your orders!', 'error')
        return redirect('/login/')

    
    orders = db.session.query(Order).filter_by(cus_id=cus_id).all()


    if not orders:
        flash('You have no orders yet.', 'info')
        return redirect('/') 

    
    return render_template('user/orders.html', orders=orders)


        
@app.route('/fashion/')
def fashion():
    cus_id = session.get('cus_loggedin')  

    if not cus_id:
        flash('You must be logged in to view this page', 'error')
        return redirect('/login/')

    
    cus_deets = db.session.query(Customer).get(cus_id)

    
    category = db.session.query(Category).filter_by(category_name="Fashion").first()
    products = []
    if category:
        products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

    
    cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

    
    return render_template('user/fashion.html', cus_deets=cus_deets, products=products, cart_count=cart_count)


@app.route('/supermarket/')
def supermarket():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Supermarket").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

        return render_template('user/supermarket.html', products=products,cus_deets=cus_deets, cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')
   


@app.route('/beauty/')
def beauty():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Beauty").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()

        return render_template('user/beauty.html',cus_deets=cus_deets,products=products,cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/appliance/')
def appliance():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Electronic & Appliance").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()
        return render_template('user/appliances.html',cus_deets=cus_deets,products=products, cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/gadget/')
def gadget():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Computer & Gadget").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()
        return render_template('user/gadget.html',cus_deets=cus_deets,products=products,cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/phone/')
def phone():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Phones & Tablet").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        cart_count = db.session.query(Cart).filter_by(cus_id=cus_id).count()
        return render_template('user/phone.html',cus_deets=cus_deets,products=products, cart_count=cart_count)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


