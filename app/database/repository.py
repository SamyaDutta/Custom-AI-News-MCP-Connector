"""
Query layer sitting between the DB and everything else (collectors write
through here, MCP tools read through here). Kept thin on Day 1 — real
query methods (search_ai_news, get_ai_radar's underlying query, etc.)
get built out alongside the pipeline stages that need them on Days 2-5.

format_with_sources() (architecture doc §2.15) also lands here once
Content/Event rows actually exist to format.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Source


def get_or_create_source(
    session: Session, name: str, type_: str, url: str | None = None,
    category_hint: str | None = None, priority: int = 3,
) -> Source:
    existing = session.execute(
        select(Source).where(Source.name == name)
    ).scalar_one_or_none()
    if existing:
        return existing

    source = Source(
        name=name, type=type_, url=url,
        category_hint=category_hint, priority=priority,
    )
    session.add(source)
    session.flush()  # get the id without a full commit
    return source


def mark_source_checked(session: Session, source: Source, found_items: bool) -> None:
    """Updates the checkpoint used for incremental fetch, plus the
    feed-health tracking from architecture doc §2.13."""
    source.last_checked = dt.datetime.now(dt.timezone.utc)
    if found_items:
        source.consecutive_empty_runs = 0
        source.flagged_unhealthy = False
    else:
        source.consecutive_empty_runs += 1
        if source.consecutive_empty_runs >= 3:
            source.flagged_unhealthy = True
