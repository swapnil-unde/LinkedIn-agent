import json
import os
import re
from datetime import datetime

import boto3

from agents.linkedin.agent import clean_linkedin_formatting
from agents.telegram.agent import send_for_approval
from agents.writer.prompt import build_linkedin_post_prompt
from config import AWS_REGION, BEDROCK_TEXT_MODEL_ID, DRAFTS_FILE, POST_DIR
from topics_store import get_next_topic_in_series


bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


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


def generate_linkedin_post(topic_id, topic, research):
    next_topic = get_next_topic_in_series(topic_id) or "the next topic in this series"
    prompt = build_linkedin_post_prompt(
        research=research,
        topic_name=topic,
        post_number=topic_id,
        next_topic_name=next_topic,
    )

    response = bedrock.converse(
        modelId=BEDROCK_TEXT_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
    )

    post = clean_linkedin_formatting(response["output"]["message"]["content"][0]["text"])
    print(f"Generated post length: {len(post)} characters")
    safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)

    os.makedirs(POST_DIR, exist_ok=True)
    filename = os.path.join(
        POST_DIR,
        f"{safe_topic}_linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(post)

    print("\n" + "=" * 60)
    print("LINKEDIN POST")
    print("=" * 60)
    print(post)
    print("=" * 60)
    print(f"\nSaved post to {filename}")

    drafts = load_drafts()
    drafts[str(topic_id)] = {
        "filename": filename,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
    }
    save_drafts(drafts)

    print("\nSending draft to Telegram...\n")
    send_for_approval(topic_id, topic, post, filename)
    return post
