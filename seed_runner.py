from app import app
from seed import seed_colors, seed_products, seed_admin
from models import db

with app.app_context():
    db.create_all()
    seed_colors()
    seed_products()
    seed_admin()
    print("✅ ALL SEEDED SUCCESSFULLY")