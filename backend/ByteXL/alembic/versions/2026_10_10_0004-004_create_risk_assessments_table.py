"""create risk_assessments table

Revision ID: 004_risk_assessments
Revises: 003_reviews_and_threat_reports
Create Date: 2026-10-10 01:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_risk_assessments"
down_revision: Union[str, None] = "003_reviews_and_threat_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "report_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_reports.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("entity_id", sa.String(length=512), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column(
            "severity",
            sa.String(length=32),
            nullable=False,
            server_default="LOW",
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.Column("indicators_json", sa.JSON(), nullable=False),
        sa.Column("recommendation_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_risk_assessments_report_id",
        "risk_assessments",
        ["report_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_assessments_entity_id",
        "risk_assessments",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_assessments_severity",
        "risk_assessments",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_risk_assessments_created_at",
        "risk_assessments",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_risk_assessments_report_created",
        "risk_assessments",
        ["report_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_report_created", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_created_at", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_severity", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_entity_id", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_report_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
