from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


wishlist = db.Table('wishlist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'))
)
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255))
    remember_token = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_admin = db.Column(db.Boolean, default=False)

    # Additional profile fields
    phone = db.Column(db.String(15))
    dob = db.Column(db.Date)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=0.0)  # Wallet balance

    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    wishlist_products = db.relationship('Product', secondary=wishlist, backref='wishlisted_by')
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)
    wallet_transactions = db.relationship('WalletTransaction', backref='user', lazy=True)
    tickets = db.relationship('Ticket', backref='user', lazy=True) 

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Integer)  # final price

    original_price = db.Column(db.Integer)
    discount_percent = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float)

    offer = db.Column(db.String(100))
    guarantee = db.Column(db.String(100))
    material = db.Column(db.String(255))
    description = db.Column(db.Text)

    size_unit = db.Column(db.String(20), default="inch")

    images = db.relationship('ProductImage', backref='product', cascade="all, delete")
    videos = db.relationship('ProductVideo', backref='product', cascade="all, delete")
    tags = db.relationship('ProductTag', backref='product', cascade="all, delete")
    sizes = db.relationship('ProductSize', backref='product', cascade="all, delete")
    product_colors = db.relationship(
        'ProductColor',
        backref='product',
        cascade="all, delete"
    )
    reviews = db.relationship(
        "Review",
        backref="product",
        cascade="all, delete"
    )

class ProductSize(db.Model):
    __tablename__ = "product_sizes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    size_label = db.Column(db.String(50))   # S / M / L or 32
    size_value = db.Column(db.Float)        # actual width/length
    
class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    image_url = db.Column(db.String(255))
    is_primary = db.Column(db.Boolean, default=False)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)


class ProductVideo(db.Model):
    __tablename__ = 'product_videos'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    video_url = db.Column(db.String(255))
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)

class ProductTag(db.Model):
    __tablename__ = 'product_tags'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    tag = db.Column(db.String(100))


class Color(db.Model):
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    code = db.Column(db.String(20))

class ProductColor(db.Model):
    __tablename__ = 'product_colors'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'))

    color = db.relationship('Color')


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type = db.Column(db.String(50))  # e.g., 'card', 'paypal', 'bank'
    provider = db.Column(db.String(50))  # e.g., 'visa', 'mastercard'
    last_four = db.Column(db.String(4))  # last 4 digits
    expiry_month = db.Column(db.Integer)
    expiry_year = db.Column(db.Integer)
    is_default = db.Column(db.Boolean, default=False)
    # For security, don't store full card details, assume tokenized


class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Float)
    type = db.Column(db.String(50))  # 'credit', 'debit'
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address_line = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))

    total_amount = db.Column(db.Float)
    status = db.Column(db.String(50), default='Pending')
    tracking_number = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)


# Wishlist association table

blog_tags = db.Table('blog_tags',
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Blog(db.Model):
    __tablename__ = 'blog'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True)
    content = db.Column(db.Text)
    image = db.Column(db.String(500))
    author = db.Column(db.String(100))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category')

    seo_title = db.Column(db.String(255))
    seo_description = db.Column(db.String(255))

    tags = db.relationship('Tag', secondary=blog_tags, backref='blogs')

    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=True)


class EmailHistory(db.Model):
    __tablename__ = "email_history"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255))
    content = db.Column(db.Text)
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    sent_by = db.Column(db.String(100))
    total_users = db.Column(db.Integer)
    opened = db.Column(db.Integer, default=0)


class EmailTrack(db.Model):
    __tablename__ = "email_track"

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("email_history.id"))
    user_email = db.Column(db.String(100))
    opened = db.Column(db.Boolean, default=False)


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='Open')  # 'Open', 'In Progress', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="reviews")

class Warranty(db.Model):
    __tablename__ = "warranty"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))

    address = db.Column(db.Text)
    purchase = db.Column(db.String(50))  # online/offline/website

    bill = db.Column(db.String(255))  # uploaded file name

    created_at = db.Column(db.DateTime, default=datetime.utcnow)