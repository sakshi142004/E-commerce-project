"""add warranty detail fields

Revision ID: c9d3e7f1a2b4
Revises: b8f2c4d6e9a1
Create Date: 2026-05-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c9d3e7f1a2b4"
down_revision = "b8f2c4d6e9a1"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("warranty")}

    with op.batch_alter_table("warranty") as batch_op:
        if "order_id" not in columns:
            batch_op.add_column(sa.Column("order_id", sa.String(length=100), nullable=True))
        if "product_name" not in columns:
            batch_op.add_column(sa.Column("product_name", sa.String(length=255), nullable=True))
        if "purchase_date" not in columns:
            batch_op.add_column(sa.Column("purchase_date", sa.String(length=50), nullable=True))
        if "message" not in columns:
            batch_op.add_column(sa.Column("message", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("warranty") as batch_op:
        batch_op.drop_column("message")
        batch_op.drop_column("purchase_date")
        batch_op.drop_column("product_name")
        batch_op.drop_column("order_id")
