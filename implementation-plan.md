# Todo Receipt Printer — Implementation Plan

A Raspberry Pi + thermal printer project that watches a Notion database and prints a little receipt every time a new todo is added. Built in two phases: Mac development first, hardware integration later.

---

## Project Structure

```
todo-receipt-printer/
├── .env                     # Notion API key + database ID (gitignored)
├── .env.example             # Template showing required env vars
├── .gitignore
├── pyproject.toml           # Project metadata + dependencies (managed by uv)
├── uv.lock                  # Lockfile (committed to git)
├── README.md
├── config.py                # Loads env vars, app settings
├── main.py                  # Entry point — runs the poll loop
├── notion_client.py         # Handles Notion API queries + new item detection
├── state.py                 # Tracks last-seen item to avoid reprints
├── formatter.py             # Turns a todo item into a receipt layout
├── printers/
│   ├── __init__.py          # Exports get_printer() factory function
│   ├── base.py              # Abstract base class for all printers
│   ├── console_printer.py   # Phase 1: prints to terminal
│   └── thermal_printer.py   # Phase 2: prints to ESC/POS hardware
└── systemd/
    └── todo-receipt.service  # Phase 2: systemd unit file for Pi
```

---

## PHASE 1 — Mac Development (No Hardware)

Build the full application with a console printer backend. Everything should be testable on a Mac with just a Notion API key.

### Step 1: Project scaffolding and config

- Create the directory structure above.
- Initialize the project with `uv init` and then `uv add requests python-dotenv` for the core dependencies. The thermal printer dependency (`python-escpos`) is added later in Phase 2 via an optional dependency group.
- In `pyproject.toml`, define an optional dependency group for hardware:
  ```toml
  [project.optional-dependencies]
  hardware = ["python-escpos"]
  ```
- `.env.example`:
  ```
  NOTION_API_KEY=your_notion_integration_token
  NOTION_DATABASE_ID=your_database_id
  PRINTER_TYPE=console
  POLL_INTERVAL_SECONDS=15
  ```
- `config.py`: Use `python-dotenv` to load `.env`. Expose a simple config object/dict with all the above values. `PRINTER_TYPE` defaults to `"console"`. `POLL_INTERVAL_SECONDS` defaults to `15`.

### Step 2: State tracking

`state.py` — Manages a small JSON file (`.last_seen.json`) that stores the ID and `created_time` of the most recently seen todo item.

- `load_state() -> dict | None` — Reads the file, returns the stored data or None if no file exists.
- `save_state(item_id: str, created_time: str) -> None` — Writes the ID and timestamp to the file.
- On first run (no state file), do NOT print all existing items. Instead, save the most recent item as the starting point and begin watching from there. This prevents a flood of receipts on first boot.

### Step 3: Notion poller

`notion_poller.py` — Talks to the Notion API to detect new todo items.

- `fetch_recent_items(api_key: str, database_id: str) -> list[dict]` — Queries the Notion database using `POST https://api.notion.com/v1/databases/{database_id}/query`. Sort by `created_time` descending. Limit to 10 results (we only care about recent ones). Use Notion API version `2022-06-28` in headers.
- `extract_item_data(notion_page: dict) -> dict` — Parses a Notion page object into a clean dict: `{ id, title, created_time, status, priority }`. Handle the Notion property types:
  - Title: extract plain text from the title property
  - Status/select: extract the name if present, default to None
  - Priority/select: same
  - Be defensive — if a property doesn't exist, use a sensible default.
- `get_new_items(items: list[dict], last_seen_id: str | None, last_seen_time: str | None) -> list[dict]` — Filters the fetched items to only those created after the last seen item. Compare by `created_time` string (ISO format sorts correctly). Return in chronological order (oldest first) so receipts print in order.

### Step 4: Receipt formatter

`formatter.py` — Turns a todo item dict into a formatted receipt string.

- `format_receipt(item: dict, width: int = 32) -> str` — Produces a receipt layout like:

```
================================
         ✦ NEW TODO ✦
================================

□  Buy groceries for the week
   and meal prep on Sunday

Added: Mar 30, 2026 — 2:45 PM
Status: Not started
Priority: High
================================



```

- Word-wrap the title text to `width - 3` characters (to account for the `□  ` prefix). Continuation lines should be indented 3 spaces to align with the text after the checkbox.
- Format `created_time` as a human-readable string (e.g., `Mar 30, 2026 — 2:45 PM`).
- Only include Status and Priority lines if those values are present.
- End with 3-4 blank lines (for paper feed on thermal printers, and visual spacing in console).
- `width` parameter is important: 32 chars for 58mm printers, 48 chars for 80mm printers. Default to 32.

### Step 5: Printer abstraction

`printers/base.py` — Abstract base class:
```python
from abc import ABC, abstractmethod

class BasePrinter(ABC):
    @abstractmethod
    def print_receipt(self, text: str) -> None:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
```

`printers/console_printer.py` — Implements `BasePrinter`:
- `print_receipt(text)`: Prints the receipt string to stdout. Add a visual border or slight indent so it stands out from log lines.
- `is_available()`: Always returns True.

`printers/__init__.py` — Factory function:
```python
def get_printer(printer_type: str) -> BasePrinter:
```
- If `printer_type == "console"`, return `ConsolePrinter()`.
- If `printer_type == "thermal"`, try to import and return `ThermalPrinter()`. If import fails (no `python-escpos`), raise a clear error message telling the user to install the hardware extras with `uv sync --extra hardware`.

### Step 6: Main loop

`main.py` — The entry point that ties everything together.

- On startup:
  1. Load config.
  2. Initialize the printer via `get_printer(config.PRINTER_TYPE)`.
  3. Check `printer.is_available()` — if not, log an error and exit.
  4. Load state.
  5. If no state exists (first run), fetch recent items, save the most recent one as starting state, log "First run — starting watch from [item title]", and enter the loop without printing anything.
- Poll loop:
  1. Fetch recent items from Notion.
  2. Get new items since last seen.
  3. For each new item (oldest first):
     - Format the receipt.
     - Print it via the printer.
     - Update the state to this item (update after each print, not after the batch, so if it crashes mid-batch we don't lose track).
  4. Sleep for `POLL_INTERVAL_SECONDS`.
  5. Repeat.
- Error handling:
  - Wrap the Notion API call in try/except. On failure, log the error and continue to next poll cycle. Don't crash.
  - Wrap the printer call in try/except. On failure, log the error but still update state (we don't want to reprint on retry).
  - Use `logging` module, not bare `print()` for log messages. Set up a basic format with timestamps.
- Handle `KeyboardInterrupt` gracefully — log "Shutting down" and exit cleanly.

### Step 7: README

Write a README covering:
- What the project does (one paragraph).
- Prerequisites: Python 3.10+, a Notion integration token, a database ID.
- Quick start: clone, run `uv sync`, copy `.env.example` to `.env`, fill in values, run `uv run python main.py`.
- Brief explanation of how to set up the Notion integration (create integration at notion.so/my-integrations, share database with integration).
- Note that Phase 2 (hardware) instructions are below.

---

## PHASE 2 — Raspberry Pi + Thermal Printer

Only do this phase once the hardware is in hand. Phase 1 should be fully working first. The polling loop from Phase 1 works well on a Pi — no need for webhooks or a public URL.

### Step 8: Thermal printer class

`printers/thermal_printer.py` — Implements `BasePrinter` using `python-escpos`. The factory in `printers/__init__.py` already handles lazy import and a clear error if `python-escpos` is missing.

- Constructor: Accept optional config for vendor ID, product ID, or device path. Read these from `config.py` settings (see Step 10). Default to USB auto-detection.
- `print_receipt(text: str)`:
  - Keep the existing `BasePrinter.print_receipt(text: str)` interface — the `formatter.py` module already produces the receipt string and both printers consume it the same way.
  - Don't just send raw text. Use ESC/POS commands via the library for nicer output:
    - Set center alignment for the header block.
    - Use bold + double-height for the "✦ NEW TODO ✦" line.
    - Switch to left alignment for the body.
    - Use normal text for the task title.
    - Use small/condensed text for the metadata lines (date, status, priority).
    - Send a cut command at the end (if the printer has a cutter) or feed enough lines to tear.
  - Parse the sections from the formatted `text` string (header, title, metadata) to decide which ESC/POS styles to apply. The receipt format is predictable enough to split on the `===` separators.
- `is_available()`: Try to initialize the USB connection. Return True if it connects, False if not.

### Step 9: Pi deployment setup

- Add a `setup_pi.sh` script that:
  1. Updates apt packages.
  2. Installs system dependencies for `python-escpos` (`libusb-1.0-0-dev` etc).
  3. Installs uv if not already present (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
  4. Runs `uv sync --extra hardware` to install all deps including the thermal printer library.
  5. Adds the current user to the `lp` group for printer access.
  6. Copies the systemd service file to `/etc/systemd/system/`.
  7. Prompts the user to fill in `.env`.

- `systemd/todo-receipt.service`:
  ```ini
  [Unit]
  Description=Todo Receipt Printer
  After=network-online.target
  Wants=network-online.target

  [Service]
  Type=simple
  User=pi
  WorkingDirectory=/home/pi/todo-receipts
  EnvironmentFile=/home/pi/todo-receipts/.env
  ExecStart=/home/pi/todo-receipts/.venv/bin/uv run python main.py
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  ```

### Step 10: Update config and README

- In `config.py`, add optional thermal printer settings: `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PRINTER_WIDTH` (32 or 48). These join the existing settings (`PRINTER_TYPE`, `POLL_INTERVAL_SECONDS`, `SETTLE_DELAY_SECONDS`).
- In `.env.example`, add the new vars commented out with notes.
- In README, add Phase 2 section: hardware shopping list (any ESC/POS USB thermal printer + Raspberry Pi 3/4/5 + power supplies), setup instructions referencing `setup_pi.sh`, how to switch `PRINTER_TYPE=thermal`, how to enable and start the systemd service, and troubleshooting tips (permissions, USB detection).

---

## Notes for the Implementer

- Use `uv` for all package management. No `pip`, no `requirements.txt`, no manual venv creation. `uv sync` handles everything.
- The systemd service should use `uv run python main.py` as the ExecStart command so it picks up the correct environment.
- Keep dependencies minimal. Only `requests` and `python-dotenv` for Phase 1.
- No classes where functions will do. The only class hierarchy is the printer abstraction — everything else should be plain functions.
- Type hints on all function signatures.
- The Notion API token and database ID are the only secrets. Everything else is non-sensitive config.
- Don't over-engineer. This is a ~200 line project, not a framework.