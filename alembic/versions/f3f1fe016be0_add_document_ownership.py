from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import UUID


# revision identifiers, used by Alembic.
revision: str = "f3f1fe016be0"
down_revision: Union[str, Sequence[str], None] = "b3d5c7c97d63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # 2. Create a temporary owner_id column.
    op.add_column(
        "documents",
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # 3. Create a default user for existing documents.
    default_user_id =UUID("00000000-0000-0000-0000-000000000001")

    op.execute(
        sa.text(
            """
            INSERT INTO users (
                id,
                email,
                password_hash,
                created_at
            )
            VALUES (
                '00000000-0000-0000-0000-000000000001'::uuid,
                'legacy@docai.local',
                'legacy-user-no-login',
                NOW()
            )
            """
        )
    )

    # 4. Assign all existing documents to that user.
    op.execute(
        sa.text(
            """
            UPDATE documents
            SET owner_id =
                '00000000-0000-0000-0000-000000000001'::uuid
            WHERE owner_id IS NULL
            """
        )
    )

    # 5. Now owner_id can safely become NOT NULL.
    op.alter_column(
        "documents",
        "owner_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    # 6. Add index.
    op.create_index(
        "ix_documents_owner_id",
        "documents",
        ["owner_id"],
        unique=False,
    )

    # 7. Add foreign key.
    op.create_foreign_key(
        "fk_documents_owner_id_users",
        "documents",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_documents_owner_id_users",
        "documents",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_documents_owner_id",
        table_name="documents",
    )

    op.drop_column(
        "documents",
        "owner_id",
    )

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_table("users")