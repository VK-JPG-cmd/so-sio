"""create reviews, threat_reports, and evidences tables

Revision ID: 003_reviews_and_threat_reports
Revises: 002_brand_tables
Create Date: 2026-10-10 00:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_reviews_and_threat_reports"
down_revision: Union[str, None] = "002_brand_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create reviews table
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING_MODERATION",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
    )
    op.create_index("ix_reviews_brand_id", "reviews", ["brand_id"])
    op.create_index("ix_reviews_customer_id", "reviews", ["customer_id"])
    op.create_index("ix_reviews_status", "reviews", ["status"])
    op.create_index("ix_reviews_brand_status", "reviews", ["brand_id", "status"])
    op.create_index("ix_reviews_customer_created", "reviews", ["customer_id", "created_at"])

    # 2. Create threat_reports table
    op.create_table(
        "threat_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "reporter_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_value", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="SUBMITTED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_threat_reports_reporter_id", "threat_reports", ["reporter_id"])
    op.create_index("ix_threat_reports_brand_id", "threat_reports", ["brand_id"])
    op.create_index("ix_threat_reports_target_type", "threat_reports", ["target_type"])
    op.create_index("ix_threat_reports_status", "threat_reports", ["status"])
    op.create_index("ix_threat_reports_reporter_created", "threat_reports", ["reporter_id", "created_at"])
    op.create_index("ix_threat_reports_status_target", "threat_reports", ["status", "target_type"])

    # 3. Create evidences table
    op.create_table(
        "evidences",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "report_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=512), unique=True, nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidences_report_id", "evidences", ["report_id"])
    op.create_index("ix_evidences_storage_key", "evidences", ["storage_key"])
    op.create_index("ix_evidences_sha256", "evidences", ["sha256"])
    op.create_index("ix_evidences_report_created", "evidences", ["report_id", "created_at"])


def downgrade() -> None:
    # Drop evidences
    op.drop_index("ix_evidences_report_created", table_name="evidences")
    op.drop_index("ix_evidences_sha256", table_name="evidences")
    op.drop_index("ix_evidences_storage_key", table_name="evidences")
    op.drop_index("ix_evidences_report_id", table_name="evidences")
    op.drop_table("evidences")

    # Drop threat_reports
    op.drop_index("ix_threat_reports_status_target", table_name="threat_reports")
    op.drop_index("ix_threat_reports_reporter_created", table_name="threat_reports")
    op.drop_index("ix_threat_reports_status", table_name="threat_reports")
    op.drop_index("ix_threat_reports_target_type", table_name="threat_reports")
    op.drop_index("ix_threat_reports_brand_id", table_name="threat_reports")
    op.drop_index("ix_threat_reports_reporter_id", table_name="threat_reports")
    op.drop_table("threat_reports")

    # Drop reviews
    op.drop_index("ix_reviews_customer_created", table_name="reviews")
    op.drop_index("ix_reviews_brand_status", table_name="reviews")
    op.drop_index("ix_reviews_status", table_name="reviews")
    op.drop_index("ix_reviews_customer_id", table_name="reviews")
    op.drop_index("ix_reviews_brand_id", table_name="reviews")
    op.drop_table("reviews")
