"""add order tracking fields

Revision ID: d4e5f6a7b8c9
Revises: c9d3e7f1a2b4
Create Date: 2026-05-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c9d3e7f1a2b4"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("orders")}

    with op.batch_alter_table("orders") as batch_op:
        if "courier_partner" not in columns:
            batch_op.add_column(sa.Column("courier_partner", sa.String(length=100), nullable=True))
        if "tracking_url" not in columns:
            batch_op.add_column(sa.Column("tracking_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_column("tracking_url")
        batch_op.drop_column("courier_partner")
