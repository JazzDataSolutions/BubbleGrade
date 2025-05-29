"""
Add explicit 'name' and 'curp_value' columns to scans table

Revision ID: 003_add_name_curp_columns
Revises: 002_add_jsonb_fields
Create Date: 2025-05-29 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_name_curp_columns'
down_revision = '002_add_jsonb_fields'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add name and curp_value columns to scans table"""
    op.add_column('scans', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('scans', sa.Column('curp_value', sa.String(length=18), nullable=True))
    op.create_index('idx_scans_name', 'scans', ['name'])
    op.create_index('idx_scans_curp_value', 'scans', ['curp_value'])

def downgrade() -> None:
    """Remove name and curp_value columns from scans table"""
    op.drop_index('idx_scans_curp_value', table_name='scans')
    op.drop_index('idx_scans_name', table_name='scans')
    op.drop_column('scans', 'curp_value')
    op.drop_column('scans', 'name')