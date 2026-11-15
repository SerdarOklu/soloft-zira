# ruff: noqa: E501, UP007, I001
"""passwordless farmer sign-in: user phone and login tokens

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-15 17:30:00.000000

"""

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=False)
    op.create_table(
        "login_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_login_tokens_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_login_tokens_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_tokens")),
    )
    op.create_index(op.f("ix_login_tokens_secret_hash"), "login_tokens", ["secret_hash"], unique=False)
    op.create_index(op.f("ix_login_tokens_user_id"), "login_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_login_tokens_user_id"), table_name="login_tokens")
    op.drop_index(op.f("ix_login_tokens_secret_hash"), table_name="login_tokens")
    op.drop_table("login_tokens")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_column("users", "phone")
