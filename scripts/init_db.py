"""
Day 1 verification script. Run this after `pip install -r requirements.txt`
to confirm the schema and config load correctly:

    python scripts/init_db.py

It creates all tables (idempotent — safe to re-run) and seeds the
`sources` table from config/sources.yaml, so you end Day 1 with a real,
inspectable database rather than just files that haven't been run yet.
"""
from __future__ import annotations

import sys
from pathlib import Path

# allow running as `python scripts/init_db.py` from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_sources_config, settings
from app.database.connection import get_session, init_db
from app.database.repository import get_or_create_source


def seed_sources() -> None:
    config = load_sources_config()

    with get_session() as session:
        count = 0
        for rss in config.get("rss_sources", []):
            get_or_create_source(
                session, name=rss["name"], type_="rss", url=rss["url"],
                category_hint=rss.get("category_hint"),
                priority=rss.get("priority", 3),
            )
            count += 1

        # Non-RSS sources (arXiv, GitHub, Hugging Face, HN, Papers With
        # Code) are registered here too, even though their collectors
        # land on Day 2 — this way `sources` reflects every feed/API in
        # the design from Day 1, not just RSS. Reddit and Semantic
        # Scholar were dropped from the design — both required an
        # account/API verification step neither of us wanted to chase.
        api_sources = [
            ("arXiv", 5),
            ("GitHub", 5),
            ("Hugging Face", 5),
            ("Hacker News", 3),
            ("Papers With Code", 3),
        ]
        for name, priority in api_sources:
            get_or_create_source(session, name=name, type_="api", priority=priority)
            count += 1

        print(f"Seeded/confirmed {count} sources.")


def main() -> None:
    print(f"Using database: {settings.DATABASE_URL}")
    init_db()
    print("Tables created (or already existed).")
    seed_sources()
    print("\nDay 1 check complete. Open the DB file in a SQLite viewer "
          "(or run the query below) to confirm the sources table is populated.")


if __name__ == "__main__":
    main()
