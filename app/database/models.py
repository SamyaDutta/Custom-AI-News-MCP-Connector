"""
SQLAlchemy models — matches architecture doc §2.2 (schema), extended with
verification_status (§2.16) and llm_usage (§2.14/§2.17).
"""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class VerificationStatus(str, enum.Enum):
    """architecture doc §2.16"""
    UNPROCESSED = "unprocessed"        # not yet through the summarizer
    VERIFIED = "verified"              # LLM summary passed both checks
    FLAGGED = "flagged"                # LLM summary failed a check -> extractive served
    EXTRACTIVE = "extractive"          # never eligible for LLM summary (past daily cap)
    PENDING_LLM_SUMMARY = "pending_llm_summary"  # fell back due to quota, retry next run (§2.17)


class ContentType(str, enum.Enum):
    PAPER = "paper"
    REPO_RELEASE = "repo_release"
    MODEL = "model"
    ARTICLE = "article"
    DISCUSSION = "discussion"


class Source(Base):
    """Registry of every feed/API being polled — architecture doc §2.2"""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # "api" | "rss"
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    category_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5, §2.6 source_quality
    last_checked: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # health tracking, §2.13 feed health check
    consecutive_empty_runs: Mapped[int] = mapped_column(Integer, default=0)
    flagged_unhealthy: Mapped[bool] = mapped_column(Boolean, default=False)

    contents: Mapped[list["Content"]] = relationship(back_populates="source_obj")


class Event(Base):
    """Deduplicated cluster — one real-world event, many sources. §2.2 / §2.4"""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_content_id: Mapped[int | None] = mapped_column(
        ForeignKey("content.id"), nullable=True
    )
    first_seen: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    importance: Mapped[float] = mapped_column(Float, default=0.0)

    # event-level summary, generated once and shared across all clustered
    # content rows — architecture doc §2.14 ("summarize at the event level")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNPROCESSED
    )
    unsupported_claims: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list, §2.16 audit trail

    items: Mapped[list["Content"]] = relationship(
        back_populates="event", foreign_keys="Content.event_id"
    )


class Content(Base):
    """Every individual item collected — architecture doc §2.2"""
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # title + truncated abstract, kept for §2.16 grounding checks
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # extractive, always computed (§2.7)
    published_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[bytes | None] = mapped_column(nullable=True)  # serialized vector, §2.4
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    popularity_signal: Mapped[float] = mapped_column(Float, default=0.0)  # stars delta / points / upvotes, normalized
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source_obj: Mapped["Source"] = relationship(back_populates="contents")
    event: Mapped["Event | None"] = relationship(back_populates="items", foreign_keys=[event_id])


class TrackedTopic(Base):
    """Personalization stub — architecture doc §2.2 / §2.8 get_learning_recommendations"""
    __tablename__ = "tracked_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LLMUsage(Base):
    """Daily usage ledger checked before every summarizer call — §2.14 / §2.17"""
    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # "groq" | "gemini" | "local"
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
