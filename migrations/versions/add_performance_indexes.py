"""Add performance indexes for scholarship search

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-08-17 23:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes for improved query performance
    
    # Index on scholarship name for text searches
    op.create_index(
        'idx_scholarships_name_btree',
        'scholarships',
        ['name'],
        postgresql_using='btree'
    )
    
    # Index on application deadline for filtering and sorting
    op.create_index(
        'idx_scholarships_deadline_btree',
        'scholarships',
        ['application_deadline'],
        postgresql_using='btree'
    )
    
    # GIN index on eligibility criteria JSON for complex queries
    op.create_index(
        'idx_scholarships_criteria_gin',
        'scholarships',
        ['eligibility_criteria'],
        postgresql_using='gin'
    )
    
    # Index on scholarship type for filtering
    op.create_index(
        'idx_scholarships_type_btree',
        'scholarships',
        ['scholarship_type'],
        postgresql_using='btree'
    )
    
    # Index on amount for filtering and sorting
    op.create_index(
        'idx_scholarships_amount_btree',
        'scholarships',
        ['amount'],
        postgresql_using='btree'
    )
    
    # Composite index for common search patterns
    op.create_index(
        'idx_scholarships_type_deadline',
        'scholarships',
        ['scholarship_type', 'application_deadline'],
        postgresql_using='btree'
    )


def downgrade():
    # Drop indexes in reverse order
    op.drop_index('idx_scholarships_type_deadline', table_name='scholarships')
    op.drop_index('idx_scholarships_amount_btree', table_name='scholarships')
    op.drop_index('idx_scholarships_type_btree', table_name='scholarships')
    op.drop_index('idx_scholarships_criteria_gin', table_name='scholarships')
    op.drop_index('idx_scholarships_deadline_btree', table_name='scholarships')
    op.drop_index('idx_scholarships_name_btree', table_name='scholarships')