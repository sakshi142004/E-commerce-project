"""add razorpay order fields

Revision ID: b8f2c4d6e9a1
Revises: 4f2b9c8d1e0a
Create Date: 2026-05-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "b8f2c4d6e9a1"
down_revision = "4f2b9c8d1e0a"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    order_item_columns = {column["name"] for column in inspector.get_columns("order_items")}

    with op.batch_alter_table("orders") as batch_op:
        if "razorpay_order_id" not in order_columns:
            batch_op.add_column(sa.Column("razorpay_order_id", sa.String(length=100), nullable=True))
        if "razorpay_payment_id" not in order_columns:
            batch_op.add_column(sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True))
        if "razorpay_signature" not in order_columns:
            batch_op.add_column(sa.Column("razorpay_signature", sa.String(length=255), nullable=True))
        if "payment_status" not in order_columns:
            batch_op.add_column(sa.Column("payment_status", sa.String(length=50), nullable=True, server_default="Pending"))
        if "order_status" not in order_columns:
            batch_op.add_column(sa.Column("order_status", sa.String(length=50), nullable=True, server_default="Pending"))
        if "paid_at" not in order_columns:
            batch_op.add_column(sa.Column("paid_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE orders SET order_status = status WHERE order_status IS NULL")
    op.execute("UPDATE orders SET payment_status = 'Pending' WHERE payment_status IS NULL")

    if "size_id" not in order_item_columns:
        with op.batch_alter_table("order_items") as batch_op:
            batch_op.add_column(sa.Column("size_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key("fk_order_items_size_id_product_sizes", "product_sizes", ["size_id"], ["id"])


def downgrade():
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.drop_constraint("fk_order_items_size_id_product_sizes", type_="foreignkey")
        batch_op.drop_column("size_id")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_column("paid_at")
        batch_op.drop_column("order_status")
        batch_op.drop_column("payment_status")
        batch_op.drop_column("razorpay_signature")
        batch_op.drop_column("razorpay_payment_id")
        batch_op.drop_column("razorpay_order_id")
