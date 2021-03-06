"""make user_artist_uuid nullable on user_release table

Revision ID: 57dd1d5b6c9f
Revises: 322f5709da9f
Create Date: 2019-02-03 19:37:37.529996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57dd1d5b6c9f'
down_revision = '322f5709da9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_release', 'user_artist_uuid',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_release', 'user_artist_uuid',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
