from flask import render_template, redirect, flash, session, request, url_for
from werkzeug.security import check_password_hash,generate_password_hash
from pkg import app
from pkg.models import db, Customer, Admin, Category, Product,Cart
from pkg.forms import AddProductForm,AdminForm
from werkzeug.utils import secure_filename
import os



@app.route('/adminlog/', methods=['GET', 'POST'])
def admin_login():
    form = AdminForm()
    
    if form.validate_on_submit():  # Check if the form submission is valid
        email = form.email.data  # Get email from form
        password = form.password.data  # Get password from form

        # Query the Admin table for the entered email
        admin = db.session.query(Admin).filter_by(email=email).first()

        if admin:  # If an admin record exists with the given email
            # Compare the hashed password from the database with the submitted password
            if admin.password:
                # Store admin ID in the session
                session['admin_loggedin'] = admin.id
                flash("Welcome back, admin!", "success")
                return redirect(url_for('admin_page'))
            else:
                # Password is incorrect
                flash("Invalid password. Please try again.", "error")
        else:
            # Email not found
            flash("No account found with that email.", "error")
        
        # Redirect back to login if authentication fails
        return redirect(url_for('admin_login'))

    # Render the login page for GET requests or form validation failure
    return render_template('admin/admin_login.html', form=form)


@app.route('/admin-home/')
def admin_page():
    admin_id = session.get("admin_loggedin")
    
    if not admin_id:
        flash("errors", "Please log in to access the dashboard.")
        return redirect(url_for('admin_login'))

    admin = db.session.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        flash("errors","Invalid session. Please log in again.", )
        return redirect(url_for('admin_login'))


    admin = f"{admin.email}"
    cus_deets = db.session.query(Customer).all()
    category = db.session.query(Category).all()

    return render_template(
        'admin/admin.html',
        admin=admin,
        cus_deets=cus_deets,
        category=category
    )
    
@app.route("/admin-logout/")
def admin_logout():
    session.pop('admin_loggedin', None)
    return redirect('/adminlog/')



@app.route('/add-product/', methods=["GET", "POST"])
def add_product():
    cus_id = session.get("loggedin")
    if not cus_id or not db.session.query(Customer).filter(Customer.id == cus_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/adminlogin/')

    form = AddProductForm()
    form.populate_categories()

    if request.method == "GET" or not form.validate_on_submit():
        return render_template(
            'admin/addproduct.html',
            form=form)

    # Handle form submission
    new_product = Product(
        pro_name=form.pro_name.data,
        pro_category_id=form.pro_category_id.data,
        in_stock=form.in_stock.data,
        old_price=form.old_price.data,
        new_price=form.new_price.data,
        id=cus_id  
    )

    if form.pro_picture.data:
        upload_folder = os.path.join(app.root_path, 'static', 'media')
        filename = secure_filename(form.pro_picture.data.filename)
        file_path = os.path.join(upload_folder, filename)
        form.pro_picture.data.save(file_path)
        new_product.pro_picture = filename

    db.session.add(new_product)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect("/add-product/")


