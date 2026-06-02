import requests

from agents.image.prompt import build_image_prompt
from agents.telegram.prompt import build_approval_message
from config import TELEGRAM_API_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def telegram_url(method):
    return f"{TELEGRAM_API_BASE_URL}/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_telegram_text(chat_id, text):
    """Send one or more Telegram messages, splitting long text if needed."""
    if not text:
        return

    for start in range(0, len(text), TELEGRAM_MAX_MESSAGE_LENGTH):
        chunk = text[start : start + TELEGRAM_MAX_MESSAGE_LENGTH]
        requests.post(
            telegram_url("sendMessage"),
            json={"chat_id": chat_id, "text": chunk},
            timeout=30,
        )


def send_draft_for_approval(draft_id, topic, post, image_prompt=None):
    """Send LinkedIn draft to Telegram for approval via inline buttons."""
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not configured in .env")
        return None

    if not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_CHAT_ID not configured in .env")
        return None

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": build_approval_message(topic, post),
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "Approve",
                        "callback_data": f"approve:{draft_id}",
                    },
                    {
                        "text": "Reject",
                        "callback_data": f"reject:{draft_id}",
                    },
                ]
            ]
        },
    }

    try:
        response = requests.post(telegram_url("sendMessage"), json=payload, timeout=30)
        result = response.json()

        if response.status_code == 200:
            print("Draft sent to Telegram successfully.")
            final_image_prompt = image_prompt or build_image_prompt(topic, post)
            print("\n" + "=" * 60)
            print("IMAGE PROMPT")
            print("=" * 60)
            print(final_image_prompt)
            print("=" * 60 + "\n")
            send_telegram_text(
                TELEGRAM_CHAT_ID,
                (
                    "Image prompt (create image manually, upload it here, then press Approve):\n\n"
                    f"{final_image_prompt}"
                ),
            )
            print("Image prompt sent to Telegram.")
        else:
            print(f"Telegram API error: {result}")

        return result
    except Exception as exc:
        print(f"Error sending to Telegram: {exc}")
        return None


def send_for_approval(topic_id, topic, post, filename):
    """Send series-topic draft to Telegram for approval."""
    return send_draft_for_approval(topic_id, topic, post)
