"""Initial schema: users, plans, plan_versions, conversation_turns, agent_outputs, daily_spend.

Revision ID: 001
Revises:
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("clerk_user_id", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)

    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("idea_summary", sa.Text(), nullable=False),
        sa.Column("current_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_progress"),
        sa.Column("total_cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plans_user_id", "plans", ["user_id"])
    op.create_index("ix_plans_created_at", "plans", ["created_at"])

    op.create_table(
        "plan_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("version_num", sa.Integer(), nullable=False),
        sa.Column("full_plan_json", JSONType, nullable=False),
        sa.Column("red_team_json", JSONType, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "version_num", name="uq_plan_versions_plan_version"),
    )
    op.create_index("ix_plan_versions_plan_id", "plan_versions", ["plan_id"])

    op.create_foreign_key(
        "fk_plans_current_version",
        "plans",
        "plan_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("turn_idx", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("affected_phases", JSONType, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conv_turns_plan_idx", "conversation_turns", ["plan_id", "turn_idx"])

    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("plan_version_id", sa.Uuid(), nullable=True),
        sa.Column("phase_id", sa.String(length=32), nullable=False),
        sa.Column("output_json", JSONType, nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_version_id"], ["plan_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_outputs_plan_phase", "agent_outputs", ["plan_id", "phase_id"])

    op.create_table(
        "daily_spend",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("spend_date", sa.Date(), nullable=False),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_spend_spend_date", "daily_spend", ["spend_date"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_daily_spend_spend_date", table_name="daily_spend")
    op.drop_table("daily_spend")
    op.drop_index("ix_agent_outputs_plan_phase", table_name="agent_outputs")
    op.drop_table("agent_outputs")
    op.drop_index("ix_conv_turns_plan_idx", table_name="conversation_turns")
    op.drop_table("conversation_turns")
    op.drop_constraint("fk_plans_current_version", "plans", type_="foreignkey")
    op.drop_index("ix_plan_versions_plan_id", table_name="plan_versions")
    op.drop_table("plan_versions")
    op.drop_index("ix_plans_created_at", table_name="plans")
    op.drop_index("ix_plans_user_id", table_name="plans")
    op.drop_table("plans")
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_table("users")
