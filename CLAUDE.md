# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Notion-to-thermal-printer bridge: polls a Notion database for new todos and prints formatted receipts. Currently supports console output; thermal printer support via `python-escpos` is planned.

## Commands

```bash
uv sync                        # install dependencies
uv sync --extra hardware       # install with thermal printer support
uv run python main.py          # start the polling loop
```

No test suite exists yet.

## Architecture

The app is a polling loop (`main.py`) with four supporting modules:

- **`config.py`** — reads all settings from `.env` via `python-dotenv`. Exits immediately if Notion credentials are missing.
- **`notion_client.py`** — Notion API client. Queries the database for recent pages and extracts title/status/priority.
- **`formatter.py`** — renders an item dict into a fixed-width (32-char) receipt string with word-wrapped title and metadata.
- **`state.py`** — persists processed page IDs and a `last_created_time` cursor to `.last_seen.json` for deduplication and incremental polling.
- **`printers/`** — strategy pattern: `BasePrinter` ABC with `ConsolePrinter` (always available) and a lazily-imported `ThermalPrinter`. `get_printer()` in `__init__.py` is the factory.

## Key Details

- Requires Python 3.14+ (see `pyproject.toml`).
- New printer backends: subclass `BasePrinter`, add a branch in `printers/__init__.py:get_printer()`.
- Notion properties `Status` and `Priority` are optional; the client handles their absence gracefully.
- The receipt width (32 chars) matches standard 58mm thermal paper.
- Polling interval is configurable via `POLL_INTERVAL_SECONDS` in `.env` (default 10s).
