"""create threat_entities, entity_relationships, campaigns, campaign_memberships, and alerts tables

Revision ID: 005_threat_intel_and_campaigns
Revises: 004_risk_assessments
Create Date: 2026-10-10 01:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_threat_intel_and_campaigns"
down_revision: Union[str, None] = "004_risk_assessments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. threat_entities table
    op.create_table(
        "threat_entities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_value", sa.String(length=2048), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("entity_type", "canonical_value", name="uq_threat_entity_type_canonical"),
    )
    op.create_index("ix_threat_entities_type", "threat_entities", ["entity_type"])
    op.create_index("ix_threat_entities_canonical", "threat_entities", ["canonical_value"])
    op.create_index("ix_threat_entities_type_last_seen", "threat_entities", ["entity_type", "last_seen_at"])

    # 2. entity_relationships table
    op.create_table(
        "entity_relationships",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "source_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("relationship_status", sa.String(length=32), server_default="CANDIDATE", nullable=False),
        sa.Column(
            "evidence_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evidences.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_entity_id",
            "target_entity_id",
            "relationship_type",
            name="uq_entity_relationship_source_target_type",
        ),
    )
    op.create_index("ix_entity_relationships_source_id", "entity_relationships", ["source_entity_id"])
    op.create_index("ix_entity_relationships_target_id", "entity_relationships", ["target_entity_id"])
    op.create_index("ix_entity_relationships_source_status", "entity_relationships", ["source_entity_id", "relationship_status"])

    # 3. campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
        sa.Column("risk_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_campaigns_brand_status", "campaigns", ["brand_id", "status"])
    op.create_index("ix_campaigns_brand_created", "campaigns", ["brand_id", "created_at"])

    # 4. campaign_memberships table
    op.create_table(
        "campaign_memberships",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "campaign_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("threat_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_reason", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("campaign_id", "entity_id", name="uq_campaign_membership_campaign_entity"),
    )
    op.create_index("ix_campaign_memberships_campaign_id", "campaign_memberships", ["campaign_id"])
    op.create_index("ix_campaign_memberships_entity_id", "campaign_memberships", ["entity_id"])

    # 5. alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(length=32), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("dedup_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_alerts_brand_fingerprint_status", "alerts", ["brand_id", "dedup_fingerprint", "status"])
    op.create_index("ix_alerts_brand_created", "alerts", ["brand_id", "created_at"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("campaign_memberships")
    op.drop_table("campaigns")
    op.drop_table("entity_relationships")
    op.drop_table("threat_entities")
