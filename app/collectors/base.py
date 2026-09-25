"""
Every collector (arxiv, github, huggingface, rss, hackernews, reddit,
papers_with_code, semantic_scholar — built out on Day 2) implements this
same interface, so the ingestion pipeline (scripts/ingest.py) never needs
source-specific branching outside app/collectors/.

architecture doc §2.3
"""
from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.database.models import ContentType


@dataclass
class RawItem:
    """Whatever a source's API/feed hands back, before normalization.
    Fields are intentionally loose — each collector fills what its
    source actually provides."""
    title: str
    url: str
    published_at: dt.datetime
    raw_payload: dict = field(default_factory=dict)  # full original response, for debugging


@dataclass
class ContentRow:
    """Canonical shape every collector's normalize() must produce —
    matches the `content` table columns that collectors are responsible
    for filling in (relevance_score, category, embedding, event_id are
    filled later by processing/, not by collectors)."""
    title: str
    url: str
    content_type: ContentType
    published_at: dt.datetime
    raw_text: str  # title + truncated abstract/description — used for
                    # extractive summaries AND the §2.16 grounding check
    author: str | None = None


class Collector(ABC):
    source_name: str
    source_priority: int = 3  # 1-5, §2.6 source_quality term

    @abstractmethod
    def fetch_since(self, checkpoint: dt.datetime | None) -> list[RawItem]:
        """Return raw items newer than checkpoint (None on first run —
        implementations should apply a sane default lookback window).

        Must NOT raise on partial/total failure — log and return an
        empty list so one dead source can't take down the pipeline
        (architecture doc §2.10, §2.13)."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: RawItem) -> ContentRow:
        """Map source-specific fields to the canonical ContentRow shape."""
        raise NotImplementedError
