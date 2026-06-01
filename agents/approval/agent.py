import json
import os
import re
import sys
import time
from pathlib import Path

# Allow: python agents/approval/agent.py (from project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests

from agents.approval.prompt import (
    approval_failure_message,
    approval_success_message,
    rejection_message,
)
from agents.linkedin.agent import post_to_linkedin
from config import (
    DRAFTS_FILE,
    IMAGES_DIR,
    TELEGRAM_API_BASE_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_POLL_INTERVAL,
)
from topics_store import (
    STATUS_POSTED,
    STATUS_REJECTED,
    get_active_topic,
    get_next_active_topic,
    update_topic_status,
)


BOT_TOKEN = TELEGRAM_BOT_TOKEN
POLL_INTERVAL = TELEGRAM_POLL_INTERVAL
TELEGRAM_MAX_MESSAGE_LENGTH = 4096

PIPELINE_COMMANDS = {"/next", "/generate", "/new"}
_pipeline_running = False

HELP_MESSAGE = """LinkedIn Agent commands

/next — Research + write next active topic and send draft here
/generate — Same as /next
/status — Show next active topic in topics.json
/help — Show this message

Workflow after /next:
1. Create image from the image prompt message
2. Upload photo here (caption = topic id if needed)
3. Press Approve on the draft message
"""


def load_drafts():
    """Load the drafts mapping file."""
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_drafts(drafts):
    """Save the drafts mapping file."""
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)


def telegram_url(method):
    return f"{TELEGRAM_API_BASE_URL}/bot{BOT_TOKEN}/{method}"


def telegram_post(method, payload):
    response = requests.post(telegram_url(method), json=payload, timeout=30)
    response.raise_for_status()
    return response


def send_telegram_message(chat_id, text):
    """Send text to Telegram, splitting if it exceeds the message limit."""
    if not text:
        return

    for start in range(0, len(text), TELEGRAM_MAX_MESSAGE_LENGTH):
        chunk = text[start : start + TELEGRAM_MAX_MESSAGE_LENGTH]
        telegram_post(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": chunk,
            },
        )


def read_draft_post(draft):
    """Return topic and post body from the draft file."""
    filename = draft.get("filename")
    topic = draft.get("topic", "")

    if not filename or not os.path.exists(filename):
        return topic, None

    with open(filename, "r", encoding="utf-8") as f:
        return topic, f.read()


def resolve_topic_id_for_photo(caption, drafts):
    """Match an uploaded photo to a draft topic id."""
    caption = (caption or "").strip()
    if caption and caption in drafts:
        return caption

    pending = [
        topic_id
        for topic_id, draft in drafts.items()
        if draft.get("status") == "pending"
    ]
    if len(pending) == 1:
        return pending[0]

    return None


def download_telegram_photo(file_id, dest_path):
    """Download a Telegram photo to a local file."""
    response = requests.get(
        telegram_url("getFile"),
        params={"file_id": file_id},
        timeout=30,
    )
    response.raise_for_status()
    file_path = response.json()["result"]["file_path"]

    file_url = f"{TELEGRAM_API_BASE_URL}/file/bot{BOT_TOKEN}/{file_path}"
    image_response = requests.get(file_url, timeout=60)
    image_response.raise_for_status()

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(image_response.content)


def save_pending_image(topic_id, draft, file_id):
    """Store uploaded Telegram image on disk and link it to the draft."""
    topic = draft.get("topic", topic_id)
    safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    pending_path = os.path.join(
        IMAGES_DIR,
        f"{safe_topic}_pending_{topic_id}.jpg",
    )

    download_telegram_photo(file_id, pending_path)

    old_pending = draft.get("pending_image_path")
    if old_pending and old_pending != pending_path and os.path.exists(old_pending):
        os.remove(old_pending)

    draft["pending_image_path"] = pending_path
    return pending_path


def finalize_draft_image(topic_id, draft):
    """Move pending upload to final image filename on approve."""
    pending_path = draft.get("pending_image_path")
    if not pending_path or not os.path.exists(pending_path):
        return None, (
            f"No image uploaded for topic {topic_id}.\n\n"
            "Send your image to this chat first, then press Approve."
        )

    topic = draft.get("topic", topic_id)
    safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    extension = Path(pending_path).suffix or ".jpg"
    final_path = os.path.join(
        IMAGES_DIR,
        f"{safe_topic}_{time.strftime('%Y%m%d_%H%M%S')}{extension}",
    )

    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.replace(pending_path, final_path)

    draft["image_path"] = final_path
    draft.pop("pending_image_path", None)
    return final_path, None


def is_authorized_chat(chat_id):
    return str(chat_id) == str(TELEGRAM_CHAT_ID)


def parse_command(text):
    if not text or not text.strip().startswith("/"):
        return None, []

    parts = text.strip().split()
    command = parts[0].split("@")[0].lower()
    return command, parts[1:]


def handle_pipeline_command(chat_id, topic_id=None):
    """Run research → writer → Telegram draft for the next (or given) active topic."""
    global _pipeline_running

    if _pipeline_running:
        send_telegram_message(
            chat_id,
            "Pipeline is already running. Wait for it to finish.",
        )
        return

    from agents.researcher.agent import run_research_agent

    try:
        if topic_id is None:
            preview = get_next_active_topic()
            topic_id = preview["topicId"]
            topic_name = preview["topicName"]
        else:
            preview = get_active_topic(topic_id)
            topic_name = preview["topicName"]

        send_telegram_message(
            chat_id,
            f"Starting pipeline for topic {topic_id}: {topic_name}\n\n"
            "This may take a minute (Bedrock research + post generation)...",
        )

        _pipeline_running = True
        run_research_agent(topic_id=topic_id)
        send_telegram_message(
            chat_id,
            f"Draft ready for topic {topic_id}: {topic_name}\n\n"
            "1. Check the post message above\n"
            "2. Create image from the image prompt\n"
            "3. Upload photo here, then press Approve",
        )
    except LookupError as exc:
        send_telegram_message(chat_id, f"No topic available.\n\n{exc}")
    except ValueError as exc:
        send_telegram_message(chat_id, f"Cannot run pipeline.\n\n{exc}")
    except Exception as exc:
        send_telegram_message(chat_id, f"Pipeline failed.\n\n{exc}")
        print(f"Pipeline error: {exc}")
    finally:
        _pipeline_running = False


def handle_status_command(chat_id):
    try:
        topic = get_next_active_topic()
        send_telegram_message(
            chat_id,
            f"Next active topic:\n"
            f"ID: {topic['topicId']}\n"
            f"Name: {topic['topicName']}\n\n"
            "Send /next to generate the draft.",
        )
    except LookupError as exc:
        send_telegram_message(chat_id, f"No active topics left.\n\n{exc}")


def handle_command_message(message, chat_id):
    """Handle Telegram text commands. Returns True if message was a command."""
    if not is_authorized_chat(chat_id):
        if message.get("text", "").strip().startswith("/"):
            send_telegram_message(chat_id, "Unauthorized chat.")
        return bool(message.get("text", "").strip().startswith("/"))

    command, args = parse_command(message.get("text", ""))
    if not command:
        return False

    if command in ("/help", "/start"):
        send_telegram_message(chat_id, HELP_MESSAGE)
    elif command == "/status":
        handle_status_command(chat_id)
    elif command in PIPELINE_COMMANDS:
        topic_id = args[0] if args else None
        handle_pipeline_command(chat_id, topic_id=topic_id)
    else:
        send_telegram_message(
            chat_id,
            f"Unknown command: {command}\n\nSend /help for available commands.",
        )

    return True


def handle_incoming_photo(message, chat_id):
    """Receive image from Telegram and attach it to a pending draft."""
    if not is_authorized_chat(chat_id):
        return

    photos = message.get("photo") or []
    if not photos:
        return

    drafts = load_drafts()
    topic_id = resolve_topic_id_for_photo(message.get("caption"), drafts)
    if not topic_id:
        send_telegram_message(
            chat_id,
            "Could not match this image to a draft.\n\n"
            "Send the photo with caption = topic id (example: 1), "
            "or keep only one pending draft.",
        )
        return

    draft = drafts.get(topic_id)
    if not draft or draft.get("status") != "pending":
        send_telegram_message(
            chat_id,
            f"Topic {topic_id} is not waiting for approval, so the image was ignored.",
        )
        return

    file_id = photos[-1]["file_id"]
    pending_path = save_pending_image(topic_id, draft, file_id)
    drafts[topic_id] = draft
    save_drafts(drafts)

    send_telegram_message(
        chat_id,
        f"Image received for topic {topic_id}.\n\n"
        f"Saved temporarily to:\n{pending_path}\n\n"
        "Press Approve when you are ready.",
    )


def clear_approval_buttons(chat_id, message_id):
    telegram_post(
        "editMessageReplyMarkup",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        },
    )


def publish_draft_to_linkedin(topic_id, draft):
    """Read the approved draft file and publish it through the LinkedIn agent."""
    filename = draft.get("filename")
    topic = draft.get("topic", topic_id)

    if not filename:
        return False, f"Post file is missing in {DRAFTS_FILE} for topic {topic_id}."

    if not os.path.exists(filename):
        return False, f"Post file not found: {filename}"

    with open(filename, "r", encoding="utf-8") as f:
        post_content = f.read()

    image_path = draft.get("image_path")
    if not image_path or not os.path.exists(image_path):
        return False, (
            f"No image found for topic {topic_id}. "
            "Upload an image to Telegram before pressing Approve."
        )

    print(f"Reading post from: {filename}")
    print(f"Topic: {topic}")
    print(f"Image: {image_path}")
    print("Sending approved post to agents.linkedin.agent.post_to_linkedin...")

    if post_to_linkedin(post_content, image_path=image_path, image_alt_text=topic):
        return True, ""

    return False, "LinkedIn posting failed. Check the LinkedIn agent output for the API response."


def handle_approval(topic_id, chat_id, message_id):
    drafts = load_drafts()
    draft = drafts.get(topic_id)

    if not draft:
        print(f"Error: No draft found for topic_id {topic_id}")
        send_telegram_message(chat_id, f"Error: No draft found for topic {topic_id}.")
        return

    if draft.get("status") == "posted":
        clear_approval_buttons(chat_id, message_id)
        send_telegram_message(chat_id, f"Topic {topic_id} was already posted to LinkedIn.")
        return

    image_path, image_error = finalize_draft_image(topic_id, draft)
    if image_error:
        send_telegram_message(chat_id, image_error)
        return

    drafts[topic_id] = draft
    save_drafts(drafts)

    success, error_message = publish_draft_to_linkedin(topic_id, draft)
    topic_name = draft.get("topic", topic_id)

    if success:
        draft["status"] = "posted"
        draft["posted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        drafts[topic_id] = draft
        save_drafts(drafts)

        clear_approval_buttons(chat_id, message_id)
        update_topic_status(topic_id, STATUS_POSTED)
        send_telegram_message(
            chat_id,
            approval_success_message(topic_id, topic_name, image_path),
        )
        return

    draft["status"] = "publish_failed"
    draft["publish_error"] = error_message
    draft["publish_failed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    drafts[topic_id] = draft
    save_drafts(drafts)

    send_telegram_message(
        chat_id,
        approval_failure_message(topic_id, error_message),
    )


def handle_rejection(topic_id, chat_id, message_id):
    drafts = load_drafts()
    draft = drafts.get(topic_id, {})
    draft["status"] = "rejected"
    draft["rejected_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    drafts[topic_id] = draft
    save_drafts(drafts)

    clear_approval_buttons(chat_id, message_id)
    try:
        update_topic_status(topic_id, STATUS_REJECTED)
    except LookupError as exc:
        print(f"Warning: {exc}")
    send_telegram_message(chat_id, rejection_message(topic_id))


def ensure_telegram_polling_mode():
    """
    Use getUpdates (polling). Clear webhook and avoid 409 conflicts with other clients.
    """
    try:
        requests.post(
            telegram_url("deleteWebhook"),
            json={"drop_pending_updates": False},
            timeout=30,
        )
        print("Telegram polling mode ready (webhook cleared).")
    except requests.RequestException as exc:
        print(f"Warning: could not clear Telegram webhook: {exc}")


def run_approval_agent():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not configured in .env")
        return

    ensure_telegram_polling_mode()

    offset = None
    print("Starting Telegram Approval Agent...")
    print("Run only ONE approval agent at a time for this bot token.")
    print("Telegram commands: /next /generate /status /help")

    while True:
        try:
            params = {}
            if offset:
                params["offset"] = offset

            response = requests.get(telegram_url("getUpdates"), params=params, timeout=30)
            if response.status_code == 409:
                print(
                    "Telegram 409 Conflict: another process is polling this bot. "
                    "Stop other terminals/servers running the approval agent."
                )
                ensure_telegram_polling_mode()
                time.sleep(5)
                continue

            response.raise_for_status()
            updates = response.json()

            for update in updates.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")
                if message:
                    chat_id = message["chat"]["id"]
                    if handle_command_message(message, chat_id):
                        continue
                    if message.get("photo"):
                        handle_incoming_photo(message, chat_id)
                        continue

                if "callback_query" not in update:
                    continue

                callback = update["callback_query"]
                callback_id = callback["id"]
                message_id = callback["message"]["message_id"]
                chat_id = callback["message"]["chat"]["id"]
                data = callback["data"]

                if not is_authorized_chat(chat_id):
                    print(f"Ignored callback from unauthorized chat {chat_id}")
                    telegram_post(
                        "answerCallbackQuery",
                        {
                            "callback_query_id": callback_id,
                            "text": "Unauthorized.",
                            "show_alert": True,
                        },
                    )
                    continue

                print(f"Received callback: {data}")
                telegram_post(
                    "answerCallbackQuery",
                    {"callback_query_id": callback_id},
                )

                action, _, topic_id = data.partition(":")
                if not topic_id:
                    print(f"Error: topic_id not found in callback data: {data}")
                    continue

                if action == "approve":
                    print(f"APPROVED: Topic ID {topic_id}")
                    handle_approval(topic_id, chat_id, message_id)
                elif action == "reject":
                    print(f"REJECTED: Topic ID {topic_id}")
                    handle_rejection(topic_id, chat_id, message_id)

            time.sleep(POLL_INTERVAL)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                print(
                    "Telegram 409 Conflict: close duplicate approval agent instances, then retrying..."
                )
                ensure_telegram_polling_mode()
                time.sleep(5)
                continue
            print(f"Error: {exc}")
            time.sleep(5)
        except Exception as exc:
            print(f"Error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_approval_agent()
