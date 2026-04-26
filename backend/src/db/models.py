"""SQLAlchemy 2.x ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    CHAR,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    - Postgres: native UUID
    - SQLite: stores UUID as CHAR(36)
    """

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: sa.Dialect):  # type: ignore[name-defined]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    clerk_user_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} clerk_user_id={self.clerk_user_id}>"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    idea_summary: Mapped[str] = mapped_column(Text, nullable=False)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey(
            "plan_versions.id",
            use_alter=True,
            name="fk_plans_current_version",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="in_progress"
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} title={self.title!r} status={self.status}>"


Index("ix_plans_created_at", Plan.created_at.desc())


class PlanVersion(Base):
    __tablename__ = "plan_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    full_plan_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    red_team_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "plan_id", "version_num", name="uq_plan_versions_plan_version"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PlanVersion id={self.id} plan_id={self.plan_id} "
            f"version_num={self.version_num}>"
        )


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    affected_phases: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationTurn id={self.id} plan_id={self.plan_id} "
            f"turn_idx={self.turn_idx} role={self.role}>"
        )


Index(
    "ix_conv_turns_plan_idx",
    ConversationTurn.plan_id,
    ConversationTurn.turn_idx,
)


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("plan_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    phase_id: Mapped[str] = mapped_column(String(32), nullable=False)
    output_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, default=Decimal("0")
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AgentOutput id={self.id} plan_id={self.plan_id} "
            f"phase_id={self.phase_id} model={self.model}>"
        )


Index(
    "ix_agent_outputs_plan_phase",
    AgentOutput.plan_id,
    AgentOutput.phase_id,
)


class DailySpend(Base):
    __tablename__ = "daily_spend"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    spend_date: Mapped[date] = mapped_column(
        Date, unique=True, index=True, nullable=False
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, default=Decimal("0")
    )
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<DailySpend id={self.id} spend_date={self.spend_date} "
            f"total_cost_usd={self.total_cost_usd}>"
        )
