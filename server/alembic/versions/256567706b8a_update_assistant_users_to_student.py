"""update_assistant_users_to_student

Revision ID: 256567706b8a
Revises: 00fa352db6f0
Create Date: 2026-02-25 13:23:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '256567706b8a'
down_revision: Union[str, Sequence[str], None] = '00fa352db6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change any users with role='assistant' to role='student'."""
    op.execute(
        sa.text("UPDATE users SET role = 'student' WHERE role = 'assistant'")
    )


def downgrade() -> None:
    """No reliable way to reverse — users would need manual reassignment."""
    pass
