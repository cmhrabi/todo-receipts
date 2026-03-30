# Todo Receipt Printer

A Raspberry Pi + thermal printer project that watches a Notion database and prints a little receipt every time a new todo is added. Currently runs on Mac with console output; hardware printing comes in Phase 2.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- A Notion integration token and database ID

## Quick Start

```bash
uv sync
cp .env.example .env
# Edit .env with your Notion API key and database ID
uv run python main.py
```

## Notion Setup

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) and create a new integration.
2. Copy the integration token into your `.env` as `NOTION_API_KEY`.
3. Open your todo database in Notion, click the `...` menu, and select "Connect to" your integration.
4. Copy the database ID from the URL (the 32-character hex string after the workspace name) into your `.env` as `NOTION_DATABASE_ID`.

The poller looks for `Status` and `Priority` properties (select or status type) on your database pages. These are optional — receipts will still print without them.

## How It Works

The app polls your Notion database every 15 seconds (configurable via `POLL_INTERVAL_SECONDS`). On first run, it saves the most recent item as a starting point without printing anything. After that, any new todos trigger a formatted receipt printed to your terminal.

State is persisted in `.last_seen.json`, so restarting won't reprint old items.
