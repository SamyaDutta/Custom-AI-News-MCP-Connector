# AI Tech Radar

A personal MCP server that aggregates AI/ML/data-engineering developments
from free public sources into a ranked, deduplicated, categorized feed,
served to Claude as a single custom connector.

Full system design: see `docs/architecture.md` (or the doc shared alongside
this repo) for the HLD/LLD this code follows section-by-section.

**Build status:** Day 1 complete — repo skeleton, DB schema, config
loading, collector interface. Days 2-7 land incrementally.

---

## Day 1 setup (do this now, in VS Code)

**1. Open the folder in VS Code**, then open a terminal (`` Ctrl+` ``).

**2. Create and activate a virtual environment:**

```bash
python3 -m venv .venv

# macOS/Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

VS Code should prompt you to select this as the interpreter — say yes
(or `Ctrl+Shift+P` → "Python: Select Interpreter" → pick `.venv`).

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

Note: `sentence-transformers` pulls in `torch`, so this install is a few
hundred MB and can take a couple of minutes — that's expected, and it's
only needed starting Day 3 (dedup/classification), not for today's check.

**4. Set up your environment file:**

```bash
cp .env.example .env
```

Day 1 doesn't strictly require any keys filled in yet (the DB check below
runs with zero credentials), but it's worth creating your GitHub PAT now
since Day 2 needs it immediately — see the comments in `.env.example`.
Everything else (arXiv, Hugging Face, RSS, Hacker News, Papers With Code)
needs no credentials at all.

**5. Run the Day 1 verification script:**

```bash
python scripts/init_db.py
```

Expected output:
```
Using database: sqlite:////.../data/ai_tech_radar.db
Tables created (or already existed).
Seeded/confirmed 11 sources.

Day 1 check complete. ...
```

**6. Confirm it actually worked** — open `data/ai_tech_radar.db` with the
[SQLite Viewer VS Code extension](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer)
(or any SQLite tool) and check the `sources` table has 11 rows across
`rss` and `api` types.

If all of that matches, Day 1 is solid and Day 2 (the actual collectors)
builds directly on top of this.

---

## Project structure

```
ai-tech-radar/
├── app/
│   ├── config.py              # central config — .env + YAML loader
│   ├── database/
│   │   ├── models.py          # SQLAlchemy schema
│   │   ├── connection.py      # engine/session/init_db()
│   │   └── repository.py      # query layer (expands Day 2-5)
│   ├── collectors/
│   │   └── base.py            # Collector interface every source implements
│   ├── processing/            # dedup, classify, rank, summarize (Day 3-4)
│   └── mcp/                   # MCP server, tools, resources, prompts (Day 5)
├── config/
│   ├── sources.yaml           # every RSS feed + API source + GitHub watchlist
│   └── categories.yaml        # 8 categories + keyword rules
├── scripts/
│   └── init_db.py             # Day 1 verification script
└── .github/workflows/         # ingestion cron (Day 4)
```

## Uploading to GitHub

Once you're happy with Day 1 (or whenever you want to push):

```bash
git init
git add .
git commit -m "Day 1: repo skeleton, DB schema, config"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

`.gitignore` already excludes `.env` and the local `data/*.db` file, so
neither your secrets nor your local database get pushed.
