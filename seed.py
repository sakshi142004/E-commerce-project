from app import app
from models import db, Color, Product, ProductColor, User
from werkzeug.security import generate_password_hash


# COLORS
def seed_colors():
    if Color.query.first():
        print("ℹ️ Colors already exist")
        return

    colors = [
        Color(name="Black", code="#000000"),
        Color(name="Brown", code="#8B4513"),
        Color(name="White", code="#FFFFFF"),
        Color(name="Blue", code="#0000FF"),
        Color(name="Red", code="#FF0000"),
    ]

    db.session.add_all(colors)
    db.session.commit()
    print("✅ Colors seeded")


# PRODUCTS
def seed_products():
    if Product.query.first():
        print("ℹ️ Products already exist")
        return

    products = [
        {
            "name": "GL Crossliner",
            "price": 699,
            "original_price": 1299,
            "discount_percent": 46,
            "rating": 4.5,
            "offer": "Limited Offer",
            "guarantee": "2-Year Assurance",
            "material": "100% Genuine Leather",
            "description": "Crossing lines texture, glossy finish..."
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
            "description": "Matt carbon fiber design..."
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
            "description": "Dot texture premium formal look..."
        }
    ]

    colors = Color.query.all()

    for p in products:
        product = Product(**p)
        db.session.add(product)
        db.session.flush()

        for c in colors:
            db.session.add(ProductColor(
                product_id=product.id,
                color_id=c.id
            ))

    db.session.commit()
    print("✅ Products seeded")


# ADMIN
def seed_admin():
    if User.query.filter_by(email="admin@gmail.com").first():
        print("ℹ️ Admin already exists")
        return

    admin = User(
        username="admin",
        email="admin@gmail.com",
        password=generate_password_hash("admin123"),
        is_admin=True
    )

    db.session.add(admin)
    db.session.commit()
    print("✅ Admin created")


# RUN ALL
if __name__ == "__main__":
    with app.app_context():   # 🔥 IMPORTANT FIX
        db.create_all()

        seed_colors()
        seed_products()
        seed_admin()

        print("🚀 ALL DATA SEEDED SUCCESSFULLY")