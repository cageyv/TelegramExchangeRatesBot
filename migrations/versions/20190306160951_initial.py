"""initial

Revision ID: 20190306160951
Revises:
Create Date: 2019-03-06 16:09:51.510721

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20190306160951"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "chat_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("currencies", sa.Text(), nullable=False),
        sa.Column("cnt", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "updated", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chats",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=False),
        sa.Column("first_name", sa.Text(), nullable=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("is_subscribed", sa.Boolean(), nullable=False),
        sa.Column("is_console_mode", sa.Boolean(), nullable=False),
        sa.Column(
            "created", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("tag", sa.Text(), nullable=True),
        sa.Column(
            "created", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("chat_rates")
    # ### end Alembic commands ###
