from . import database
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    user_name = database.Column(database.String(50))
    email = database.Column(database.String(100), unique=True)
    phone_number = database.Column(database.Integer, unique=True)
    hashed_password = database.Column(database.String(150))
    created_at = database.Column(database.DateTime(), default=datetime.utcnow)

    carts = database.relationship('Cart', backref=database.backref('user', lazy=True))
    orders = database.relationship('Order', backref=database.backref('user', lazy=True))
    
    @property
    def password(self):
        raise AttributeError('unreadable password')

    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password=password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password=password)
    
    def __str__(self):
        return '<User %r>' % self.id
    
class Cart(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    price = database.Column(database.Float, nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    quantity = database.Column(database.Integer, nullable=False)

    users_link = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    products_link = database.Column(database.Integer, database.ForeignKey('product.id'), nullable=False)

    def __str__(self):
        return '<Cart %r>' % self.id

class Order(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    quantity = database.Column(database.Integer, nullable=False)
    price = database.Column(database.Float, nullable=False)
    payment_id = database.Column(database.String(1000), nullable=False)
    status = database.Column(database.String(100), nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)

    users_link = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    products_link = database.Column(database.Integer, database.ForeignKey('product.id'), nullable=False)
    
    def __str__(self):
        return '<Order %r>' % self.id

class Product(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    product_name = database.Column(database.String(100), nullable=False)
    price = database.Column(database.Float, nullable=False)
    description = database.Column(database.String(1000), nullable=False)
    in_stock = database.Column(database.Integer, nullable=False)
    product_picture = database.Column(database.String(1000), nullable=False)
    main_category = database.Column(database.String(50), nullable=False)
    sub_category = database.Column(database.String(50), nullable=False)
    date_added = database.Column(database.DateTime, default=datetime.utcnow)

    carts = database.relationship('Cart', backref=database.backref('product', lazy=True), cascade='all, delete-orphan')
    orders = database.relationship('Order', backref=database.backref('product', lazy=True), cascade='all, delete-orphan')

    def __str__(self):
        return '<Product %r>' % self.product_name

class user_interaction(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    type = database.Column(database.String(20), nullable=False)
    weight = database.Column(database.Integer, default=1)
    interaction_count = database.Column(database.Integer, default=1)
    last_interaction_date = database.Column(database.DateTime, default=datetime.utcnow)
    
    user = database.relationship('User', backref=database.backref('interactions', lazy=True))
    product = database.relationship('Product', backref=database.backref('user_interactions', lazy=True, cascade='all, delete-orphan'))
    
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    product_id = database.Column(database.Integer, database.ForeignKey('product.id'), nullable=False)

    def __str__(self):
        return '<user_interaction %r>' % self.id