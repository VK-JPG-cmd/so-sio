"""create brand tables: brand_applications, domain_challenges, brands, brand_assets

Revision ID: 002_brand_tables
Revises: 001_auth_tables
Create Date: 2026-10-10 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_brand_tables"
down_revision: Union[str, None] = "001_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create brand_applications table
    op.create_table(
        "brand_applications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("official_domain", sa.String(length=255), nullable=False),
        sa.Column(
            "application_status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING_DOMAIN_VERIFICATION",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brand_applications_owner_user_id", "brand_applications", ["owner_user_id"])
    op.create_index("ix_brand_applications_official_domain", "brand_applications", ["official_domain"])
    op.create_index("ix_brand_applications_application_status", "brand_applications", ["application_status"])
    op.create_index("ix_brand_apps_owner_status", "brand_applications", ["owner_user_id", "application_status"])
    op.create_index("ix_brand_apps_domain", "brand_applications", ["official_domain"])

    # 2. Create domain_challenges table
    op.create_table(
        "domain_challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "application_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brand_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("challenge_hash", sa.String(length=64), nullable=False),
        sa.Column("record_host", sa.String(length=255), nullable=False),
        sa.Column("attempts_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_domain_challenges_application_id", "domain_challenges", ["application_id"])
    op.create_index("ix_domain_challenges_challenge_hash", "domain_challenges", ["challenge_hash"])
    op.create_index("ix_challenges_app_created", "domain_challenges", ["application_id", "created_at"])

    # 3. Create brands table
    op.create_table(
        "brands",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "application_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brand_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("official_domain", sa.String(length=255), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(length=32),
            nullable=False,
            server_default="VERIFIED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brands_application_id", "brands", ["application_id"], unique=True)
    op.create_index("ix_brands_owner_user_id", "brands", ["owner_user_id"])
    op.create_index("ix_brands_official_domain", "brands", ["official_domain"], unique=True)
    op.create_index("ix_brands_verification_status", "brands", ["verification_status"])
    op.create_index("ix_brands_status_domain", "brands", ["verification_status", "official_domain"])

    # 4. Create brand_assets table
    op.create_table(
        "brand_assets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brand_assets_brand_id", "brand_assets", ["brand_id"])
    op.create_index("ix_brand_assets_asset_type", "brand_assets", ["asset_type"])
    op.create_index("ix_brand_assets_storage_key", "brand_assets", ["storage_key"], unique=True)
    op.create_index("ix_brand_assets_content_hash", "brand_assets", ["content_hash"])
    op.create_index("ix_brand_assets_brand_type", "brand_assets", ["brand_id", "asset_type"])


def downgrade() -> None:
    op.drop_table("brand_assets")
    op.drop_table("brands")
    op.drop_table("domain_challenges")
    op.drop_table("brand_applications")
