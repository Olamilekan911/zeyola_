from flask import render_template, redirect, flash, session, request, url_for
from werkzeug.security import check_password_hash,generate_password_hash
from sqlalchemy.exc import IntegrityError
from pkg import app
from pkg.models import db, Customer, Admin, Category, Product,Cart,Payment,Order
from pkg.forms import AddProductForm,AdminForm
from werkzeug.utils import secure_filename
import os,werkzeug



@app.route('/adminlog/', methods=['GET', 'POST'])
def admin_login():
    form = AdminForm()
    
    if form.validate_on_submit():  
        email = form.email.data  
        password = form.password.data  

        
        admin = db.session.query(Admin).filter_by(email=email).first()

        if admin:  
            if admin.password:
                
                session['admin_loggedin'] = admin.id
                flash("Welcome back, admin!", "success")
                return redirect(url_for('admin_page'))
            else:
                
                flash("Invalid password. Please try again.", "error")
        else:
            
            flash("No account found with that email.", "error")
        
        
        return redirect(url_for('admin_login'))

    
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

    
    admin_email = admin.email

    cus_deets = db.session.query(Customer).all()


    category = db.session.query(Category).all()


    total_sales = db.session.query(db.func.sum(Order.order_price)).scalar() or 0  
    total_orders = db.session.query(Order).count()  
    orders = db.session.query(Order).all()

    return render_template(
        'admin/admin.html',
        admin=admin_email,
        cus_deets=cus_deets,
        category=category,
        total_sales=total_sales,
        total_orders=total_orders,
        orders=orders
    )

    
@app.route("/admin-logout/")
def admin_logout():
    session.pop('admin_loggedin', None)
    return redirect('/adminlog/')



@app.route('/view-payments/')
def view_payments():
    admin_id = session.get("admin_loggedin")
    if not admin_id or not db.session.query(Admin).filter(Admin.id == admin_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/adminlog/')

    # Fetch all payments from the database
    payments = Payment.query.all()

    return render_template('admin/payment.html', payments=payments)





@app.route('/add-product/', methods=["GET", "POST"])
def add_product():
    admin_id = session.get("admin_loggedin")
    if not admin_id or not db.session.query(Admin).filter(Admin.id == admin_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/adminlog/')

    form = AddProductForm()
    form.populate_categories()

    if request.method == "GET" or not form.validate_on_submit():
        return render_template(
            'admin/addproduct.html',
            form=form)

    
    new_product = Product(
        pro_name=form.pro_name.data,
        pro_category_id=form.pro_category_id.data,
        in_stock=form.in_stock.data,
        old_price=form.old_price.data,
        new_price=form.new_price.data,
        pro_desc=form.pro_desc.data,
        pro_spec=form.pro_spec.data,
        id=admin_id  
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


@app.route('/update-product/<int:product_id>/', methods=["GET", "POST"])
def update_product(product_id):
    admin_id = session.get("admin_loggedin")
    if not admin_id or not db.session.query(Admin).filter(Admin.id == admin_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/adminlog/')

    # Fetch the product to be updated
    product = Product.query.get_or_404(product_id)

    form = AddProductForm()
    form.populate_categories()  # Ensure categories are populated

    # Pre-fill the form with the product's current data on a GET request
    if request.method == "GET":
        form.pro_name.data = product.pro_name
        form.pro_category_id.data = product.pro_category_id
        form.in_stock.data = product.in_stock
        form.old_price.data = product.old_price
        form.new_price.data = product.new_price
        form.pro_desc.data = product.pro_desc
        form.pro_spec.data = product.pro_spec
        return render_template(
            'admin/update.html',
            form=form,
            product=product
        )

    # If the form is submitted and valid
    if form.validate_on_submit():
        product.pro_name = form.pro_name.data
        product.pro_category_id = form.pro_category_id.data
        product.in_stock = form.in_stock.data
        product.old_price = form.old_price.data
        product.new_price = form.new_price.data
        product.pro_desc = form.pro_desc.data
        product.pro_spec = form.pro_spec.data

        # If a new image is uploaded, replace the old one
        if form.pro_picture.data:
            try:
                # Delete the old image if it exists
                if product.pro_picture:
                    old_picture_path = os.path.join(app.root_path, 'static', 'media', product.pro_picture)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)

                # Save the new image
                upload_folder = os.path.join(app.root_path, 'static', 'media')
                filename = secure_filename(form.pro_picture.data.filename)

                # Verify file type
                allowed_extensions = {"jpg", "jpeg", "png", "gif"}
                if filename.split('.')[-1].lower() not in allowed_extensions:
                    flash("Invalid file type. Only images are allowed.", "error")
                    return render_template(
                        'admin/update.html',
                        form=form,
                        product=product
                    )

                file_path = os.path.join(upload_folder, filename)
                form.pro_picture.data.save(file_path)
                product.pro_picture = filename
            except Exception as e:
                flash(f"An error occurred while updating the product image: {str(e)}", "error")
                return render_template(
                    'admin/update.html',
                    form=form,
                    product=product
                )

        # Commit the updated product details to the database
        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
        except Exception as e:
            flash(f"An error occurred while saving changes: {str(e)}", "error")
            return render_template(
                'admin/update.html',
                form=form,
                product=product
            )

        return redirect('/view-products/')

   

    return render_template(
        'admin/update.html',
        form=form,
        product=product
    )


@app.route('/delete-product/<int:product_id>/', methods=["POST"])
def delete_product(product_id):
    admin_id = session.get("admin_loggedin")
    if not admin_id:
        flash('You need to log in as an admin first!', 'error')
        return redirect('/adminlog/')

    product = Product.query.get_or_404(product_id)

    try:
        # Handle related orders and payments
        orders = Order.query.filter_by(product_id=product_id).all()
        for order in orders:
            payments = Payment.query.filter_by(payment_order_id=order.order_id).all()
            for payment in payments:
                db.session.delete(payment)  # Delete associated payments
            
            db.session.delete(order)  # Delete associated orders
        
        # Remove the product's image if it exists
        if product.pro_picture:
            picture_path = os.path.join(app.root_path, 'static', 'media', product.pro_picture)
            if os.path.exists(picture_path):
                os.remove(picture_path)

        # Delete the product
        db.session.delete(product)
        db.session.commit()

        flash('Product and associated records deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'error')

    return redirect('/view-products/')


@app.route('/view-products/', methods=["GET"])
def view_products():
    admin_id = session.get("admin_loggedin")
    if not admin_id or not db.session.query(Admin).filter(Admin.id == admin_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/adminlog/')

    
    page = request.args.get('page', 1, type=int)
    per_page = 10  
    products = Product.query.filter_by(id=admin_id).paginate(page=page, per_page=per_page)

    return render_template(
        'admin/view_shop.html',
        products=products
    )


@app.route('/admin/customers/', methods=['GET'])
def admin_customers():
    
    if 'admin_loggedin' not in session:
        flash('You need to log in as an admin to view this page.', 'error')
        return redirect('/admin/login')

    
    customers = Customer.query.all()

    return render_template('admin/customer.html', customers=customers)

@app.route('/admin-orders/')
def admin_orders():
    # Check if admin is logged in
    admin_id = session.get("admin_loggedin")
    cus_id = session.get("cus_loggedin")
    if not admin_id:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('admin_login'))

    # Get the admin details
    admin = db.session.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        flash("Invalid session. Please log in again.", "error")
        return redirect(url_for('admin_login'))

    # Pagination: Correct the query to paginate properly
    page = request.args.get('page', 1, type=int)  # Get the current page from the query string
    pagination = db.session.query(Order).paginate(page=page, per_page=10, error_out=False)  # Paginate with 10 orders per page

    # Debugging: Print order statuses for verification (optional)
    for order in pagination.items:
        print(f"Order ID: {order.order_id}, Order Status: {order.order_status}")

    return render_template(
        'admin/vieworders.html',  
        admin=admin,
        orders=pagination,
        cus_id=cus_id  # Pass the paginated orders to the template
    )

