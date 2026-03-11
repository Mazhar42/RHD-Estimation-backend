"""change_no_of_units_to_numeric

Revision ID: 1a41bf5af789
Revises: 002_add_performance_indexes
Create Date: 2026-03-11 18:43:41.452262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a41bf5af789'
down_revision: Union[str, None] = '002_add_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change no_of_units from Integer to Numeric(15, 3) to allow fractional units and prevent overflow
    op.alter_column('estimation_lines', 'no_of_units',
               existing_type=sa.Integer(),
               type_=sa.Numeric(15, 3),
               existing_nullable=True,
               postgresql_using='no_of_units::numeric(15,3)')
    
    # Also update special_item_requests table
    op.alter_column('special_item_requests', 'no_of_units',
               existing_type=sa.Integer(),
               type_=sa.Numeric(15, 3),
               existing_nullable=True,
               postgresql_using='no_of_units::numeric(15,3)')


def downgrade() -> None:
    # Revert back to Integer (Warning: This may fail if data contains decimals)
    op.alter_column('estimation_lines', 'no_of_units',
               existing_type=sa.Numeric(15, 3),
               type_=sa.Integer(),
               existing_nullable=True,
               postgresql_using='no_of_units::integer')
               
    op.alter_column('special_item_requests', 'no_of_units',
               existing_type=sa.Numeric(15, 3),
               type_=sa.Integer(),
               existing_nullable=True,
               postgresql_using='no_of_units::integer')
