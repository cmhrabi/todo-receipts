import logging
import time
from datetime import datetime, timezone

import config
from formatter import format_receipt
from notion_client import extract_item_data, query_database
from printers import get_printer
from state import (
    is_processed,
    load_state,
    mark_processed,
    save_state,
    update_cursor,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def poll_once(state: dict, printer) -> dict:
    pages = query_database(
        config.NOTION_API_KEY,
        config.NOTION_DATABASE_ID,
        created_after=state["last_created_time"],
    )

    now = datetime.now(timezone.utc)

    for page in pages:
        page_id = page["id"]
        if is_processed(page_id, state):
            continue

        created = datetime.fromisoformat(page["created_time"])
        age = (now - created).total_seconds()
        if age < config.SETTLE_DELAY_SECONDS:
            logger.debug("Skipping %s — only %.0fs old", page_id, age)
            continue

        try:
            item = extract_item_data(page)
            receipt = format_receipt(item)
            printer.print_receipt(receipt)
            logger.info("Printed receipt for: %s", item["title"])
        except Exception:
            logger.exception("Failed to process page %s", page_id)
            continue

        state = mark_processed(page_id, state)
        state = update_cursor(state, page["created_time"])

    save_state(state)
    return state


def main():
    printer = get_printer(config.PRINTER_TYPE)
    if not printer.is_available():
        logger.error("Printer not available")
        raise SystemExit(1)

    state = load_state()
    logger.info(
        "Polling Notion database every %ds", config.POLL_INTERVAL_SECONDS
    )

    while True:
        try:
            state = poll_once(state, printer)
        except Exception:
            logger.exception("Poll cycle failed")
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
