import requests,json,random,os,secrets
from flask import render_template,request,redirect,flash,session,url_for,jsonify
from flask_login import login_required, login_user, logout_user, current_user
from flask_wtf.csrf import CSRFProtect,CSRFError
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from pkg import app
from pkg.models import Customer,Product,Cart,State,Lga,db,Payment,Category,Admin
from pkg.forms import LoginForm






@app.route('/')
def home():
    
    cus_id = session.get('cus_loggedin') 
    
    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)


    return render_template('user/index.html', cus_deets=cus_deets)


@app.route('/login/', methods=['GET','POST'])
def user_login():
    loginform = LoginForm()
    if request.method == 'GET':
        return render_template('user/login.html', loginform=loginform)
    else:
        if loginform.validate_on_submit():
            email = loginform.email.data
            password = loginform.password.data

            record = db.session.query(Customer).filter(Customer.email==email).first()
            if record: 
                hashed_password = record.password
                chk = check_password_hash(hashed_password,password)#compare the hashed password with the plain text coming from the form. return true or false
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
            return render_template('user/login.html', loginform=loginform)


@app.route('/register/', methods=['POST', 'GET'])
def user_register():
    if request.method == 'GET':
        return render_template('user/register.html')
    else:
        email = request.form.get('email')
        password = request.form.get('pass')
        cpassword = request.form.get('confirm')
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
    cus_id = session['cus_loggedin'] #it will return the details of the person
    # pform = ProfileForm()
    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        return render_template('user/profile.html',cus_deets=cus_deets)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')
    

@app.route('/cart/', methods=['GET'])
def get_cart():
    cus_id = session.get('cus_loggedin')  # Get customer ID from the session

    if cus_id:
        # Fetch customer details
        cus_deets = db.session.query(Customer).filter(Customer.id == cus_id).first()

        # Fetch cart items for the logged-in customer
        cart_items = []
        cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
        for item in cart:
            product = db.session.query(Product).filter_by(product_id=item.product_id).first()
            if product:
                cart_items.append({
                    'pro_id': item.product_id,
                    'pro_picture': product.pro_picture,
                    'cart_id': item.cart_id,
                    'product_name': product.pro_name,
                    'quantity': item.cart_quantity,
                    'new_price': float(product.new_price),
                    'total_price': float(item.cart_quantity * product.new_price)
                })

        # Render the cart page with customer and cart details
        return render_template('user/cart.html', cus_deets=cus_deets, cart_items=cart_items)
    else:
        flash('errormsg', 'You must be logged in')
        return redirect('/login/')
    



# @app.route('/cart/add/', methods=['GET','POST'])
# def add_to_cart():
#     if 'cus_loggedin' not in session:
#         flash('Please log in to add items to your cart.', 'error')
#         return redirect(url_for('user_login'))

#     # Get data from the form
#     pro_id = request.form.get('pro_id', type=int)
#     quantity = request.form.get('quantity', type=int)

#     # Validate product and quantity
#     if not pro_id or quantity <= 0:
#         flash('Invalid product or quantity!', 'error')
#         return redirect(url_for('home'))

#     cus_id = session['cus_loggedin']

#     # Check if the product exists
#     product = db.session.query(Product).filter_by(prod_id=pro_id).first()
#     if not product:
#         flash('Product not found.', 'error')
#         return redirect(url_for('home'))

#     # Check if the product is already in the cart
#     cart_item = db.session.query(Cart).filter_by(pro_id=pro_id, cus_id=cus_id).first()
#     if cart_item:
#         # Update quantity if already in cart
#         cart_item.cart_quantity = quantity
#         flash('Cart updated successfully!', 'success')
#     else:
#         # Add new product to cart
#         new_cart_item = Cart(pro_id=pro_id, cart_quantity=quantity, cus_id=cus_id)
#         db.session.add(new_cart_item)
#         flash('Item added to cart!', 'success')

#     db.session.commit()
#     return redirect(url_for('get_cart'))

# @app.route('/cart/update/<int:cart_id>/', methods=['POST'])
# def update_cart(cart_id):
#     cus_id = session.get('cus_loggedin')  # Ensure the user is logged in
#     if not cus_id:
#         flash('errormsg', 'You must be logged in to update items in the cart.')
#         return redirect('/login/')

#     quantity = request.form.get('quantity', type=int)
#     if not quantity or quantity <= 0:
#         flash('errormsg', 'Invalid quantity.')
#         return redirect('/cart/')

#     # Find the cart item
#     cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()
#     if not cart_item:
#         flash('errormsg', 'Cart item not found.')
#         return redirect('/cart/')

#     # Update quantity
#     cart_item.cart_quantity = quantity
#     db.session.commit()
#     flash('successmsg', 'Cart updated successfully.')
#     return redirect('/cart/')


# @app.route('/cart/remove/<int:cart_id>/', methods=['POST'])
# def remove_from_cart(cart_id):
#     cus_id = session.get('cus_loggedin')  # Ensure the user is logged in
#     if not cus_id:
#         flash('errormsg', 'You must be logged in to remove items from the cart.')
#         return redirect('/login/')

#     # Find the cart item
#     cart_item = db.session.query(Cart).filter_by(cart_id=cart_id, cus_id=cus_id).first()
#     if not cart_item:
#         flash('errormsg', 'Cart item not found.')
#         return redirect('/cart/')

#     # Remove the cart item
#     db.session.delete(cart_item)
#     db.session.commit()
#     flash('successmsg', 'Item removed from cart.')
#     return redirect('/cart/')







@app.route('/cart/add/', methods=['POST'])
def add_to_cart():
    if 'cus_loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'You need to log in to add items to the cart!'}), 401

    cus_id = session.get('cus_loggedin')
    
    # Parse JSON data from the request
    try:
        data = request.get_json()
        product_id = data.get('product_id', type=int)
        quantity = data.get('quantity', type=int)
    except:
        return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400

    if not product_id or not quantity or quantity <= 0:
        return jsonify({'status': 'error', 'message': 'Invalid product or quantity'}), 400

    product = db.session.query(Product).filter_by(product_id=product_id).first()
    if not product:
        return jsonify({'status': 'error', 'message': 'Product not found'}), 404

    existing_cart_item = db.session.query(Cart).filter_by(product_id=product_id, cus_id=cus_id).first()

    if existing_cart_item:
        existing_cart_item.cart_quantity += quantity
        message = 'Cart updated successfully!'
    else:
        new_cart_item = Cart(
            product_id=product_id,
            cart_quantity=quantity,
            cus_id=cus_id
        )
        db.session.add(new_cart_item)
        message = 'Item added to cart!'

    db.session.commit()
    return jsonify({'status': 'success', 'message': message}), 200





@app.route('/fashion/')
def fashion():
    cus_id = session['cus_loggedin'] #it will return the details of the person

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Fashion").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()
        return render_template('user/fashion.html',cus_deets=cus_deets,products=products)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/supermarket/')
def supermarket():
    cus_id = session['cus_loggedin'] 

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Supermarket").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()

        return render_template('user/supermarket.html', products=products,cus_deets=cus_deets)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')
   


@app.route('/beauty/')
def beauty():
    cus_id = session['cus_loggedin'] #it will return the details of the person

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Fashion").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()
        return render_template('user/beauty.html',cus_deets=cus_deets,products=products)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/appliance/')
def appliance():
    cus_id = session['cus_loggedin'] #it will return the details of the person

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Fashion").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()
        return render_template('user/appliances.html',cus_deets=cus_deets,products=products)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/gadget/')
def gadget():
    cus_id = session['cus_loggedin'] #it will return the details of the person

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Computer & Gadget").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()
        return render_template('user/gadget.html',cus_deets=cus_deets,products=products)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')


@app.route('/phone/')
def phone():
    cus_id = session['cus_loggedin'] #it will return the details of the person

    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        category = db.session.query(Category).filter_by(category_name="Fashion").first()
        products = []
        if category:
            products = db.session.query(Product).filter(Product.pro_category_id == category.category_id).all()
        return render_template('user/phone.html',cus_deets=cus_deets,products=products)
    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')
