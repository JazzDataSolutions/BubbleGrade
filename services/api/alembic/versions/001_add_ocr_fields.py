"""Add OCR fields for BubbleGrade enhancement

Revision ID: 001_bubblegrade_ocr
Revises: base
Create Date: 2024-05-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_bubblegrade_ocr'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade database schema for BubbleGrade OCR capabilities"""
    
    # Create enum for scan status
    scan_status_enum = postgresql.ENUM(
        'QUEUED', 'PROCESSING', 'COMPLETED', 'ERROR', 'NEEDS_REVIEW',
        name='scan_status_enum'
    )
    scan_status_enum.create(op.get_bind())
    
    # Create processed_scans table (enhanced version of scans)
    op.create_table(
        'processed_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('status', scan_status_enum, nullable=False, default='QUEUED'),
        
        # OCR Results - Name
        sa.Column('nombre_value', sa.String(200), nullable=True),
        sa.Column('nombre_confidence', sa.Float, nullable=True),
        sa.Column('nombre_needs_review', sa.Boolean, default=False),
        sa.Column('nombre_corrected_by', sa.String(100), nullable=True),
        sa.Column('nombre_corrected_at', sa.DateTime(timezone=True), nullable=True),
        
        # OCR Results - CURP
        sa.Column('curp_value', sa.String(18), nullable=True),
        sa.Column('curp_confidence', sa.Float, nullable=True),
        sa.Column('curp_is_valid', sa.Boolean, default=False),
        sa.Column('curp_needs_review', sa.Boolean, default=False),
        sa.Column('curp_corrected_by', sa.String(100), nullable=True),
        sa.Column('curp_corrected_at', sa.DateTime(timezone=True), nullable=True),
        
        # OMR Results (existing functionality)
        sa.Column('score', sa.Integer, nullable=True),
        sa.Column('answers', postgresql.JSONB, nullable=True),
        sa.Column('total_questions', sa.Integer, nullable=True),
        
        # Processing metadata
        sa.Column('upload_time', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
        sa.Column('processed_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_time', sa.DateTime(timezone=True), nullable=True),
        
        # Image quality metrics
        sa.Column('image_quality', postgresql.JSONB, nullable=True),
        
        # Regional bounding boxes for UI editing
        sa.Column('regions', postgresql.JSONB, nullable=True),
        
        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('processing_attempts', sa.Integer, default=0),
        
        # File metadata
        sa.Column('file_hash', sa.String(64), nullable=True),  # SHA-256 for duplicate detection
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('image_dimensions', postgresql.JSONB, nullable=True),
        
        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for better query performance
    op.create_index('idx_processed_scans_status', 'processed_scans', ['status'])
    op.create_index('idx_processed_scans_upload_time', 'processed_scans', ['upload_time'])
    op.create_index('idx_processed_scans_filename', 'processed_scans', ['filename'])
    op.create_index('idx_processed_scans_file_hash', 'processed_scans', ['file_hash'])
    op.create_index('idx_processed_scans_needs_review', 'processed_scans', 
                   ['nombre_needs_review', 'curp_needs_review'])
    
    # Create exam templates table for answer keys and validation
    op.create_table(
        'exam_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('total_questions', sa.Integer, nullable=False),
        sa.Column('correct_answers', postgresql.JSONB, nullable=False),
        sa.Column('question_layout', postgresql.JSONB, nullable=True),  # Grid layout info
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add template relationship to processed_scans
    op.add_column('processed_scans', 
                 sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_processed_scans_template', 'processed_scans', 'exam_templates',
                         ['template_id'], ['id'], ondelete='SET NULL')
    
    # Create processing logs table for detailed audit trail
    op.create_table(
        'processing_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step', sa.String(50), nullable=False),  # 'upload', 'omr', 'ocr_nombre', etc.
        sa.Column('status', sa.String(20), nullable=False), # 'started', 'completed', 'failed'
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
    )
    
    op.create_foreign_key('fk_processing_logs_scan', 'processing_logs', 'processed_scans',
                         ['scan_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_processing_logs_scan_id', 'processing_logs', ['scan_id'])
    op.create_index('idx_processing_logs_timestamp', 'processing_logs', ['timestamp'])
    
    # Create user corrections table for tracking manual edits
    op.create_table(
        'user_corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(50), nullable=False),  # 'nombre', 'curp'
        sa.Column('original_value', sa.String(500), nullable=True),
        sa.Column('corrected_value', sa.String(500), nullable=False),
        sa.Column('original_confidence', sa.Float, nullable=True),
        sa.Column('correction_reason', sa.String(200), nullable=True),
        sa.Column('corrected_by', sa.String(100), nullable=False),
        sa.Column('corrected_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
    )
    
    op.create_foreign_key('fk_user_corrections_scan', 'user_corrections', 'processed_scans',
                         ['scan_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_user_corrections_scan_id', 'user_corrections', ['scan_id'])
    op.create_index('idx_user_corrections_field', 'user_corrections', ['field_name'])
    
    # Create performance metrics table for monitoring
    op.create_table(
        'performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_type', sa.String(50), nullable=False),  # 'ocr_latency', 'omr_accuracy', etc.
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), 
                 nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_performance_metrics_type', 'performance_metrics', ['metric_type'])
    op.create_index('idx_performance_metrics_recorded_at', 'performance_metrics', ['recorded_at'])

def downgrade() -> None:
    """Downgrade database schema"""
    
    # Drop tables in reverse order
    op.drop_table('performance_metrics')
    op.drop_table('user_corrections')
    op.drop_table('processing_logs')
    op.drop_table('exam_templates')
    op.drop_table('processed_scans')
    
    # Drop enum
    op.execute('DROP TYPE scan_status_enum')