from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(201), nullable=False)

class Customer(db.Model):


    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(201), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cart_items = db.relationship('Cart', backref='customer', lazy=True)
    orders = db.relationship('Order', back_populates='customer', lazy=True)
    payments = db.relationship('Payment', back_populates='customer', lazy=True)

    def __str__(self):
        return f'<Customer {self.fname} {self.lname}>'

class Product(db.Model):


    product_id = db.Column(db.Integer, primary_key=True)
    pro_name = db.Column(db.String(100), nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    pro_desc = db.Column(db.Text, nullable=False)
    pro_spec = db.Column(db.Text, nullable=False)
    pro_picture = db.Column(db.String(1000), nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    pro_category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', back_populates='products')
    cart_items = db.relationship('Cart', backref='product', lazy=True)
    orders = db.relationship('Order', back_populates='product', lazy=True, cascade="all, delete")

    def __str__(self):
        return f'<Product {self.pro_name}>'

class Category(db.Model):


    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), nullable=False)

    # Relationships
    products = db.relationship('Product', back_populates='category', lazy=True)

    def __str__(self):
        return f'<Category {self.category_name}>'    


class Cart(db.Model):
    __tablename__ = 'cart_item'
    cart_id = db.Column(db.Integer, primary_key=True)
    cart_quantity = db.Column(db.Integer, nullable=False)
    # Foreign Keys
    cus_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)

    def __str__(self):
        return f'<Cart {self.cart_id}>'


class Order(db.Model):

    order_id = db.Column(db.Integer, primary_key=True)
    order_quantity = db.Column(db.Integer, nullable=False)
    order_price = db.Column(db.Float, nullable=False)
    order_status = db.Column(db.String(100), nullable=False)
    payment_id = db.Column(db.String(1000), nullable=False)
    order_reference = db.Column(db.String(45), nullable=False)

    # Foreign Keys
    cus_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)

    # Relationships
    customer = db.relationship('Customer', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')

    def __str__(self):
        return f'<Order {self.order_id}>'

class Payment(db.Model):


    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    payment_status = db.Column(db.Enum('pending', 'paid', 'failed'), nullable=False, server_default="pending")
    payment_custid = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    payment_ref = db.Column(db.String(100), nullable=True)
    payment_amt = db.Column(db.Float, nullable=True)
    payment_data = db.Column(db.Text, nullable=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='payments')
    order = db.relationship('Order', backref='payment', lazy=True)

    def __str__(self):
        return f'<Payment {self.payment_id}>'


class State(db.Model):
    state_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state_name = db.Column(db.String(100), nullable=False)
    lgas = db.relationship('Lga', backref='state')

class Lga(db.Model):
    lga_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lga_name = db.Column(db.String(100), nullable=False)
    lga_state = db.Column(db.Integer ,db.ForeignKey('state.state_id') , nullable=False,)