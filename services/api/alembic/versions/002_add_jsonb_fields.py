"""
Add JSONB fields for enriched processing data

Revision ID: 002_add_jsonb_fields
Revises: 001_bubblegrade_ocr
Create Date: 2025-05-29 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_jsonb_fields'
down_revision = '001_bubblegrade_ocr'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add JSONB columns to scans table for regions, OCR data, and quality metrics"""
    op.add_column('scans', sa.Column('regions', postgresql.JSONB, nullable=True))
    op.add_column('scans', sa.Column('nombre', postgresql.JSONB, nullable=True))
    op.add_column('scans', sa.Column('curp', postgresql.JSONB, nullable=True))
    op.add_column('scans', sa.Column('image_quality', postgresql.JSONB, nullable=True))
    # Optionally index JSONB paths if needed
    # op.create_index('idx_scans_regions', 'scans', ['regions'], postgresql_using='gin')

def downgrade() -> None:
    """Remove JSONB columns from scans table"""
    op.drop_column('scans', 'image_quality')
    op.drop_column('scans', 'curp')
    op.drop_column('scans', 'nombre')
    op.drop_column('scans', 'regions')