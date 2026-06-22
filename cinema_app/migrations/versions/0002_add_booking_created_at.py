"""add created_at to booking

Revision ID: 0002_add_booking_created_at
Revises: 5038af58d124
Create Date: 2026-06-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_booking_created_at'
down_revision = '5038af58d124'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'booking',
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
    )


def downgrade():
    op.drop_column('booking', 'created_at')
