"""add_bx_in_tx_exchange

Revision ID: 20190326083625
Revises: 20190326060130
Create Date: 2019-03-26 08:36:25.229520

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session


class BxInThExchange:
    name = "[bx.in.th](https://bx.in.th/ref/s9c3HU/)"


# revision identifiers, used by Alembic.
revision = "20190326083625"
down_revision = "20190326060130"
branch_labels = None
depends_on = None

Base = declarative_base()


class Exchange(Base):
    __tablename__ = "exchanges"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, nullable=False, index=True)
    weight = sa.Column(sa.Integer, nullable=False)
    is_active = sa.Column(sa.Boolean, nullable=False)


def upgrade():
    session = Session(bind=op.get_bind())
    session.add(Exchange(name=BxInThExchange.name, is_active=True, weight=15))
    session.flush()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
