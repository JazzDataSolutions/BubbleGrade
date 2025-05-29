"""Add exam_id column and unique constraint on exam_id + curp_value in scans table

Revision ID: 004_add_exam_id_and_unique_constraint
Revises: 003_add_name_curp_columns
Create Date: 2025-05-29 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_exam_id_and_unique_constraint'
down_revision = '003_add_name_curp_columns'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'scans',
        sa.Column('exam_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_scans_exam_id_exam_templates',
        'scans', 'exam_templates',
        ['exam_id'], ['id'], ondelete='SET NULL'
    )
    op.create_unique_constraint(
        'uq_scans_exam_id_curp_value',
        'scans', ['exam_id', 'curp_value']
    )

def downgrade() -> None:
    op.drop_constraint('uq_scans_exam_id_curp_value', 'scans', type_='unique')
    op.drop_constraint('fk_scans_exam_id_exam_templates', 'scans', type_='foreignkey')
    op.drop_column('scans', 'exam_id')