import sqlalchemy as sa
from sqlalchemy.sql import func
from shared.database import metadata

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("username", sa.String(50), nullable=False, unique=True, index=True),
    sa.Column("email", sa.String(100), nullable=False, unique=True, index=True),
    sa.Column("password", sa.String(255), nullable=False),
    sa.Column("full_name", sa.String(100), nullable=True),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), default=func.now()),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now()),
)