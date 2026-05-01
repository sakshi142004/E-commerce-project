from app import app
from models import db, Color, Product, ProductColor
from werkzeug.security import generate_password_hash
from models import User

# =========================
# 🔹 SEED COLORS
# =========================
def seed_colors():
    if Color.query.count() == 0:
        colors = [
            Color(name="Black", code="#000000"),
            Color(name="Brown", code="#8B4513"),
            Color(name="White", code="#FFFFFF"),
            Color(name="Blue", code="#0000FF"),
            Color(name="Red", code="#FF0000"),
        ]

        db.session.add_all(colors)
        db.session.commit()
        print("✅ Colors seeded successfully")
    else:
        print("ℹ️ Colors already exist")


# =========================
# 🔹 SEED PRODUCTS
# =========================
def seed_products():
    products_data = [
        {
            "name": "GL Crossliner",
            "price": 699,
            "original_price": 1299,
            "discount_percent": 46,
            "rating": 4.5,
            "offer": "Limited Offer",
            "guarantee": "2-Year Assurance",
            "material": "100% Genuine Leather",
            "description": "Slightly glossy finish, crossing lines texture. Dual-Coated Finish, Signature Wrinkle-Free Strip, Feather-Light Comfort, Micro-Adjustable Precision, Precision Stitching, Rust-Resistant Hardware."
        },
        {
            "name": "GL Drill",
            "price": 699,
            "original_price": 1299,
            "discount_percent": 46,
            "rating": 4.4,
            "offer": "Hot Deal",
            "guarantee": "2-Year Assurance",
            "material": "100% Genuine Leather",
            "description": "Matt finish with carbon fiber design, decent modern look. Dual-Coated Finish, Signature Wrinkle-Free Strip, Feather-Light Comfort, Micro-Adjustable Precision, Precision Stitching, Rust-Resistant Hardware."
        },
        {
            "name": "GL Fortzila",
            "price": 699,
            "original_price": 1299,
            "discount_percent": 46,
            "rating": 4.6,
            "offer": "Best Seller",
            "guarantee": "2-Year Assurance",
            "material": "100% Genuine Leather",
            "description": "Dot texture all over belt, glossy formal premium look. Dual-Coated Finish, Signature Wrinkle-Free Strip, Feather-Light Comfort, Micro-Adjustable Precision, Precision Stitching, Rust-Resistant Hardware."
        }
    ]

    colors = Color.query.all()

    for p in products_data:
        existing = Product.query.filter_by(name=p["name"]).first()
        if existing:
            continue

        product = Product(**p)
        db.session.add(product)
        db.session.flush()  # get product id

        # attach all colors (Black + Brown etc.)
        for color in colors:
            db.session.add(ProductColor(
                product_id=product.id,
                color_id=color.id
            ))

    db.session.commit()
    print("✅ Products seeded successfully")

def seed_admin():
    admin_email = "admin@gmail.com"

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print("ℹ️ Admin already exists")
        return

    admin = User(
        username="admin",
        email=admin_email,
        password=generate_password_hash("admin123"),
        is_admin=True
    )

    db.session.add(admin)
    db.session.commit()
    print("✅ Admin created successfully")

# =========================
# 🔹 RUN SEED
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        seed_colors()
        seed_products()
        seed_admin()
        print("✅ All seed data inserted")