from app import app
from models import db, Color, Product, ProductColor, ProductImage, User
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

    # ✅ Placeholder images - Cloudinary ya koi bhi public image URL
    placeholder_images = {
        "Black": "https://via.placeholder.com/400x400/000000/FFFFFF?text=Black+Belt",
        "Brown": "https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Brown+Belt",
        "White": "https://via.placeholder.com/400x400/CCCCCC/000000?text=White+Belt",
        "Blue":  "https://via.placeholder.com/400x400/0000FF/FFFFFF?text=Blue+Belt",
        "Red":   "https://via.placeholder.com/400x400/FF0000/FFFFFF?text=Red+Belt",
    }

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

    for p_data in products_data:
        product = Product(**p_data)
        db.session.add(product)
        db.session.flush()  # ID mil jaye

        first_image = True

        for c in colors:
            # ✅ Color relation add karo
            db.session.add(ProductColor(
                product_id=product.id,
                color_id=c.id
            ))

            # ✅ Har color ke liye image add karo
            image_url = placeholder_images.get(c.name, 
                "https://via.placeholder.com/400x400/888888/FFFFFF?text=Belt"
            )

            db.session.add(ProductImage(
                product_id=product.id,
                image_url=image_url,
                color_id=c.id,
                is_primary=first_image  # pehli image primary
            ))

            first_image = False

    db.session.commit()
    print("✅ Products seeded with images")


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
    with app.app_context():
        db.create_all()
        seed_colors()
        seed_products()
        seed_admin()
        print("🚀 ALL DATA SEEDED SUCCESSFULLY")