import json
import os
import time

import requests

from agents.approval.prompt import (
    approval_failure_message,
    approval_success_message,
    rejection_message,
)
from agents.linkedin.agent import post_to_linkedin
from config import (
    DRAFTS_FILE,
    TELEGRAM_API_BASE_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_POLL_INTERVAL,
)


BOT_TOKEN = TELEGRAM_BOT_TOKEN
POLL_INTERVAL = TELEGRAM_POLL_INTERVAL


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
    telegram_post(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
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

    print(f"Reading post from: {filename}")
    print(f"Topic: {topic}")
    print("Sending approved post to agents.linkedin.agent.post_to_linkedin...")

    if post_to_linkedin(post_content):
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

    success, error_message = publish_draft_to_linkedin(topic_id, draft)

    if success:
        draft["status"] = "posted"
        draft["posted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        drafts[topic_id] = draft
        save_drafts(drafts)

        clear_approval_buttons(chat_id, message_id)
        send_telegram_message(
            chat_id,
            approval_success_message(topic_id, draft.get("topic", topic_id)),
        )
        return

    draft["status"] = "publish_failed"
    draft["publish_error"] = error_message
    draft["publish_failed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    drafts[topic_id] = draft
    save_drafts(drafts)

    send_telegram_message(chat_id, approval_failure_message(topic_id, error_message))


def handle_rejection(topic_id, chat_id, message_id):
    drafts = load_drafts()
    draft = drafts.get(topic_id, {})
    draft["status"] = "rejected"
    draft["rejected_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    drafts[topic_id] = draft
    save_drafts(drafts)

    clear_approval_buttons(chat_id, message_id)
    send_telegram_message(chat_id, rejection_message(topic_id))


def run_approval_agent():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not configured in .env")
        return

    offset = None
    print("Starting Telegram Approval Agent...")

    while True:
        try:
            params = {}
            if offset:
                params["offset"] = offset

            response = requests.get(telegram_url("getUpdates"), params=params, timeout=30)
            response.raise_for_status()
            updates = response.json()

            for update in updates.get("result", []):
                offset = update["update_id"] + 1

                if "callback_query" not in update:
                    continue

                callback = update["callback_query"]
                callback_id = callback["id"]
                message_id = callback["message"]["message_id"]
                chat_id = callback["message"]["chat"]["id"]
                data = callback["data"]

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
        except Exception as exc:
            print(f"Error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_approval_agent()
