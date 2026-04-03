import sqlite3
from flask_mail import Mail, Message
from flask import Flask, render_template, request, jsonify, session, redirect
from pymysql import connect
from sqlalchemy import text
from models import Address, Blog, Order, OrderItem, Subscriber, db, User, Product, ProductImage, ProductVideo, ProductTag
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "your_secret_key"
mail = Mail(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# ================= HOME =================
SHOW_COMING_SOON = True

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        email = request.form.get("email")

        if email:
            try:
                subscriber = Subscriber(email=email)
                db.session.add(subscriber)
                db.session.commit()
                c = connect.cursor()
                c.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
                
                sqlite3.Connection.close()

                # 📧 SEND EMAIL
                msg = Message(
                    subject="You're on the list 🎉",
                    sender=app.config["MAIL_USERNAME"],
                    recipients=[email]
                )

                msg.html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:Poppins,Arial;">

<div style="max-width:600px;margin:auto;background:#1a1a1a;padding:40px;text-align:center;color:#fff;border-radius:10px;">

    <img src="https://belt-parse.com/static/images/Belt-Purse_logo-01.png" width="150" style="margin-bottom:20px;">

    <h2 style="letter-spacing:2px;">WELCOME TO BELTPURSE</h2>

    <p style="color:#ccc;font-size:14px;">
        Thank you for subscribing. You're now on our exclusive launch list.
    </p>

    <div style="margin:25px 0;padding:15px;background:#000;border-radius:8px;">
        <p style="color:#d4af37;font-size:18px;margin:0;">
            Luxury is arriving soon ✨
        </p>
    </div>

    <p style="font-size:13px;color:#aaa;">
        We'll notify you when we go live.
    </p>

    <hr style="border:none;border-top:1px solid #333;margin:30px 0;">

    <p style="font-size:12px;color:#777;">
        © 2026 BeltPurse. All rights reserved.
    </p>

</div>

</body>
</html>
"""

                mail.send(msg)

                message = "Subscribed + Email sent 🎉"

            except sqlite3.IntegrityError:
                message = "Email already registered!"

    return render_template("coming_soon.html", message=message)


# 🔥 ADD THIS ROUTE (IMPORTANT)
@app.route("/preview")
def preview():
    return render_template("index.html")
# ================= REGISTER =================
from werkzeug.security import generate_password_hash

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data received"}), 400

    if not all(k in data for k in ("name", "email", "password")):
        return jsonify({"message": "Missing fields"}), 400

    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({"message": "Email already exists"}), 400

    # ✅ HASH PASSWORD
    hashed_password = generate_password_hash(data['password'])

    user = User(
        username=data['name'],
        email=data['email'],
        password=hashed_password   # ✅ FIXED
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"})

# ================= LOGIN =================
from werkzeug.security import check_password_hash

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data"}), 400

    # ✅ Only check email
    user = User.query.filter_by(
        email=data.get('email')
    ).first()

    # ✅ Compare hashed password
    if user and check_password_hash(user.password, data.get('password')):
        session['user'] = user.username
        session['email'] = user.email

        return jsonify({
            "message": "Login successful",
            "name": user.username
        })

    return jsonify({"message": "Invalid credentials"}), 401

# ================= PRODUCTS =================
@app.route('/products')
def products():
    products = Product.query.all()

    result = []

    for p in products:
        images = ProductImage.query.filter_by(product_id=p.id).all()
        videos = ProductVideo.query.filter_by(product_id=p.id).all()
        tags = ProductTag.query.filter_by(product_id=p.id).all()

        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "offer": p.offer,
            "guarantee": p.guarantee,
            "material": p.material,
            "description": p.description,
            "images": [img.image_url for img in images],
            "videos": [vid.video_url for vid in videos],
            "tags": [t.tag for t in tags]
        })

    return jsonify(result)

@app.route('/api/search')
def api_search():
    query = request.args.get('q')

    products = Product.query.filter(
        Product.name.ilike(f"%{query}%")
    ).limit(6).all()

    result = []

    for p in products:
        image = ProductImage.query.filter_by(product_id=p.id).first()

        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "image": image.image_url if image else "/static/images/default.png"
        })

    return jsonify(result)

# ================= PRODUCT DETAIL =================
@app.route('/product/<int:id>')
def product_detail(id):
    product = db.session.get(Product, id)

    if not product:
        return "Product not found", 404

    images = ProductImage.query.filter_by(product_id=id).all()
    videos = ProductVideo.query.filter_by(product_id=id).all()
    tags = ProductTag.query.filter_by(product_id=id).all()

    related_products = Product.query.limit(4).all()

    return render_template(
        "product.html",
        product=product,
        images=images,
        videos=videos,
        tags=tags,
        related_products=related_products
    )



@app.route('/products-page')
def products_page():
    return render_template("products.html")


# ================= CONTEXT =================
@app.context_processor
def inject_counts():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        cart_count = db.session.execute(text("""
            SELECT SUM(quantity) FROM cart WHERE user_id=:uid
        """), {"uid": user.id}).scalar() or 0

        wishlist_count = db.session.execute(text("""
            SELECT COUNT(*) FROM wishlist WHERE user_id=:uid
        """), {"uid": user.id}).scalar() or 0

        return dict(cart_count=cart_count, wishlist_count=wishlist_count)

    return dict(cart_count=0, wishlist_count=0)

# ================= CART =================


@app.route('/cart')
def cart_page():
    if 'email' not in session:
        return redirect('/')

    user = User.query.filter_by(email=session['email']).first()

    items = db.session.execute(text("""
    SELECT 
        p.*, 
        (SELECT image_url 
         FROM product_images 
         WHERE product_id = p.id 
         LIMIT 1) AS image_url,
        c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = :uid
        """), {"uid": user.id}).fetchall()
    
    return render_template("cart.html", products=items)

@app.route('/remove_cart/<int:id>')
def remove_cart(id):
    if 'email' not in session:
        return "Unauthorized", 401

    user = User.query.filter_by(email=session['email']).first()

    db.session.execute(text("""
        DELETE FROM cart WHERE user_id=:uid AND product_id=:pid
    """), {"uid": user.id, "pid": id})
    db.session.commit()

    return "Removed"

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'email' not in session:
        return jsonify({"error": "Login required"}), 401

    user = User.query.filter_by(email=session['email']).first()

    existing = db.session.execute(text("""
        SELECT * FROM cart WHERE user_id=:uid AND product_id=:pid
    """), {"uid": user.id, "pid": id}).fetchone()

    if existing:
        db.session.execute(text("""
            UPDATE cart SET quantity = quantity + 1
            WHERE user_id=:uid AND product_id=:pid
        """), {"uid": user.id, "pid": id})
    else:
        db.session.execute(text("""
            INSERT INTO cart (user_id, product_id)
            VALUES (:uid, :pid)
        """), {"uid": user.id, "pid": id})

    db.session.commit()

    count = db.session.execute(text("""
        SELECT SUM(quantity) FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({"count": count})

# ================= WISHLIST =================
@app.route('/add_to_wishlist/<int:id>')
def add_to_wishlist(id):
    if 'email' not in session:
        return jsonify({"error": "Login required"}), 401

    user = User.query.filter_by(email=session['email']).first()

    # prevent duplicate
    existing = db.session.execute(text("""
        SELECT * FROM wishlist WHERE user_id=:uid AND product_id=:pid
    """), {"uid": user.id, "pid": id}).fetchone()

    if not existing:
        db.session.execute(text("""
            INSERT INTO wishlist (user_id, product_id)
            VALUES (:uid, :pid)
        """), {"uid": user.id, "pid": id})
        db.session.commit()

    # count from DB
    count = db.session.execute(text("""
        SELECT COUNT(*) FROM wishlist WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({"count": count})

@app.route('/get_wishlist')
def get_wishlist():
    if 'email' not in session:
        return jsonify([])

    user = User.query.filter_by(email=session['email']).first()

    items = db.session.execute(text("""
        SELECT p.*, pi.image_url 
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN product_images pi ON p.id = pi.product_id
        WHERE w.user_id = :uid
        GROUP BY p.id
    """), {"uid": user.id}).fetchall()

    return jsonify([dict(row._mapping) for row in items])

@app.route('/remove_wishlist/<int:id>')
def remove_wishlist(id):
    if 'email' not in session:
        return "Unauthorized", 401

    user = User.query.filter_by(email=session['email']).first()

    db.session.execute(
        text("DELETE FROM wishlist WHERE user_id=:uid AND product_id=:pid"),
        {"uid": user.id, "pid": id}
    )
    db.session.commit()

    return "Removed"

@app.route('/wishlist')
def wishlist_page():
    if 'email' not in session:
        return redirect('/')

    user = User.query.filter_by(email=session['email']).first()

    items = db.session.execute(text("""
        SELECT p.* FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = :uid
    """), {"uid": user.id}).fetchall()

    return render_template("wishlist.html", items=items)


@app.route('/get_counts')
def get_counts():
    if 'email' not in session:
        return jsonify({"cart": 0, "wishlist": 0})

    user = User.query.filter_by(email=session['email']).first()

    cart_count = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity),0) FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    wishlist_count = db.session.execute(text("""
        SELECT COUNT(*) FROM wishlist WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({
        "cart": cart_count,
        "wishlist": wishlist_count
    })

@app.route('/update_quantity/<int:product_id>/<string:action>')
def update_quantity(product_id, action):
    if 'email' not in session:
        return jsonify({"status": "error"})

    user = User.query.filter_by(email=session['email']).first()

    cart_item = db.session.execute(text("""
        SELECT * FROM cart WHERE user_id=:uid AND product_id=:pid
    """), {"uid": user.id, "pid": product_id}).fetchone()

    if not cart_item:
        return jsonify({"status": "not_found"})

    qty = cart_item.quantity

    if action == "plus":
        qty += 1
    elif action == "minus":
        qty -= 1

    if qty <= 0:
        db.session.execute(text("""
            DELETE FROM cart WHERE user_id=:uid AND product_id=:pid
        """), {"uid": user.id, "pid": product_id})
    else:
        db.session.execute(text("""
            UPDATE cart SET quantity=:q WHERE user_id=:uid AND product_id=:pid
        """), {"q": qty, "uid": user.id, "pid": product_id})

    db.session.commit()

    # return updated cart count
    new_count = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity),0) FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({"status": "ok", "quantity": qty, "cart_count": new_count})

# ================= ORDERS =================
@app.route('/get_orders')
def get_orders():
    if 'email' not in session:
        return jsonify([])

    user = User.query.filter_by(email=session['email']).first()

    orders = Order.query.filter_by(user_id=user.id).all()

    return jsonify([{
        "id": o.id,
        "total": o.total_amount,
        "status": o.status
    } for o in orders])

# ================= ADDRESS =================
@app.route('/add_address', methods=['POST'])
def add_address():
    if 'email' not in session:
        return jsonify({"message": "Login required"}), 401

    data = request.get_json()
    user = User.query.filter_by(email=session['email']).first()

    address = Address(
        user_id=user.id,   # ✅ FIXED
        full_name=data['full_name'],
        phone=data['phone'],
        address_line=data['address_line'],
        city=data['city'],
        state=data['state'],
        pincode=data['pincode']
    )

    db.session.add(address)
    db.session.commit()

    return jsonify({"message": "Address saved"})

@app.route('/get_addresses')
def get_addresses():
    if 'email' not in session:
        return jsonify([])

    user = User.query.filter_by(email=session['email']).first()

    addresses = Address.query.filter_by(user_id=user.id).all()  # ✅ FIXED

    return jsonify([{
        "full_name": a.full_name,
        "phone": a.phone,
        "city": a.city,
        "pincode": a.pincode
    } for a in addresses])

# ================= CART PAGE =================


# ================= CHECKOUT =================
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'email' not in session:
        return jsonify({"message": "Login required"}), 401

    user = User.query.filter_by(email=session['email']).first()

    # ✅ Fetch cart items
    cart_items = db.session.execute(text("""
        SELECT product_id, quantity 
        FROM cart 
        WHERE user_id = :uid
    """), {"uid": user.id}).fetchall()

    # ✅ Fix empty check
    if not cart_items:
        return jsonify({"message": "Cart is empty"})

    total = 0

    # ✅ Create order first
    order = Order(
        user_id=user.id,
        total_amount=0,
        status="Processing",
        tracking_number=f"TRK{user.id}{len(cart_items)}"
    )

    db.session.add(order)
    db.session.commit()

    # ✅ Loop properly
    for item in cart_items:
        pid = item.product_id
        qty = item.quantity

        product = Product.query.get(pid)

        if not product:
            continue

        item_total = product.price * qty
        total += item_total

        db.session.add(OrderItem(
            order_id=order.id,
            product_id=pid,
            quantity=qty,
            price=product.price
        ))

    # ✅ Update total
    order.total_amount = total
    db.session.commit()

    # ✅ Clear cart from DB (IMPORTANT)
    db.session.execute(text("""
        DELETE FROM cart WHERE user_id = :uid
    """), {"uid": user.id})
    db.session.commit()

    return jsonify({"message": "Order placed successfully"})

# ================= TRACK =================
@app.route('/track/<tracking>')
def track(tracking):
    order = Order.query.filter_by(tracking_number=tracking).first()

    if not order:
        return jsonify({"message": "Invalid tracking"}), 404

    return jsonify({
        "status": order.status,
        "tracking": order.tracking_number
    })

# ================= AVATAR =================
import os
from werkzeug.utils import secure_filename

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    file = request.files['file']

    filename = secure_filename(file.filename)
    path = os.path.join('static/images', filename)
    file.save(path)

    user = User.query.filter_by(email=session['email']).first()
    user.avatar = filename
    db.session.commit()

    return jsonify({
        "message": "Uploaded successfully",
        "url": "/static/images/" + filename
    })

# ================= ACCOUNT =================
@app.route('/account')
def account():
    if 'email' not in session:
        return redirect('/')

    user = User.query.filter_by(email=session['email']).first()
    return render_template("account.html", user=user)

# ================= UPDATE PROFILE =================
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    data = request.get_json()
    user = User.query.filter_by(email=session['email']).first()

    user.username = data.get("name")   # ✅ FIXED
    user.email = data.get("email")

    if data.get("password"):
        user.password = data.get("password")

    db.session.commit()

    session['user'] = user.username   # ✅ FIXED
    session['email'] = user.email

    return jsonify({"message": "Profile updated"})



@app.route('/blogs')
def blogs():
    blogs = Blog.query.filter_by(is_published=True)\
                      .order_by(Blog.created_at.desc())\
                      .all()
    return render_template("blogs.html", blogs=blogs)


@app.route('/blog/<slug>')
def blog_detail(slug):
    blog = Blog.query.filter_by(slug=slug).first()

    if not blog:
        return "Blog not found", 404

    return render_template("blog_detail.html", blog=blog)



@app.route('/shipping-policy')
def shipping_policy():
    return render_template("shipping.html")

@app.route('/return-policy')
def return_policy():
    return render_template("returns.html")

@app.route('/privacy-policy')
def privacy_policy():
    return render_template("privacy.html")

@app.route('/terms')
def terms():
    return render_template("terms.html")

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= RUN =================
if __name__ == '__main__':
    app.run()