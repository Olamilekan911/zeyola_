import requests,json,random,os,secrets
from flask import render_template,request,redirect,flash,session,url_for
from flask_login import login_required, login_user, logout_user, current_user
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
    cus_id = session['cus_loggedin'] 
    if cus_id:
        cus_deets = db.session.query(Customer).get(cus_id)
        cart = db.session.query(Cart).filter_by(cus_id=cus_id).all()
    for item in cart:
        product = db.session.query(Product).filter_by(product_id=item.product_id).first()
        if product:
            cart.append({
                'pro_id': item.product_id,
                'pro_picture': product.pro_picture,
                'cart_id': item.cart_id,
                'product_name': product.pro_name,
                'quantity': item.cart_quantity,
                'new_price': float(product.new_price),
                'total_price': float(item.cart_quantity * product.new_price)
            })
        return render_template('user/cart.html',cus_deets=cus_deets, cart=cart)

    else:
        flash ('errormsg', 'You must be logged in')
        return redirect('/login/')




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
        category = db.session.query(Category).filter_by(category_name="Fashion").first()
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
