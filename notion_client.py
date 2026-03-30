import requests

NOTION_API_URL = "https://api.notion.com/v1/pages/{page_id}"
NOTION_DB_QUERY_URL = "https://api.notion.com/v1/databases/{database_id}/query"
NOTION_VERSION = "2022-06-28"


def fetch_page(api_key: str, page_id: str) -> dict:
    response = requests.get(
        NOTION_API_URL.format(page_id=page_id),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    response.raise_for_status()
    return response.json()


def query_database(api_key: str, database_id: str, created_after: str | None = None) -> list[dict]:
    body: dict = {
        "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
    }
    if created_after:
        body["filter"] = {
            "timestamp": "created_time",
            "created_time": {"after": created_after},
        }

    response = requests.post(
        NOTION_DB_QUERY_URL.format(database_id=database_id),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
        },
        json=body,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def _extract_select_or_status(props: dict, name: str) -> str | None:
    prop = props.get(name)
    if prop is None:
        return None
    if prop["type"] == "status" and prop.get("status"):
        return prop["status"]["name"]
    if prop["type"] == "select" and prop.get("select"):
        return prop["select"]["name"]
    return None


def extract_item_data(notion_page: dict) -> dict:
    props = notion_page["properties"]

    # Every database has exactly one title property
    title = "(untitled)"
    for prop in props.values():
        if prop["type"] == "title" and prop["title"]:
            title = prop["title"][0]["plain_text"]
            break

    return {
        "id": notion_page["id"],
        "title": title,
        "created_time": notion_page["created_time"],
        "status": _extract_select_or_status(props, "Status"),
        "priority": _extract_select_or_status(props, "Priority"),
    }
