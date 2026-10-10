"""create official brand assets tables for social and mobile applications

Revision ID: 007_official_brand_assets
Revises: 006_brand_owner_portal_and_audit
Create Date: 2026-10-10 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "007_official_brand_assets"
down_revision: Union[str, None] = "006_brand_owner_portal_and_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. brand_social_assets table
    op.create_table(
        "brand_social_assets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("canonical_url", sa.String(length=512), nullable=False),
        sa.Column(
            "verification_status",
            sa.Enum("PENDING", "VERIFIED", "REJECTED", name="asset_verification_status_enum", native_enum=False),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("evidence", sa.String(length=1024), nullable=True),
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
        sa.UniqueConstraint("brand_id", "platform", "handle", name="uq_brand_social_asset_handle"),
    )
    op.create_index("ix_brand_social_assets_brand_id", "brand_social_assets", ["brand_id"])
    op.create_index(
        "ix_brand_social_assets_platform_handle", "brand_social_assets", ["platform", "handle"]
    )
    op.create_index(
        "ix_brand_social_assets_status", "brand_social_assets", ["verification_status"]
    )

    # 2. brand_mobile_apps table
    op.create_table(
        "brand_mobile_apps",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "brand_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("app_name", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("app_identifier", sa.String(length=255), nullable=False),
        sa.Column("publisher_name", sa.String(length=255), nullable=False),
        sa.Column("store_url", sa.String(length=512), nullable=False),
        sa.Column(
            "verification_status",
            sa.Enum("PENDING", "VERIFIED", "REJECTED", name="asset_verification_status_enum", native_enum=False),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("evidence", sa.String(length=1024), nullable=True),
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
        sa.UniqueConstraint(
            "brand_id", "platform", "app_identifier", name="uq_brand_mobile_app_identifier"
        ),
    )
    op.create_index("ix_brand_mobile_apps_brand_id", "brand_mobile_apps", ["brand_id"])
    op.create_index(
        "ix_brand_mobile_apps_platform_identifier",
        "brand_mobile_apps",
        ["platform", "app_identifier"],
    )
    op.create_index(
        "ix_brand_mobile_apps_status", "brand_mobile_apps", ["verification_status"]
    )


def downgrade() -> None:
    op.drop_table("brand_mobile_apps")
    op.drop_table("brand_social_assets")
