from collections import defaultdict
from flask_login import login_required, current_user
import cloudinary
import cloudinary.uploader
from flask import Flask, flash, render_template, request, jsonify, session, redirect, abort, url_for
from sqlalchemy import exists, text
from sqlalchemy.orm import joinedload
from models import Address, Blog, Cart, Category, Color, EmailHistory, EmailTrack, Order, OrderItem, PasswordResetToken, ProductColor, ProductSize, Review, Tag, Warranty, db, User, Product, ProductImage, ProductVideo, ProductTag, PaymentMethod, WalletTransaction, Ticket
from config import Config
from flask_login import LoginManager, login_user
from functools import wraps
import base64
import html
import os
import re
import secrets
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_migrate import Migrate

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path=".env"):
        if not os.path.exists(path):
            return False

        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)

        return True

try:
    import resend
except ImportError:
    resend = None


load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# ✅ Cloudinary config (KEEP)
cloudinary.config(
    cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
    api_key=app.config["CLOUDINARY_API_KEY"],
    api_secret=app.config["CLOUDINARY_API_SECRET"]
)

# ✅ DB init (KEEP)
db.init_app(app)

# ✅ Login Manager (KEEP)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ✅ Mail (KEEP - but env vars required)
mail = Mail(app)

# ✅ Migrations (IMPORTANT for Railway)
migrate = Migrate(app, db)

# ❌ REMOVE LOCAL STORAGE (Railway pe useless)
# UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]
# IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, "static/images")
# VIDEO_UPLOAD_FOLDER = os.path.join(app.root_path, "static/videos")
# os.makedirs(...)

# ❌ REMOVE THESE (DANGEROUS IN PRODUCTION)
# def ensure_column(...)
# def ensure_variant_columns(...)

# ❌ REMOVE THIS BLOCK COMPLETELY
# with app.app_context():
#     db.create_all()
#     ensure_variant_columns()

# ✅ OPTIONAL DEBUG PRINT (SAFE)
with app.app_context():
    print("DB IN USE:", db.engine.url)
    PasswordResetToken.__table__.create(db.engine, checkfirst=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi"}
BLOG_UPLOAD_SUBDIR = "uploads/blogs"
BLOG_UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads", "blogs")
DEFAULT_IMAGE_URL = "/static/images/default.png"

os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, filetype="image"):
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()

    if filetype == "image":
        return ext in {"png", "jpg", "jpeg", "webp"}
    else:
        return ext in {"mp4", "mov", "avi"}


def save_blog_image(file):
    if not file or not file.filename or not allowed_file(file.filename, "image"):
        return None

    filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{filename}"
    file.save(os.path.join(BLOG_UPLOAD_FOLDER, filename))
    return filename


def request_blog_image_file():
    for field_name in ("cover_image_cropped", "cover_image", "image"):
        file = request.files.get(field_name)
        if file and file.filename:
            return file
    return None


def blog_image_url(image):
    if not image:
        return DEFAULT_IMAGE_URL

    image = str(image).strip().replace("\\", "/")
    if not image:
        return DEFAULT_IMAGE_URL

    if image.startswith(("http://", "https://", "//", "data:")):
        return image

    if image.startswith("/static/"):
        return image

    if image.startswith("static/"):
        return f"/{image}"

    if image.startswith("/uploads/blogs/"):
        return url_for("static", filename=image.lstrip("/"))

    if image.startswith(BLOG_UPLOAD_SUBDIR + "/"):
        return url_for("static", filename=image)

    static_marker = f"static/{BLOG_UPLOAD_SUBDIR}/"
    if static_marker in image:
        return f"/{image[image.index(static_marker):]}"

    return url_for("static", filename=f"{BLOG_UPLOAD_SUBDIR}/{os.path.basename(image)}")


app.jinja_env.globals["blog_image_url"] = blog_image_url


def normalize_optional_int(value):
    if value in (None, "", "null", "None", "undefined"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def request_color_id(data=None):
    data = data or {}
    return normalize_optional_int(
        data.get("color_id")
        or data.get("product_color_id")
        or request.args.get("color_id")
        or request.args.get("product_color_id")
        or request.args.get("color")
    )


def nullable_match_sql(column_name, param_name):
    return f"(({column_name} IS NULL AND :{param_name} IS NULL) OR {column_name}=:{param_name})"


SUPPORT_EMAIL = "beltpurse.com@gmail.com"
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Belt Purse <noreply@belt-purse.com>")


def json_error(message="Something went wrong", status_code=500):
    return jsonify({"success": False, "message": message}), status_code


def send_resend_email(subject, body="", attachments=None, to_email=None, html=None):
    if resend is None:
        raise RuntimeError("resend package is not installed. Run: pip install resend")

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY environment variable is not set")

    resend.api_key = api_key
    params = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email or SUPPORT_EMAIL],
        "subject": subject,
    }

    if html:
        params["html"] = html
    else:
        params["text"] = body

    if attachments:
        params["attachments"] = attachments

    return resend.Emails.send(params)


def get_base_url():
    base_url = (os.environ.get("BASE_URL") or "").strip().rstrip("/")
    if base_url:
        return base_url
    return request.url_root.rstrip("/")


def build_reset_password_url(token):
    return f"{get_base_url()}{url_for('reset_password', token=token)}"


def password_is_strong(password):
    return (
        len(password or "") >= 8
        and re.search(r"[A-Za-z]", password or "") is not None
        and re.search(r"\d", password or "") is not None
    )


def build_password_reset_email(reset_url, username):
    display_name = html.escape(username or "there")
    safe_reset_url = html.escape(reset_url, quote=True)
    return f"""
    <div style="margin:0;padding:0;background:#f7f3ec;font-family:Arial,sans-serif;color:#183633;">
      <div style="max-width:560px;margin:0 auto;padding:32px 18px;">
        <div style="background:#ffffff;border:1px solid #eadfce;border-radius:16px;padding:28px;box-shadow:0 12px 34px rgba(8,62,58,0.08);">
          <h2 style="margin:0 0 12px;color:#083E3A;font-size:24px;">Reset your Belt Purse password</h2>
          <p style="margin:0 0 18px;line-height:1.6;color:#38504d;">Hi {display_name},</p>
          <p style="margin:0 0 22px;line-height:1.6;color:#38504d;">
            We received a request to reset your password. This secure link will expire in 30 minutes.
          </p>
          <a href="{safe_reset_url}" style="display:inline-block;background:#0A5C56;color:#ffffff;text-decoration:none;padding:13px 22px;border-radius:999px;font-weight:600;">
            Reset Password
          </a>
          <p style="margin:24px 0 0;line-height:1.6;color:#6a7c78;font-size:13px;">
            If the button does not work, open this link:<br>
            <a href="{safe_reset_url}" style="color:#0A5C56;">{safe_reset_url}</a>
          </p>
          <p style="margin:18px 0 0;line-height:1.6;color:#6a7c78;font-size:13px;">
            If you did not request this, you can ignore this email.
          </p>
        </div>
      </div>
    </div>
    """


def build_resend_attachment(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename) or "invoice"
    content = base64.b64encode(file_storage.read()).decode("utf-8")
    file_storage.stream.seek(0)

    return {
        "filename": filename,
        "content": content,
    }
    

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("admin"):
            abort(404)

        email = session.get("email")

        if not email:
            abort(404)

        user = User.query.filter_by(email=email).first()

        if not user or not user.is_admin:
            abort(404)

        return f(*args, **kwargs)

    return decorated_function


from flask import send_from_directory
import os

@app.route('/googlef86ab741e88ae339.html')
def google_site_verification():
    return send_from_directory(
        os.getcwd(),
        'googlef86ab741e88ae339.html'
    )


@app.route("/__seed__", methods=["GET"])
def run_seed_route():

    # 🔒 simple security key
    if request.args.get("key") != "1234":
        return "Forbidden", 403

    from seed import seed_colors, seed_products, seed_admin

    with app.app_context():
        seed_colors()
        seed_products()
        seed_admin()

    return "Seed Done Successfully"





from datetime import timedelta

app.permanent_session_lifetime = timedelta(days=7)  # 🔥 7 days login

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        data = request.get_json(silent=True)

        # fallback for HTML form
        if not data:
            data = request.form

        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password) and user.is_admin:

            session['admin'] = True
            session['email'] = user.email

            session.permanent = bool(data.get("remember"))

            return jsonify({"message": "Admin login success"})

        return jsonify({"message": "Invalid admin credentials"}), 401

    return render_template("admin/login.html")

@app.route("/secure-admin-portal-9821")
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_products = Product.query.count()

    return render_template(
        "admin/dashboard.html",
        users=total_users,
        orders=total_orders,
        products=total_products
    )

from werkzeug.security import generate_password_hash

@app.route("/admin/admins", methods=["GET", "POST"])
@admin_required
def admin_list():

    if request.method == "POST":
        username = request.form.get("username")   # ✅ sabse pehle lo
        email = request.form.get("email")
        password = request.form.get("password")

        # ❌ validation
        if not username or not email or not password:
            flash("All fields are required", "error")
            return redirect("/admin/admins")

        # ❌ username already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return redirect("/admin/admins")

        # ❌ email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect("/admin/admins")

        # ✅ create admin
        new_admin = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=True
        )

        db.session.add(new_admin)
        db.session.commit()

        flash("Admin created successfully", "success")
        return redirect("/admin/admins")

    admins = User.query.filter_by(is_admin=True).all()
    return render_template("admin/admin_list.html", admins=admins)

@app.route("/admin/delete-admin/<int:id>", methods=["POST"])
@admin_required
def delete_admin(id):

    admin = User.query.get_or_404(id)

    # ❌ self delete block
    if admin.email == session.get("email"):
        flash("You cannot delete yourself", "error")
        return redirect("/admin/admins")

    # ❌ only admin delete
    if not admin.is_admin:
        abort(404)

    db.session.delete(admin)
    db.session.commit()

    flash("Admin deleted successfully", "success")
    return redirect("/admin/admins")
@app.route("/admin-logout")
def admin_logout():
    session.clear()   # 🔥 FULL session remove

    return redirect("/admin-login")  # ✅ correct route

@app.route("/admin/products")
@admin_required
def admin_products():
    products = Product.query.options(
        db.joinedload(Product.images),
        db.joinedload(Product.videos), 
        db.joinedload(Product.product_colors).joinedload(ProductColor.color)
    ).all()

    return render_template("admin/products.html", products=products)
@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def add_product():

    if request.method == "POST":
        name = request.form.get("name")
        guarantee = request.form.get("guarantee")
        material = request.form.get("material")
        description = request.form.get("description")

        original_price = float(request.form.get("original_price", 0))
        discount_percent = float(request.form.get("discount_percent", 0))
        rating = request.form.get("rating")
        size_unit = request.form.get("size_unit", "inch")

        final_price = original_price - (original_price * discount_percent / 100)

        product = Product(
            name=name,
            price=int(final_price),
            original_price=original_price,
            discount_percent=discount_percent,
            rating=float(rating) if rating else None,
            size_unit=size_unit,
            offer=f"{discount_percent}% OFF" if discount_percent > 0 else None,
            guarantee=guarantee,
            material=material,
            description=description
        )

        db.session.add(product)
        db.session.commit()

        # =========================
        # ✅ SIZES
        # =========================
        sizes = request.form.get("sizes")
        if sizes:
            for s in sizes.split(","):
                s = s.strip()
                if s:
                    db.session.add(ProductSize(
                        product_id=product.id,
                        size_label=s,
                        size_value=float(s)
                    ))

        # =========================
        # 🎨 COLORS + IMAGES
        # =========================
        selected_colors = request.form.getlist("colors")

        for color_id in selected_colors:

            db.session.add(ProductColor(
                product_id=product.id,
                color_id=int(color_id)
            ))

            images = request.files.getlist(f"color_images_{color_id}")

            first_for_color = False   # 🔥 IMPORTANT (per color)

            for img in images:
                if img and allowed_file(img.filename, "image"):

                    result = cloudinary.uploader.upload(img)

                    db.session.add(ProductImage(
                        product_id=product.id,
                        image_url=result["secure_url"],
                        color_id=int(color_id),
                        is_primary=not first_for_color   # ✅ per color primary
                    ))

                    first_for_color = True

        # =========================
        # 🔥 DEFAULT (NO COLOR)
        # =========================
        default_images = request.files.getlist("images")

        first_default = False

        for img in default_images:
            if img and allowed_file(img.filename, "image"):

                result = cloudinary.uploader.upload(img)

                db.session.add(ProductImage(
                    product_id=product.id,
                    image_url=result["secure_url"],
                    color_id=None,
                    is_primary=not first_default
                ))

                first_default = True

        # =========================
        # 🎥 VIDEOS
        # =========================
        for color_id in selected_colors:
            videos = request.files.getlist(f"color_videos_{color_id}")

            for vid in videos:
                if vid and allowed_file(vid.filename, "video"):

                    result = cloudinary.uploader.upload(
                        vid,
                        resource_type="video",
                        folder="products/videos"
                    )

                    db.session.add(ProductVideo(
                        product_id=product.id,
                        video_url=result["secure_url"],
                        color_id=int(color_id)
                    ))

        # =========================
        # 🏷 TAGS
        # =========================
        tags = request.form.get("tags")
        if tags:
            for t in tags.split(","):
                db.session.add(ProductTag(
                    product_id=product.id,
                    tag=t.strip()
                ))

        db.session.commit()
        return redirect("/admin/products")

    # GET
    colors = Color.query.all()
    return render_template(
        "admin/add_product.html",
        colors=colors,
        product=None,
        selected_color_ids=[]
    )
@app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_product(id):

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        # =========================
        # BASIC DETAILS
        # =========================
        product.name = request.form.get("name")
        product.guarantee = request.form.get("guarantee")
        product.material = request.form.get("material")
        product.description = request.form.get("description")
        product.size_unit = request.form.get("size_unit", "inch")

        # =========================
        # PRICE
        # =========================
        original_price = float(request.form.get("original_price", 0))
        discount_percent = float(request.form.get("discount_percent", 0))
        rating = request.form.get("rating")

        final_price = original_price - (original_price * discount_percent / 100)

        product.original_price = int(original_price)
        product.discount_percent = int(discount_percent)
        product.price = int(final_price)
        product.rating = float(rating) if rating else None

        product.offer = f"{discount_percent}% OFF" if discount_percent > 0 else None

        # =========================
        # COLORS RESET
        # =========================
        ProductColor.query.filter_by(product_id=id).delete()

        selected_colors = request.form.getlist("colors")

        # =========================
        # ADD COLORS + NEW IMAGES
        # =========================
        for color_id in selected_colors:

            db.session.add(ProductColor(
                product_id=id,
                color_id=int(color_id)
            ))

            images = request.files.getlist(f"color_images_{color_id}")

            for img in images:
                if img and allowed_file(img.filename, "image"):

                    result = cloudinary.uploader.upload(img)

                    db.session.add(ProductImage(
                        product_id=id,
                        image_url=result["secure_url"],
                        color_id=int(color_id),
                        is_primary=False
                    ))

        # =========================
        # DEFAULT IMAGES (NO COLOR)
        # =========================
        default_images = request.files.getlist("images")

        for img in default_images:
            if img and allowed_file(img.filename, "image"):

                result = cloudinary.uploader.upload(img)

                db.session.add(ProductImage(
                    product_id=id,
                    image_url=result["secure_url"],
                    color_id=None,
                    is_primary=False
                ))

        # =========================
        # 🔥 ENSURE PRIMARY PER COLOR
        # =========================
        colors = ProductColor.query.filter_by(product_id=id).all()

        for pc in colors:

            primary = ProductImage.query.filter_by(
                product_id=id,
                color_id=pc.color_id,
                is_primary=True
            ).first()

            if not primary:
                first_img = ProductImage.query.filter_by(
                    product_id=id,
                    color_id=pc.color_id
                ).first()

                if first_img:
                    first_img.is_primary = True

        # =========================
        # 🔥 DEFAULT PRIMARY (NO COLOR)
        # =========================
        no_color_primary = ProductImage.query.filter_by(
            product_id=id,
            color_id=None,
            is_primary=True
        ).first()

        if not no_color_primary:
            first_img = ProductImage.query.filter_by(
                product_id=id,
                color_id=None
            ).first()

            if first_img:
                first_img.is_primary = True

        # =========================
        # VIDEOS
        # =========================
        for color_id in selected_colors:

            videos = request.files.getlist(f"color_videos_{color_id}")

            for vid in videos:
                if vid and allowed_file(vid.filename, "video"):

                    result = cloudinary.uploader.upload(
                        vid,
                        resource_type="video",
                        folder="products/videos"
                    )

                    db.session.add(ProductVideo(
                        product_id=id,
                        video_url=result["secure_url"],
                        color_id=int(color_id)
                    ))

        # =========================
        # SIZES
        # =========================
        sizes = ProductSize.query.filter_by(product_id=id).all()

        Cart.query.filter_by(product_id=id).delete()


        ProductSize.query.filter_by(product_id=id).delete()
        sizes = request.form.get("sizes")

        if sizes:
            for s in sizes.split(","):
                s = s.strip()
                if s:
                    db.session.add(ProductSize(
                        product_id=id,
                        size_label=s,
                        size_value=float(s)
                    ))

        # =========================
        # TAGS
        # =========================
        ProductTag.query.filter_by(product_id=id).delete()

        tags = request.form.get("tags")

        if tags:
            for t in tags.split(","):
                t = t.strip()
                if t:
                    db.session.add(ProductTag(
                        product_id=id,
                        tag=t
                    ))

        # =========================
        # SAVE
        # =========================
        db.session.commit()

        return redirect("/admin/products")

    # GET
    colors = Color.query.all()

    return render_template(
        "admin/edit_product.html",
        product=product,
        colors=colors
    )

@app.route("/admin/products/delete/<int:id>")
@admin_required
def delete_product(id):

    product = Product.query.get_or_404(id)

    # ❌ BLOCK if in orders
    order_item = OrderItem.query.filter_by(product_id=id).first()

    if order_item:
        return """
        <script>
            alert("❌ Cannot delete! Product is used in an order.");
            window.location.href = "/admin/products";
        </script>
        """

    # 🟡 REMOVE FROM CART
    db.session.execute(
        text("DELETE FROM cart WHERE product_id = :pid"),
        {"pid": id}
    )

    db.session.delete(product)
    db.session.commit()

    return redirect("/admin/products")


@app.route("/admin/video/delete/<int:id>")
@admin_required
def delete_video(id):
    video = ProductVideo.query.get_or_404(id)

    db.session.delete(video)
    db.session.commit()

    return redirect(request.referrer)

@app.route("/admin/image/delete/<int:id>")
@admin_required
def delete_image(id):
    image = ProductImage.query.get_or_404(id)
    product_id = image.product_id
    color_id = image.color_id
    was_primary = image.is_primary

    db.session.delete(image)
    db.session.flush()

    if was_primary:
        replacement = ProductImage.query.filter_by(
            product_id=product_id,
            color_id=color_id
        ).order_by(ProductImage.id).first()
        if replacement:
            replacement.is_primary = True

    db.session.commit()

    return redirect(request.referrer)

@app.route("/admin/image/primary/<int:id>")
@admin_required
def set_primary_image(id):
    image = ProductImage.query.get_or_404(id)

    # 🔥 ONLY same color reset
    ProductImage.query.filter_by(
        product_id=image.product_id,
        color_id=image.color_id
    ).update({"is_primary": False})

    image.is_primary = True

    db.session.commit()

    return redirect(request.referrer)


def generate_slug(title, blog_id=None):
    base_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not base_slug:
        base_slug = uuid.uuid4().hex[:8]
    slug = base_slug
    counter = 1

    while True:
        existing = Blog.query.filter_by(slug=slug).first()
        if not existing or existing.id == blog_id:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug

# 📚 All Blogs (Admin Panel)
@app.route('/admin/blogs')
def admin_blogs():
    blogs = Blog.query.order_by(
        Blog.created_at.is_(None),
        Blog.created_at.desc(),
        Blog.id.desc()
    ).all()
    categories = Category.query.all()

    return render_template(
        "admin/blogs.html",
        blogs=blogs,
        categories=categories
    )

# ➕ Add Blog
@app.route('/admin/blogs/add', methods=['GET', 'POST'])
def add_blog():

    categories =  Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']


        category_id = request.form.get('category')
        seo_title = request.form.get('seo_title') or title
        seo_description = request.form.get('seo_description') or content[:150]
        # 🔥 SEO Friendly Slug
        slug = generate_slug(title)

        # 🔥 Image Upload
        file = request_blog_image_file()

        image_filename = save_blog_image(file)
        app.logger.info("Blog cover image saved: %s", image_filename)


        tag_names = request.form.get('tags', "").split(",")

        tag_objects = []
        for tag in tag_names:
            tag = tag.strip().lower()
            if tag:
                existing = Tag.query.filter_by(name=tag).first()
                if existing:
                    tag_objects.append(existing)
                else:
                    new_tag = Tag(name=tag)
                    db.session.add(new_tag)
                    tag_objects.append(new_tag)


        new_blog = Blog(
            title=title,
            slug=slug,
            content=content,
            image=image_filename,
            author=author,
            category_id=category_id,
            seo_title=seo_title,
            seo_description=seo_description,
            tags=tag_objects,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_published=True
        )

        db.session.add(new_blog)
        db.session.commit()

        return redirect('/admin/blogs')

    return render_template("admin/add_blog.html")


# ✏️ Edit Blog
@app.route('/admin/blogs/edit/<int:id>', methods=['GET', 'POST'])
def edit_blog(id):
    blog = Blog.query.get_or_404(id)
    categories =  Category.query.all()
    if request.method == 'POST':
        blog.title = request.form['title']
        blog.content = request.form['content']
        blog.author = request.form['author']


        blog.category_id = request.form.get('category')
        blog.seo_title = request.form.get('seo_title') or blog.title
        blog.seo_description = request.form.get('seo_description') or blog.content[:150]

        blog.slug=generate_slug(blog.title, blog.id)

        # 🔥 Image update
        file = request_blog_image_file()
        image_filename = save_blog_image(file)
        if image_filename:
            blog.image = image_filename
            app.logger.info("Blog %s cover image updated: %s", blog.id, image_filename)
         

        tag_names = request.form.get('tags', "").split(",")
        blog.tags.clear()

        for tag in tag_names:
            tag = tag.strip().lower()
            if tag:
                existing = Tag.query.filter_by(name=tag).first()
                if existing:
                    blog.tags.append(existing)
                else:
                    new_tag = Tag(name=tag)
                    db.session.add(new_tag)
                    blog.tags.append(new_tag)

                
        blog.is_published = True if request.form.get('is_published') else False
        blog.updated_at = datetime.utcnow()

        db.session.commit()
        return redirect('/admin/blogs')

    return render_template("admin/edit_blog.html", blog=blog)


# 🗑 Delete Blog
@app.route('/admin/blogs/delete/<int:id>')
def delete_blog(id):
    blog = Blog.query.get_or_404(id)

    # optional: delete image file
    

    db.session.delete(blog)
    db.session.commit()

    return redirect('/admin/blogs')

@app.route('/upload-image', methods=['POST'])
def upload_image():
    file = request.files.get('image')

    if not file:
        return jsonify({"error": "No file"}), 400
    
    result = cloudinary.uploader.upload(file)

    return jsonify({
        "url": result["secure_url"]
    })




@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin/orders.html", orders=orders)

@app.route('/admin/orders/<int:id>')
def order_detail(id):
    order = Order.query.get_or_404(id)
    items = OrderItem.query.filter_by(order_id=id).all()
    return render_template("admin/order_detail.html", order=order, items=items)

@app.route('/admin/orders/update/<int:id>', methods=['POST'])
def update_order(id):
    order = Order.query.get_or_404(id)

    order.status = request.form['status']
    order.tracking_number = request.form['tracking_number']

    db.session.commit()
    return redirect('/admin/orders')

@app.route('/my-orders')
def my_orders():
    user_id = session.get('user_id')

    orders = Order.query.filter_by(user_id=user_id).all()

    return render_template("user/orders.html", orders=orders)


def create_order(user_id, cart_items, address_id):

    total = sum(item['price'] * item['qty'] for item in cart_items)

    order = Order(
        user_id=user_id,
        address_id=address_id,
        total_amount=total,
        status="Placed"
    )

    db.session.add(order)
    db.session.commit()

    # add items
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['id'],
            quantity=item['qty'],
            price=item['price']
        )
        db.session.add(order_item)

    db.session.commit()

    return order.id


@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users)

# Fetch orders for modal
@app.route("/admin/users/<int:user_id>/orders")
@admin_required
def admin_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    order_list = []
    for o in orders:
        order_list.append({
            "id": o.id,
            "total_amount": o.total_amount,
            "status": o.status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
            "tracking_number": o.tracking_number
        })
    return jsonify({"orders": order_list})

# Toggle active/deactive user
@app.route("/admin/users/toggle/<int:user_id>")
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_admin:  # never toggle admin
        user.is_active = not getattr(user, 'is_active', True)
        db.session.commit()
    return redirect("/admin/users")


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():

    admin = User.query.filter_by(email=session.get("email")).first()

    if not admin:
        return redirect("/admin-login")

    if request.method == "POST":

        # ======================
        # BASIC UPDATE
        # ======================
        username = request.form.get("username")
        email = request.form.get("email")

        admin.username = username
        admin.email = email

        # ⚠️ session email bhi update karna important hai
        session["email"] = email

        # ======================
        # PASSWORD CHANGE
        # ======================
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if current_password or new_password or confirm_password:

            # ❌ check current password
            if not check_password_hash(admin.password, current_password):
                return """
                <script>
                    alert("❌ Current password incorrect");
                    window.location.href="/admin/settings";
                </script>
                """

            # ❌ match new passwords
            if new_password != confirm_password:
                return """
                <script>
                    alert("❌ Passwords do not match");
                    window.location.href="/admin/settings";
                </script>
                """

            # ✅ update password
            admin.password = generate_password_hash(new_password)

        db.session.commit()

        return """
        <script>
            alert("✅ Settings updated successfully");
            window.location.href="/admin/settings";
        </script>
        """

    return render_template("admin/settings.html", admin=admin)
# ================= HOME =================

@app.route("/", methods=["GET", "POST"])
def home():

    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


    
# ================= REGISTER =================
from werkzeug.security import generate_password_hash

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data received"}), 400

    if not all(k in data for k in ("name", "email", "password")):
        return jsonify({"message": "Missing fields"}), 400
    if len(data['password']) < 6:
      return jsonify({"message": "Password too short"}), 400
    existing_user = User.query.filter_by(username=data['name']).first()

    if existing_user:
       return jsonify({"message": "Username already exists"}), 400

    existing_email = User.query.filter_by(email=data['email']).first()
    if existing_email:
        return jsonify({"message": "Email already registered"}), 400

    # ✅ HASH PASSWORD
    hashed_password = generate_password_hash(data['password'])

    user = User(
        username=data['name'],
        email=data['email'],
        password=hashed_password   # ✅ FIXED
    )

    db.session.add(user)
    db.session.commit()

    session['user'] = user.username
    session['email'] = user.email
    session['user_id'] = user.id

    return jsonify({"message": "Registered successfully"})

# ================= LOGIN =================
from werkzeug.security import check_password_hash
from flask import request, jsonify, session

# LOGIN FIX
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Invalid request"}), 400

    email = data.get('email')
    password = data.get('password')
    remember = bool(data.get('remember'))

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password, password):
        return jsonify({"message": "Wrong password"}), 401

    session.clear()
    session.permanent = remember

    session['user_id'] = user.id
    session['username'] = user.username
    session['email'] = user.email
    session['is_admin'] = user.is_admin

    return jsonify({
        "message": "Login successful",
        "name": user.username,   # ✅ IMPORTANT FIX
        "email": user.email,
        "id": user.id
    }), 200


@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"success": False, "message": "Email required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "Email/User not found."}), 404

    try:
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({"used": True})

        token = secrets.token_urlsafe(48)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            used=False,
        )
        db.session.add(reset_token)
        db.session.flush()

        reset_url = build_reset_password_url(token)
        send_resend_email(
            "Reset your Belt Purse password",
            body=f"Open this link to reset your Belt Purse password: {reset_url}",
            to_email=user.email,
            html=build_password_reset_email(reset_url, user.username),
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Password reset email error: {e}")
        return jsonify({"success": False, "message": "Unable to send reset link right now."}), 500

    return jsonify({"success": True, "message": "Reset password link sent to your email."}), 200


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    token_valid = bool(reset_token and reset_token.expires_at >= datetime.utcnow())

    if request.method == "POST":
        if not token_valid:
            return render_template(
                "reset_password.html",
                token=token,
                token_valid=False,
                error="This password reset link is invalid or expired.",
            ), 400

        new_password = (request.form.get("new_password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()

        if new_password != confirm_password:
            return render_template(
                "reset_password.html",
                token=token,
                token_valid=True,
                error="Passwords do not match.",
            ), 400

        if not password_is_strong(new_password):
            return render_template(
                "reset_password.html",
                token=token,
                token_valid=True,
                error="Password must be 8+ characters and include at least 1 letter and 1 number.",
            ), 400

        user = User.query.get(reset_token.user_id)
        if not user:
            return render_template(
                "reset_password.html",
                token=token,
                token_valid=False,
                error="This password reset link is invalid or expired.",
            ), 400

        user.password = generate_password_hash(new_password)
        reset_token.used = True
        db.session.commit()
        session.clear()
        return redirect("/?show_login=1&reset=success")

    return render_template(
        "reset_password.html",
        token=token,
        token_valid=token_valid,
        error=None if token_valid else "This password reset link is invalid or expired.",
    )

from collections import defaultdict
from flask import jsonify

@app.route('/products')
def products():
    all_products = Product.query.all()

    result = []

    for p in all_products:

        # 📦 related data
        images = ProductImage.query.filter_by(product_id=p.id).order_by(
            ProductImage.color_id,
            ProductImage.is_primary.desc(),
            ProductImage.id
        ).all()

        # 🎨 color-wise images mapping
        color_images = defaultdict(list)

        for img in images:
            if img.color_id:
                color_images[img.color_id].append(img.image_url)

        # 🖼️ fallback images (no color)
        fallback_images = [img.image_url for img in images if not img.color_id]

        # ❌ SKIP if no images at all
        if not images:
            continue

        # =========================
        # ✅ CASE 1: NO COLORS PRODUCT
        # =========================
        if not p.product_colors:
            result.append({
                "id": p.id,
                "product_id": p.id,

                "name": p.name,
                "price": p.price,
                "original_price": p.original_price,
                "discount_percent": p.discount_percent or 0,
                "rating": p.rating or 0,

                "images": fallback_images if fallback_images else [images[0].image_url],

                "color_variant": None,
                "colors": []
            })

        # =========================
        # 🎨 CASE 2: COLOR VARIANTS
        # =========================
        for pc in p.product_colors:

            imgs = color_images.get(pc.color_id)

            # 🧠 fallback logic
            if not imgs:
                imgs = fallback_images if fallback_images else [images[0].image_url]

            # ❌ still empty → skip
            if not imgs:
                continue

            result.append({
                "id": f"{p.id}_{pc.color_id}",   # ✅ UNIQUE CARD ID
                "product_id": p.id,

                "name": p.name,
                "price": p.price,
                "original_price": p.original_price,
                "discount_percent": p.discount_percent or 0,
                "rating": p.rating or 0,

                "images": imgs,

                "color_variant": {
                    "id": pc.color.id,
                    "name": pc.color.name,
                    "code": pc.color.code
                },

                "colors": [
                    {
                        "id": pc.color.id,
                        "name": pc.color.name,
                        "code": pc.color.code
                    }
                ]
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


@app.route('/api/warranty', methods=['POST'])
def warranty():

    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    purchase = request.form.get('purchase')

    file = request.files.get('bill')

    filename = None
    if file:
       ext = file.filename.split('.')[-1]
       filename = f"{uuid.uuid4()}.{ext}"

    new_claim = Warranty(
        name=name,
        phone=phone,
        email=email,
        address=address,
        purchase=purchase,
        bill=filename
    )

    db.session.add(new_claim)
    db.session.commit()

    return jsonify({"message": "Warranty claim submitted successfully"})


@app.route('/send-contact-email', methods=['POST'])
def send_contact_email():
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        message = (data.get("message") or "").strip()

        if not name or not email or not message:
            return json_error("All fields are required", 400)

        body = (
            "New contact message received from Belt Purse website.\n\n"
            f"Customer Name: {name}\n"
            f"Customer Email: {email}\n\n"
            f"Message:\n{message}"
        )

        send_resend_email("New Contact Message - Belt Purse", body)
        return jsonify({"success": True, "message": "Email sent successfully"})
    except Exception as e:
        print(f"Error sending contact email: {e}")
        return json_error()


@app.route('/send-help-email', methods=['POST'])
def send_help_email():
    try:
        data = request.get_json(silent=True) or {}
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()
        user_email = (data.get("user_email") or "").strip()
        user_name = (data.get("user_name") or "").strip()

        if not subject or not message:
            return json_error("Subject and message are required", 400)

        body = (
            "New support issue submitted from Belt Purse account page.\n\n"
            f"Name: {user_name or 'Not provided'}\n"
            f"Email: {user_email or 'Not provided'}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}"
        )

        send_resend_email(f"New Support Issue - {subject}", body)
        return jsonify({"success": True, "message": "Email sent successfully"})
    except Exception as e:
        print(f"Error sending help email: {e}")
        return json_error()


@app.route('/send-warranty-email', methods=['POST'])
def send_warranty_email():
    try:
        name = (request.form.get("w_name") or "").strip()
        phone = (request.form.get("w_phone") or "").strip()
        email = (request.form.get("w_email") or "").strip()
        purchase = (request.form.get("w_purchase") or "").strip()
        address = (request.form.get("w_address") or "").strip()

        if not name or not phone or not purchase:
            return json_error("Name, phone, and purchase source are required", 400)

        body = (
            "New warranty registration received from Belt Purse account page.\n\n"
            f"Full Name: {name}\n"
            f"Phone: {phone}\n"
            f"Email: {email or 'Not provided'}\n"
            f"Purchase Source: {purchase}\n"
            f"Address: {address or 'Not provided'}"
        )

        bill = request.files.get("w_bill")
        attachment = build_resend_attachment(bill)

        try:
            send_resend_email(
                "New Warranty Registration - Belt Purse",
                body,
                attachments=[attachment] if attachment else None
            )
        except Exception as attachment_error:
            if not attachment:
                raise
            print(f"Error sending warranty attachment, retrying without attachment: {attachment_error}")
            send_resend_email("New Warranty Registration - Belt Purse", body)

        return jsonify({"success": True, "message": "Email sent successfully"})
    except Exception as e:
        print(f"Error sending warranty email: {e}")
        return json_error()
# ================= PRODUCT DETAIL =================
@app.route('/product/<int:id>')
def product_detail(id):
    product = db.session.get(Product, id)

    if not product:
        return "Product not found", 404

    selected_color_id = normalize_optional_int(request.args.get("color"))

    images_query = ProductImage.query.filter_by(product_id=id).order_by(
        ProductImage.is_primary.desc(),
        ProductImage.id
    )
    images = images_query.all()
    if selected_color_id:
        images = sorted(
            images,
            key=lambda img: (
                0 if img.color_id == selected_color_id and img.is_primary else
                1 if img.color_id == selected_color_id else
                2 if img.color_id is None and img.is_primary else
                3 if img.is_primary else
                4,
                img.id
            )
        )

    images_data = [
      {
        "id": img.id,
        "image_url": img.image_url,
        "color_id": img.color_id
      }
        for img in images
   ]
    videos = ProductVideo.query.filter_by(product_id=id).all()
    tags = ProductTag.query.filter_by(product_id=id).all()
    sizes = ProductSize.query.filter_by(product_id=id).all()
    colors = ProductColor.query.filter_by(product_id=id).all()
    related_products = Product.query.limit(4).all()
    reviews = Review.query.options(joinedload(Review.user))\
       .filter_by(product_id=id).all()

    return render_template(
        "product.html",
        product=product,
        reviews=reviews,
        images=images_data,
        videos=videos,
        tags=tags,
        sizes=sizes,
        colors=colors,
        related_products=related_products
    )



@app.route('/products-page')
def products_page():
    color_id = request.args.get('color')

    if color_id:
        products = Product.query.join(ProductColor).filter(
            ProductColor.color_id == color_id
        ).all()
    else:
        products = Product.query.all()

    return render_template("products.html", products=products)
# ================= CONTEXT =================
@app.context_processor
def inject_counts():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user:
            cart_count = db.session.execute(text("""
                SELECT SUM(quantity) FROM cart WHERE user_id=:uid
            """), {"uid": user.id}).scalar() or 0

            wishlist_count = db.session.execute(text("""
                SELECT COUNT(*) FROM wishlist WHERE user_id=:uid
            """), {"uid": user.id}).scalar() or 0

            # ✅ FIX: object bhej, string nahi
            return dict(
                cart_count=cart_count,
                wishlist_count=wishlist_count,
                user={
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar
                }
            )

    return dict(cart_count=0, wishlist_count=0, user=None)
# ================= CART =================
from sqlalchemy import text

@app.route('/cart')
def cart_page():
    if 'email' not in session:
        return render_template("cart.html", products=[], total=0, total_items=0)


    user = User.query.filter_by(email=session['email']).first()
    if not user:
        session.clear()
        return redirect('/')

    # ✅ PostgreSQL compatible query (SQLAlchemy)
    rows = db.session.execute(text("""
        SELECT 
            c.id AS cart_id,
            p.id,
            p.name,
            p.price,
            c.color_id,
            c.size_id,
            COALESCE(co.name, '') AS color_name,
            COALESCE(co.code, '') AS color_code,
            COALESCE(
                (SELECT pi.image_url FROM product_images pi
                 WHERE pi.product_id = p.id AND c.color_id IS NOT NULL
                   AND pi.color_id = c.color_id AND pi.is_primary = TRUE
                 ORDER BY pi.id LIMIT 1),
                (SELECT pi.image_url FROM product_images pi
                 WHERE pi.product_id = p.id AND c.color_id IS NOT NULL
                   AND pi.color_id = c.color_id
                 ORDER BY pi.id LIMIT 1),
                (SELECT pi.image_url FROM product_images pi
                 WHERE pi.product_id = p.id AND pi.color_id IS NULL AND pi.is_primary = TRUE
                 ORDER BY pi.id LIMIT 1),
                (SELECT pi.image_url FROM product_images pi
                 WHERE pi.product_id = p.id AND pi.is_primary = TRUE
                 ORDER BY pi.id LIMIT 1),
                (SELECT pi.image_url FROM product_images pi
                 WHERE pi.product_id = p.id
                 ORDER BY pi.id LIMIT 1)
            ) AS image_url,
            c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        LEFT JOIN colors co ON co.id = c.color_id
        WHERE c.user_id = :uid
    """), {"uid": user.id}).fetchall()

    total = 0
    total_items = 0
    clean_items = []

    for p in rows:
        # 🔥 row mapping fix (important for PostgreSQL)
        p = dict(p._mapping)

        price = int(p['price']) if p['price'] else 0
        qty = int(p['quantity']) if p['quantity'] else 0

        total += price * qty
        total_items += qty

        clean_items.append({
            "cart_id": p['cart_id'],
            "id": p['id'],
            "name": p['name'],
            "price": price,
            "quantity": qty,
            "image_url": p['image_url'],
            "color_id": p['color_id'],
            "size_id": p['size_id'],
            "color_name": p['color_name'],
            "color_code": p['color_code']
        })

    return render_template(
        "cart.html",
        products=clean_items,
        total=total,
        total_items=total_items
    )

@app.route('/remove_cart/<int:id>')
def remove_cart(id):
    if 'email' not in session:
        return jsonify({"success": False}), 401

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()
    size_id = normalize_optional_int(request.args.get("size_id"))

    db.session.execute(text("""
        DELETE FROM cart WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        AND (:sid IS NULL OR size_id=:sid)
    """), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id})

    db.session.commit()

    count = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity),0)
        FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({
        "success": True,
        "count": count
    })


@app.route('/decrease_cart/<int:id>')
def decrease_cart(id):
    if 'email' not in session:
        return "Unauthorized", 401

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()
    size_id = normalize_optional_int(request.args.get("size_id"))

    item = db.session.execute(text("""
        SELECT quantity FROM cart
        WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        AND (:sid IS NULL OR size_id=:sid)
        LIMIT 1
    """), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id}).fetchone()

    if item:
        if item.quantity > 1:
            db.session.execute(text("""
                UPDATE cart SET quantity = quantity - 1
                WHERE user_id=:uid AND product_id=:pid
                AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
                AND (:sid IS NULL OR size_id=:sid)
            """), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id})
        else:
            db.session.execute(text("""
                DELETE FROM cart WHERE user_id=:uid AND product_id=:pid
                AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
                AND (:sid IS NULL OR size_id=:sid)
            """), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id})

    db.session.commit()
    return jsonify({"success": True, "message": "Updated"})

@app.route('/add_to_cart/<int:id>', methods=['GET', 'POST'])
def add_to_cart(id):
    if 'email' not in session:
        return jsonify({"error": "Login required"}), 401

    user     = User.query.filter_by(email=session['email']).first()
    data     = request.get_json(silent=True) or {}
    color_id = request_color_id(data)
    size_id  = normalize_optional_int(data.get('size_id')  or request.args.get('size_id'))

    print(f"add_to_cart user={user.id} product={id} color={color_id} size={size_id}")

    existing = db.session.execute(text(
        "SELECT quantity FROM cart WHERE user_id=:uid AND product_id=:pid "
        "AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid) "
        "AND ((size_id IS NULL AND :sid IS NULL) OR size_id=:sid)"
    ), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id}).fetchone()

    if existing:
        db.session.execute(text(
            "UPDATE cart SET quantity = quantity + 1 "
            "WHERE user_id=:uid AND product_id=:pid "
            "AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid) "
            "AND ((size_id IS NULL AND :sid IS NULL) OR size_id=:sid)"
        ), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id})
    else:
        db.session.execute(text(
            "INSERT INTO cart (user_id, product_id, color_id, size_id, quantity) "
            "VALUES (:uid, :pid, :cid, :sid, 1)"
        ), {"uid": user.id, "pid": id, "cid": color_id, "sid": size_id})

    db.session.commit()

    count = db.session.execute(text(
        "SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE user_id=:uid"
    ), {"uid": user.id}).scalar()

    return jsonify({"success": True, "count": count})


# ================= WISHLIST =================
@app.route('/add_to_wishlist/<int:id>')
def add_to_wishlist(id):
    if 'email' not in session:
        return jsonify({"error": "Login required"}), 401

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()
    print(f"add_to_wishlist user={user.id} product={id} color={color_id}")

    # prevent duplicate
    existing = db.session.execute(text("""
        SELECT * FROM wishlist WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
    """), {"uid": user.id, "pid": id, "cid": color_id}).fetchone()

    if not existing:
        db.session.execute(text("""
            INSERT INTO wishlist (user_id, product_id, color_id)
            VALUES (:uid, :pid, :cid)
        """), {"uid": user.id, "pid": id, "cid": color_id})
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
        SELECT p.*, w.color_id, co.name AS color_name, co.code AS color_code,
               COALESCE(
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.color_id IS NULL AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id
                    ORDER BY pi.id LIMIT 1)
               ) AS image_url
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN colors co ON w.color_id = co.id
        WHERE w.user_id = :uid
    """), {"uid": user.id}).fetchall()

    return jsonify([dict(row._mapping) for row in items])

@app.route('/remove_wishlist/<int:id>')
def remove_wishlist(id):
    if 'email' not in session:
        return "Unauthorized", 401

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()
    size_id = normalize_optional_int(request.args.get("size_id"))

    db.session.execute(
        text("""
            DELETE FROM wishlist
            WHERE user_id=:uid AND product_id=:pid
            AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        """),
        {"uid": user.id, "pid": id, "cid": color_id}
    )
    db.session.commit()

    return "Removed"

def get_user():
    return User.query.filter_by(email=session.get('email')).first()

@app.route('/wishlist')
def wishlist_page():
    if 'email' not in session:
         return render_template("wishlist.html", items=[])
    user = User.query.filter_by(email=session['email']).first()
    if not user:
       session.clear()
       return redirect('/')
    
    items = db.session.execute(text("""
        SELECT p.*,
               w.color_id,
               co.name AS color_name,
               co.code AS color_code,
               COALESCE(
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.color_id IS NULL AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id
                    ORDER BY pi.id LIMIT 1)
               ) AS image_url
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN colors co ON co.id = w.color_id
        WHERE w.user_id = :uid
    """), {"uid": user.id}).fetchall()

    return render_template("wishlist.html", items=items)

@app.route('/wishlist/check/<int:product_id>')
def check_wishlist(product_id):
    if 'email' not in session:
        return jsonify({"in_wishlist": False})

    user = get_user()
    if not user:
        return jsonify({"in_wishlist": False})

    color_id = request_color_id()

    exists = db.session.execute(text("""
        SELECT 1 FROM wishlist 
        WHERE user_id=:uid 
        AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id = :cid)
    """), {"uid": user.id, "pid": product_id, "cid": color_id}).fetchone()

    return jsonify({"in_wishlist": bool(exists)})


@app.route('/wishlist/toggle/<int:product_id>', methods=["GET", "POST"])
def toggle_wishlist(product_id):
    if 'email' not in session:
        return jsonify({"error": "Login required"}), 401

    user = get_user()
    color_id = request_color_id()

    existing = db.session.execute(text("""
        SELECT 1 FROM wishlist 
        WHERE user_id=:uid 
        AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id = :cid)
    """), {"uid": user.id, "pid": product_id, "cid": color_id}).fetchone()

    if existing:
        db.session.execute(text("""
            DELETE FROM wishlist 
            WHERE user_id=:uid 
            AND product_id=:pid
            AND ((color_id IS NULL AND :cid IS NULL) OR color_id = :cid)
        """), {"uid": user.id, "pid": product_id, "cid": color_id})
        in_wishlist = False
    else:
        db.session.execute(text("""
            INSERT INTO wishlist (user_id, product_id, color_id)
            VALUES (:uid, :pid, :cid)
        """), {"uid": user.id, "pid": product_id, "cid": color_id})

        in_wishlist = True

    db.session.commit()

    # 🔥 LIVE COUNT SAFE (UNCHANGED BEHAVIOR)
    count = db.session.execute(text("""
        SELECT COUNT(*) FROM wishlist WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({
        "in_wishlist": in_wishlist,
        "count": count
    })
@app.route("/cart/toggle/<int:product_id>", methods=["POST"])
def toggle_cart(product_id):

    if 'email' not in session:
        return jsonify({"error": "login required"}), 401

    data = request.get_json() or {}
    size_id = data.get("size_id")
    color_id = request_color_id(data)

    user = get_user()

    if not size_id:
        return jsonify({"error": "size_required"}), 400

    existing = db.session.execute(text("""
        SELECT 1 FROM cart 
        WHERE user_id=:uid 
        AND product_id=:pid 
        AND size_id=:sid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id = :cid)
    """), {
        "uid": user.id,
        "pid": product_id,
        "sid": size_id,
        "cid": color_id
    }).fetchone()

    if existing:
        db.session.execute(text("""
            DELETE FROM cart 
            WHERE user_id=:uid 
            AND product_id=:pid 
            AND size_id=:sid
            AND ((color_id IS NULL AND :cid IS NULL) OR color_id = :cid)
        """), {
            "uid": user.id,
            "pid": product_id,
            "sid": size_id,
            "cid": color_id
        })
        in_cart = False
    else:
        db.session.execute(text("""
            INSERT INTO cart (user_id, product_id, color_id, size_id, quantity)
            VALUES (:uid, :pid, :cid, :sid, 1)
        """), {
            "uid": user.id,
            "pid": product_id,
            "sid": size_id,
            "cid": color_id
        })
        in_cart = True

    db.session.commit()

    count = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity),0)
        FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({"in_cart": in_cart, "count": count})

@app.route("/cart/check/<int:product_id>")
def check_cart(product_id):

    if 'email' not in session:
        return jsonify({"in_cart": False})

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()

    exists = db.session.execute(text("""
        SELECT size_id FROM cart 
         WHERE user_id=:uid AND product_id=:pid
         AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        LIMIT 1
"""), {"uid": user.id, "pid": product_id, "cid": color_id}).fetchone()

    return jsonify({
      "in_cart": bool(exists),
      "size_id": exists.size_id if exists else None
})

@app.route('/get_counts')
def get_counts():
    if 'email' not in session:
        return jsonify({"cart": 0, "wishlist": 0})

    user = User.query.filter_by(email=session['email']).first()
    if not user:
      session.clear()              # ← clear stale session
      return jsonify({"cart": 0, "wishlist": 0})

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


# script.js compatibility alias
@app.route('/api/counts')
def api_counts():
    return get_counts()


@app.route('/update_quantity/<int:product_id>/<string:action>')
def update_quantity(product_id, action):
    if 'email' not in session:
        return jsonify({"status": "error"})

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()
    size_id = normalize_optional_int(request.args.get("size_id"))
    cart_item = db.session.execute(text("""
        SELECT * FROM cart
        WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        AND (:sid IS NULL OR size_id=:sid)
        LIMIT 1
    """), {"uid": user.id, "pid": product_id, "cid": color_id, "sid": size_id}).fetchone()

    if not cart_item:
        return jsonify({"status": "not_found"})

    qty = int(cart_item.quantity) if cart_item else 0

    if action == "plus":
        qty += 1
    elif action == "minus":
        qty -= 1

    if qty <= 0:
        db.session.execute(text("""
            DELETE FROM cart WHERE user_id=:uid AND product_id=:pid
            AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
            AND (:sid IS NULL OR size_id=:sid)
        """), {"uid": user.id, "pid": product_id, "cid": color_id, "sid": size_id})
    else:
        db.session.execute(text("""
            UPDATE cart SET quantity=:q WHERE user_id=:uid AND product_id=:pid
            AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
            AND (:sid IS NULL OR size_id=:sid)
        """), {"q": qty, "uid": user.id, "pid": product_id, "cid": color_id, "sid": size_id})

    db.session.commit()

    # return updated cart count
    new_count = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity),0) FROM cart WHERE user_id=:uid
    """), {"uid": user.id}).scalar()

    return jsonify({"status": "ok", "quantity": qty, "cart_count": new_count})



@app.route("/product/sizes/<int:product_id>")
def get_product_sizes(product_id):

    sizes = ProductSize.query.filter_by(product_id=product_id).all()

    return jsonify([
        {
            "id": s.id,
            "label": s.size_label,
            "value": s.size_value
        }
        for s in sizes
    ])
@app.route("/cart/selected_size/<int:product_id>")
def get_selected_size(product_id):

    if 'email' not in session:
        return jsonify({"size_id": None})

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()

    row = db.session.execute(text("""
        SELECT size_id 
        FROM cart 
        WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
        LIMIT 1
    """), {"uid": user.id, "pid": product_id, "cid": color_id}).fetchone()

    return jsonify({
        "size_id": row.size_id if row else None
    })

@app.route('/api/orders', methods=['GET'])
def api_orders():
    if 'email' not in session:
        return jsonify([])

    user = User.query.filter_by(email=session['email']).first()

    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()

    return jsonify([{
        "id": o.id,
        "total": o.total_amount,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None
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
        "address_line": a.address_line,
        "city": a.city,
        "state": a.state,
        "pincode": a.pincode
    } for a in addresses]) 

# ================= CART PAGE =================



@app.route("/review/add/<int:product_id>", methods=["POST"])
def add_review(product_id):

    if 'email' not in session:
        return jsonify({"error": "login_required"})

    data = request.get_json()

    user = User.query.filter_by(email=session['email']).first()

    rating = int(data.get("rating"))
    comment = data.get("comment")

    if not comment:
        return jsonify({"error": "empty_comment"})

    review = Review(
        user_id=user.id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({
        "success": True,
        "username": user.username,
        "rating": rating,
        "comment": comment
    })



# ================= CHECKOUT =================
@app.route('/api/checkout-review', methods=['GET'])
def checkout_review():
    """
    Get review data before checkout - shows user details, cart, and addresses
    """
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # ✅ Fetch cart items
    cart_items = db.session.execute(text("""
        SELECT product_id, color_id, quantity 
        FROM cart 
        WHERE user_id = :uid
    """), {"uid": user.id}).fetchall()

    if not cart_items:
        return jsonify({
            "message": "Cart is empty",
            "cart": [],
            "total": 0
        })

    # ✅ Build cart details with product info
    cart_details = []
    total = 0

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            color = Color.query.get(item.color_id) if item.color_id else None
            item_total = product.price * item.quantity
            total += item_total
            cart_details.append({
                "product_id": product.id,
                "product_name": product.name,
                "color_id": item.color_id,
                "color_name": color.name if color else None,
                "quantity": item.quantity,
                "price": product.price,
                "item_total": item_total
            })

    # ✅ Get user's addresses
    addresses = Address.query.filter_by(user_id=user.id).all()
    addresses_list = [{
        "id": a.id,
        "full_name": a.full_name,
        "phone": a.phone,
        "address_line": a.address_line,
        "city": a.city,
        "state": a.state,
        "pincode": a.pincode
    } for a in addresses]

    # ✅ Return review data
    review_data = {
        "user": {
            "name": user.username,
            "email": user.email,
            "phone": user.phone or None,
            "dob": user.dob.strftime('%Y-%m-%d') if user.dob else None,
            "phone_warning": "⚠️ Phone number not set" if not user.phone else None
        },
        "cart": cart_details,
        "cart_count": len(cart_details),
        "total": total,
        "addresses": addresses_list,
        "addresses_count": len(addresses_list),
        "ready_for_checkout": len(addresses_list) > 0 and total > 0
    }

    return jsonify(review_data)

@app.route('/api/sync-guest-cart', methods=['POST'])
def sync_guest_cart():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401
    user = User.query.filter_by(email=session['email']).first()
    items = request.get_json().get('items', [])
    for item in items:
        color_id = normalize_optional_int(item.get('colorId') or item.get('color_id') or item.get('product_color_id'))
        size_id = normalize_optional_int(item.get('sizeId') or item.get('size_id'))
        qty = int(item.get('qty', 1) or 1)

        existing = Cart.query.filter_by(
            user_id=user.id,
            product_id=item['productId'],
            color_id=color_id,
            size_id=size_id
        ).first()
        if existing:
            existing.quantity = (existing.quantity or 0) + qty
        else:
            cart_item = Cart(
                user_id=user.id,
                product_id=item['productId'],
                quantity=qty,
                color_id=color_id,
                size_id=size_id
            )
            db.session.add(cart_item)
    db.session.commit()
    return jsonify({"message": "Cart synced"})

@app.route('/api/sync-guest-wishlist', methods=['POST'])
def sync_guest_wishlist():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401
    user = User.query.filter_by(email=session['email']).first()
    items = request.get_json().get('items', [])
    for item in items:
        db.session.execute(text("""
            INSERT INTO wishlist (user_id, product_id, color_id)
            SELECT :uid, :pid, :cid
            WHERE NOT EXISTS (
                SELECT 1 FROM wishlist WHERE user_id=:uid AND product_id=:pid AND (color_id=:cid OR (color_id IS NULL AND :cid IS NULL))
            )
        """), {"uid": user.id, "pid": item['productId'], "cid": item.get('colorId')})
    db.session.commit()
    return jsonify({"message": "Wishlist synced"})


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'email' not in session:
        if request.method == 'GET':
               return redirect('/')
        return jsonify({"message": "login_required", "redirect": "/checkout"}), 401

    user = User.query.filter_by(email=session['email']).first()

    # ✅ VALIDATE phone number is provided
    if not user.phone or user.phone.strip() == "":
        return jsonify({
            "error": True,
            "message": "Phone number is required to complete order",
            "error_type": "missing_phone",
            "redirect": "/account"
        })
    data = request.json

    # ✅ Fetch cart items
    cart_items = db.session.execute(text("""
        SELECT product_id, color_id, quantity 
        FROM cart 
        WHERE user_id = :uid
    """), {"uid": user.id}).fetchall()

    # ✅ Fix empty check
    if not cart_items:
        return jsonify({"message": "Cart is empty"})

    total = 0

    data = request.get_json() or {}

# 👉 user addresses
    addresses = Address.query.filter_by(user_id=user.id).all()

    if not addresses:
      return jsonify({"message": "No address found"})

    selected_index = data.get("address_index", 0)

    if selected_index >= len(addresses):
        return jsonify({"message": "Invalid address"})

    selected_address = addresses[selected_index]

    order = Order(
      user_id=user.id,
      address_id=selected_address.id,
      total_amount=0,
      status="Pending",
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
            color_id=item.color_id,
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
import time

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    if not user and 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user:
            session['user_id'] = user.id

    if not user:
        return jsonify({"error": "Not logged in"}), 401

    file = request.files.get('avatar')

    if not file:
        return jsonify({"error": "No file"}), 400

    # 🔥 Upload to Cloudinary
    result = cloudinary.uploader.upload(file, folder="avatars")

    # ✅ Save URL in DB
    user.avatar = result["secure_url"]

    db.session.commit()

    return jsonify({
        "url": result["secure_url"]
    })

# ================= ACCOUNT =================
@app.route('/account')
def account():
    if 'email' not in session:
        return redirect('/?show_login=1')

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


# ================= API ROUTES =================
@app.route('/api/profile', methods=['PUT'])
def api_update_profile():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    try:
        data = request.get_json()
        user = User.query.filter_by(email=session['email']).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        # ✅ Update name (optional)
        if data.get("name") and data.get("name").strip() != "":
            user.username = data.get("name").strip()

        # ✅ Update email with uniqueness check
        if data.get("email") and data.get("email").strip() != "":
            new_email = data.get("email").strip()
            # Check if email already exists (and is not the current user's email)
            if new_email != user.email:
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    return jsonify({"error": "Email already registered"}), 400
            user.email = new_email

        # ✅ Update phone (optional)
        if data.get("phone"):
            user.phone = data.get("phone").strip()

        # ✅ Update DOB (optional)
        dob = data.get("dob")
        if dob and dob.strip() != "":
            try:
                user.dob = datetime.strptime(dob, '%Y-%m-%d').date()
                print(f"✅ DOB set to: {user.dob}")
            except ValueError as e:
                return jsonify({"error": f"Invalid date format"}), 400

        # ✅ Handle password change (optional)
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if new_password and new_password.strip() != "":
            # Must provide current password to change password
            if not current_password or current_password.strip() == "":
                return jsonify({"error": "Current password required to change password"}), 400
            
            # Verify current password
            if not check_password_hash(user.password, current_password):
                return jsonify({"error": "Current password is incorrect"}), 400
            
            # Hash and set new password
            user.password = generate_password_hash(new_password)
            print(f"✅ Password updated for user: {user.email}")

        # Commit all changes
        db.session.commit()
        print(f"✅ Profile updated for user: {user.email}")

        # Update session with new email if it changed
        session['email'] = user.email

        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "dob": user.dob.strftime('%Y-%m-%d') if user.dob else None
            }
        })
    
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/api/verify-phone', methods=['POST'])
def api_verify_phone():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    user.phone_verified = True
    db.session.commit()

    return jsonify({"message": "Phone verified"})


import random

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to user's phone (for testing, OTP is printed to console)
    Free alternative: User can read OTP from console/logs
    """
    data = request.get_json()
    phone = data.get("phone")

    if not phone or phone.strip() == "":
        return jsonify({"message": "Phone number required"}), 400

    # Generate OTP
    otp = random.randint(100000, 999999)  # 6-digit OTP

    # Store in session
    session['otp'] = str(otp)
    session['otp_phone'] = phone
    
    # 🔥 For development/testing: Print to console and also return it
    print(f"\n{'='*50}")
    print(f"📱 OTP for {phone}: {otp}")
    print(f"{'='*50}\n")

    return jsonify({
        "message": f"OTP sent to {phone}",
        "otp": str(otp)  # 🔥 For testing during development
    })

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP entered by user
    """
    data = request.get_json()
    entered_otp = data.get("otp")

    if not entered_otp:
        return jsonify({"message": "OTP required"}), 400

    session_otp = session.get('otp')
    
    if str(entered_otp).strip() == str(session_otp).strip():
        try:
            user = User.query.filter_by(email=session['email']).first()
            if not user:
                return jsonify({"message": "User not found"}), 404
            
            user.phone_verified = True
            user.phone = session.get('otp_phone', user.phone)  # Update phone if not already there
            db.session.commit()
            
            print(f"✅ Phone verified for user: {user.email}")

            return jsonify({
                "message": "Phone verified successfully",
                "verified": True
            })
        except Exception as e:
            print(f"❌ Error verifying phone: {e}")
            return jsonify({"message": f"Error: {str(e)}"}), 500
    else:
        return jsonify({"message": "Invalid OTP"}), 400


@app.route('/api/verify-phone-direct', methods=['POST'])
def verify_phone_direct():
    """
    Direct phone verification without OTP (free option)
    Just verify the phone number without SMS
    """
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    data = request.get_json()
    phone = data.get("phone")

    if not phone or phone.strip() == "":
        return jsonify({"message": "Phone number required"}), 400

    try:
        user = User.query.filter_by(email=session['email']).first()
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        user.phone = phone
        user.phone_verified = True
        db.session.commit()
        
        print(f"✅ Phone verified directly for user: {user.email} - {phone}")

        return jsonify({
            "message": "Phone verified successfully (no OTP required)",
            "verified": True
        })
    except Exception as e:
        print(f"❌ Error verifying phone: {e}")
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/addresses', methods=['GET', 'POST'])
def api_addresses():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'GET':
        addresses = Address.query.filter_by(user_id=user.id).all()
        return jsonify([{
            "id": a.id,
            "full_name": a.full_name,
            "phone": a.phone,
            "address_line": a.address_line,
            "city": a.city,
            "state": a.state,
            "pincode": a.pincode
        } for a in addresses])

    data = request.get_json()
    address = Address(
        user_id=user.id,
        full_name=data['full_name'],
        phone=data['phone'],
        address_line=data['address_line'],
        city=data['city'],
        state=data['state'],
        pincode=data['pincode']
    )
    db.session.add(address)
    db.session.commit()
    return jsonify({"message": "Address added"})

@app.route('/api/addresses/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_address(id):
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    address = Address.query.filter_by(id=id, user_id=user.id).first()
    if not address:
        return jsonify({"message": "Address not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": address.id,
            "full_name": address.full_name,
            "phone": address.phone,
            "address_line": address.address_line,
            "city": address.city,
            "state": address.state,
            "pincode": address.pincode
        })

    if request.method == 'PUT':
        data = request.get_json()
        address.full_name = data['full_name']
        address.phone = data['phone']
        address.address_line = data['address_line']
        address.city = data['city']
        address.state = data['state']
        address.pincode = data['pincode']
        db.session.commit()
        return jsonify({"message": "Address updated"})

    if request.method == 'DELETE':
        db.session.delete(address)
        db.session.commit()
        return jsonify({"message": "Address deleted"})

@app.route('/api/wallet', methods=['GET'])
def api_wallet():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    transactions = WalletTransaction.query.filter_by(user_id=user.id).order_by(WalletTransaction.created_at.desc()).all()
    return jsonify({
        "balance": user.balance,
        "transactions": [{
            "id": t.id,
            "amount": t.amount,
            "type": t.type,
            "description": t.description,
            "created_at": t.created_at.isoformat()
        } for t in transactions]
    })

@app.route('/api/wishlist', methods=['GET'])
def api_wishlist():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    rows = db.session.execute(text("""
        SELECT p.id, p.name, p.price, w.color_id,
               co.name AS color_name,
               COALESCE(
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND w.color_id IS NOT NULL
                      AND pi.color_id = w.color_id
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.color_id IS NULL AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id AND pi.is_primary = TRUE
                    ORDER BY pi.id LIMIT 1),
                   (SELECT pi.image_url FROM product_images pi
                    WHERE pi.product_id = p.id
                    ORDER BY pi.id LIMIT 1)
               ) AS image_url
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN colors co ON w.color_id = co.id
        WHERE w.user_id=:uid
    """), {"uid": user.id}).fetchall()

    return jsonify([{
        "id": row.id,
        "name": row.name,
        "price": row.price,
        "color_id": row.color_id,
        "color_name": row.color_name,
        "images": [{"image_url": row.image_url}] if row.image_url else []
    } for row in rows])

@app.route('/api/wishlist/<int:product_id>', methods=['DELETE'])
def api_remove_wishlist(product_id):
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    color_id = request_color_id()

    result = db.session.execute(text("""
        DELETE FROM wishlist
        WHERE user_id=:uid AND product_id=:pid
        AND ((color_id IS NULL AND :cid IS NULL) OR color_id=:cid)
    """), {"uid": user.id, "pid": product_id, "cid": color_id})
    db.session.commit()

    if result.rowcount:
        return jsonify({"message": "Removed from wishlist"})

    return jsonify({"message": "Not in wishlist"}), 404

@app.route('/api/payment-methods', methods=['GET', 'POST'])
def api_payment_methods():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'GET':
        payments = PaymentMethod.query.filter_by(user_id=user.id).all()
        return jsonify([{
            "id": p.id,
            "type": p.type,
            "provider": p.provider,
            "last_four": p.last_four,
            "expiry_month": p.expiry_month,
            "expiry_year": p.expiry_year,
            "is_default": p.is_default
        } for p in payments])

    data = request.get_json()
    payment = PaymentMethod(
        user_id=user.id,
        type=data['type'],
        provider=data['provider'],
        last_four=data['last_four'],
        expiry_month=int(data['expiry_month']),
        expiry_year=int(data['expiry_year'])
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({"message": "Payment method added"})

@app.route('/api/payment-methods/<int:id>', methods=['DELETE'])
def api_delete_payment(id):
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    payment = PaymentMethod.query.filter_by(id=id, user_id=user.id).first()
    if not payment:
        return jsonify({"message": "Payment method not found"}), 404

    db.session.delete(payment)
    db.session.commit()
    return jsonify({"message": "Payment method deleted"})

@app.route('/api/tickets', methods=['GET', 'POST'])
def api_tickets():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'GET':
        tickets = Ticket.query.filter_by(user_id=user.id).order_by(Ticket.created_at.desc()).all()
        return jsonify([{
            "id": t.id,
            "subject": t.subject,
            "message": t.message,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat()
        } for t in tickets])

    data = request.get_json()
    ticket = Ticket(
        user_id=user.id,
        subject=data['subject'],
        message=data['message']
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket created"})

@app.route('/api/terms', methods=['GET'])
def api_terms():
    # Return static terms content
    terms = """
Terms and Conditions

1. Acceptance of Terms
By accessing and using this website, you accept and agree to be bound by the terms and conditions of this agreement.

2. Use License
Permission is granted to temporarily download one copy of the materials on our website for personal, non-commercial transitory viewing only.

3. Disclaimer
The materials on our website are provided on an 'as is' basis. We make no warranties, expressed or implied.

4. Limitations
In no event shall we be liable for any damages arising out of the use or inability to use the materials on our website.

5. Privacy Policy
Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the website.
"""
    return terms

@app.route('/api/delete-account', methods=['DELETE'])
def api_delete_account():
    if 'email' not in session:
        return jsonify({"message": "Not logged in"}), 401

    user = User.query.filter_by(email=session['email']).first()
    # In a real app, you'd want to soft delete or archive data
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return jsonify({"message": "Account deleted"})


@app.route('/blogs')
def blogs():
    blogs = Blog.query.filter_by(is_published=True)\
                      .order_by(
                          Blog.created_at.is_(None),
                          Blog.created_at.desc(),
                          Blog.id.desc()
                      )\
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
