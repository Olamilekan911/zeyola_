"""empty message

Revision ID: 063db99d31e0
Revises: f008815cec05
Create Date: 2024-12-29 16:39:59.348105

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '063db99d31e0'
down_revision = 'f008815cec05'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), nullable=False))
        batch_op.drop_constraint('product_ibfk_1', type_='foreignkey')
        batch_op.create_foreign_key(None, 'customer', ['id'], ['id'])
        batch_op.drop_column('customer_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('product_ibfk_1', 'customer', ['customer_id'], ['id'])
        batch_op.drop_column('id')

    # ### end Alembic commands ###