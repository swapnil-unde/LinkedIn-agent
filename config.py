import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def load_env_file(path=ENV_FILE):
    """Load simple KEY=VALUE pairs from .env without requiring extra setup."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def get_int(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_path(name, default):
    value = os.getenv(name, default)
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(BASE_DIR / path)


load_env_file()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_TEXT_MODEL_ID = os.getenv("BEDROCK_TEXT_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_IMAGE_MODEL_ID = os.getenv("BEDROCK_IMAGE_MODEL_ID", "amazon.nova-canvas-v1:0")

DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "LinkedInTopics")
TOPIC_ID = os.getenv("TOPIC_ID", "1")

DRAFTS_FILE = get_path("DRAFTS_FILE", "_drafts.json")
POST_DIR = get_path("POST_DIR", "agents/writer/post")
RESEARCH_DIR = get_path("RESEARCH_DIR", "agents/researcher/research")
IMAGES_DIR = get_path("IMAGES_DIR", "agents/image/images")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org")
TELEGRAM_POLL_INTERVAL = get_int("TELEGRAM_POLL_INTERVAL", 2)

LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_ID = os.getenv("LINKEDIN_PERSON_ID", "")
LINKEDIN_API_URL = os.getenv("LINKEDIN_API_URL", "https://api.linkedin.com/rest")
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202506")
LINKEDIN_RESTLI_PROTOCOL_VERSION = os.getenv("LINKEDIN_RESTLI_PROTOCOL_VERSION", "2.0.0")
