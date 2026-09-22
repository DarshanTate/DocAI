"""add job processing fields

Revision ID: b3d5c7c97d63
Revises: 6c46f33488cf
Create Date: 2026-09-22 14:06:10.698726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3d5c7c97d63"
down_revision: Union[str, Sequence[str], None] = "6c46f33488cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_jobs",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "processing_jobs",
        sa.Column(
            "max_retries",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
    )

    op.add_column(
        "processing_jobs",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "processing_jobs",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "processing_jobs",
        "completed_at",
    )

    op.drop_column(
        "processing_jobs",
        "started_at",
    )

    op.drop_column(
        "processing_jobs",
        "max_retries",
    )

    op.drop_column(
        "processing_jobs",
        "retry_count",
    )