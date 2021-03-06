"""remove unnecessary uuid columns from user_artist and user_release tables

Revision ID: 339c0e295c93
Revises: b44e10c1f032
Create Date: 2019-02-21 00:59:56.032617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '339c0e295c93'
down_revision = 'b44e10c1f032'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_artist_uuid', table_name='user_artist')
    op.drop_column('user_artist', 'uuid')
    op.drop_index('ix_user_release_uuid', table_name='user_release')
    op.drop_column('user_release', 'uuid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_release', sa.Column('uuid', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_index('ix_user_release_uuid', 'user_release', ['uuid'], unique=True)
    op.add_column('user_artist', sa.Column('uuid', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_index('ix_user_artist_uuid', 'user_artist', ['uuid'], unique=True)
    # ### end Alembic commands ###
