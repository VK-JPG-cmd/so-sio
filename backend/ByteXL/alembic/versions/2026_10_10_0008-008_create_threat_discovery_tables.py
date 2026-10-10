"""create threat discovery tables for external indicators and monitoring checkpoints

Revision ID: 008_threat_discovery
Revises: 007_official_brand_assets
Create Date: 2026-10-10 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_threat_discovery"
down_revision: Union[str, None] = "007_official_brand_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. discovery_checkpoints table
    op.create_table(
        "discovery_checkpoints",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("checkpoint_value", sa.String(length=255), nullable=True),
        sa.Column("last_poll_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("indicators_fetched_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("indicators_accepted_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("indicators_rejected_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("poll_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="IDLE", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_discovery_checkpoints_source_id", "discovery_checkpoints", ["source_id"])

    # 2. discovered_indicators table
    op.create_table(
        "discovered_indicators",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=True),
        sa.Column("indicator_type", sa.String(length=64), nullable=False),
        sa.Column("raw_indicator", sa.String(length=2048), nullable=False),
        sa.Column("canonical_value", sa.String(length=2048), nullable=False),
        sa.Column("source_first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_observed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(length=32), nullable=True),
        sa.Column(
            "threat_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_entities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campaign_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "alert_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("alerts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "evidence_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "source_id", "canonical_value", name="uq_discovered_indicator_source_canonical"
        ),
    )
    op.create_index("ix_discovered_indicators_source_id", "discovered_indicators", ["source_id"])
    op.create_index("ix_discovered_indicators_canonical", "discovered_indicators", ["canonical_value"])
    op.create_index("ix_discovered_indicators_status", "discovered_indicators", ["processing_status"])
    op.create_index("ix_discovered_indicators_brand_id", "discovered_indicators", ["brand_id"])
    op.create_index("ix_discovered_indicators_source_status", "discovered_indicators", ["source_id", "processing_status"])
    op.create_index("ix_discovered_indicators_source_record", "discovered_indicators", ["source_id", "source_record_id"])


def downgrade() -> None:
    op.drop_table("discovered_indicators")
    op.drop_table("discovery_checkpoints")
