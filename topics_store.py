import json
from pathlib import Path

from config import TOPICS_FILE

STATUS_ACTIVE = "active"
STATUS_REJECTED = "rejected"
STATUS_POSTED = "posted"

VALID_STATUSES = {STATUS_ACTIVE, STATUS_REJECTED, STATUS_POSTED}


def _topics_path():
    return Path(TOPICS_FILE)


def load_topics():
    """Load all topics from topics.json."""
    path = _topics_path()
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Legacy single-topic DynamoDB-style export
        return [_normalize_topic_record(data)]

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array of topics.")

    return [_normalize_topic_record(topic) for topic in data]


def save_topics(topics):
    """Write topics array to topics.json."""
    path = _topics_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2)
        f.write("\n")


def _normalize_topic_record(record):
    """Support plain JSON and old DynamoDB attribute format."""
    if "topicId" in record and isinstance(record["topicId"], dict):
        return {
            "topicId": str(record["topicId"].get("S", "")).strip(),
            "topicName": str(record.get("topicName", {}).get("S", "")).strip(),
            "status": str(record.get("status", {}).get("S", STATUS_ACTIVE)).strip().lower(),
        }

    return {
        "topicId": str(record.get("topicId", "")).strip(),
        "topicName": str(record.get("topicName", "")).strip(),
        "status": str(record.get("status", STATUS_ACTIVE)).strip().lower(),
    }


def get_topic(topic_id):
    """Return a single topic by id."""
    topic_id = str(topic_id).strip()
    for topic in load_topics():
        if topic["topicId"] == topic_id:
            return topic
    return None


def get_next_topic_in_series(current_topic_id):
    """Return the next topicName in topics.json order (for 'Next I'll explain' teaser)."""
    topics = load_topics()
    current_topic_id = str(current_topic_id).strip()
    seen_current = False

    for topic in topics:
        if seen_current:
            return topic["topicName"]
        if topic["topicId"] == current_topic_id:
            seen_current = True

    return None


def get_next_active_topic():
    """
    Return the first active topic by reading topics.json top to bottom (line by line).
  Skips posted/rejected rows until the first active row is found.
    """
    for topic in load_topics():
        if topic["status"] == STATUS_ACTIVE:
            return topic

    raise LookupError(f"No active topics found in {TOPICS_FILE}.")


def get_active_topic(topic_id):
    """Return a specific topic only if it exists and is active."""
    topic = get_topic(topic_id)
    if not topic:
        raise LookupError(f"Topic id {topic_id} not found in {TOPICS_FILE}.")
    if topic["status"] != STATUS_ACTIVE:
        raise ValueError(
            f"Topic {topic_id} is not active (status={topic['status']})."
        )
    return topic


def update_topic_status(topic_id, status):
    """Update topic status to active, rejected, or posted."""
    status = str(status).strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Use: {', '.join(sorted(VALID_STATUSES))}")

    topics = load_topics()
    topic_id = str(topic_id).strip()
    updated = False

    for topic in topics:
        if topic["topicId"] == topic_id:
            topic["status"] = status
            updated = True
            break

    if not updated:
        raise LookupError(f"Topic id {topic_id} not found in {TOPICS_FILE}.")

    save_topics(topics)
    return get_topic(topic_id)
