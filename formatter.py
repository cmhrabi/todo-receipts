import textwrap
from datetime import datetime


def format_receipt(item: dict, width: int = 32) -> str:
    separator = "=" * width
    header = "✦ NEW TODO ✦".center(width)

    # Word-wrap title with checkbox prefix
    lines = textwrap.wrap(item["title"], width=width - 3)
    if not lines:
        lines = ["(untitled)"]
    title_block = ""
    for i, line in enumerate(lines):
        prefix = "□  " if i == 0 else "   "
        title_block += prefix + line + "\n"

    # Format created_time as local time
    dt = datetime.fromisoformat(item["created_time"].replace("Z", "+00:00"))
    local_dt = dt.astimezone()
    date_str = local_dt.strftime("%b %d, %Y — %-I:%M %p")

    parts = [separator, header, separator, "", title_block, f"Added: {date_str}"]
    if item.get("status"):
        parts.append(f"Status: {item['status']}")
    if item.get("priority"):
        parts.append(f"Priority: {item['priority']}")
    parts.extend([separator, "", "", ""])

    return "\n".join(parts)
