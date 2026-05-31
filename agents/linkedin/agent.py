import re

import requests

from config import (
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_API_URL,
    LINKEDIN_PERSON_ID,
    LINKEDIN_RESTLI_PROTOCOL_VERSION,
    LINKEDIN_VERSION,
)
from agents.linkedin.prompt import POST_LOG_END, POST_LOG_START


LINKEDIN_SHARE_URL = f"{LINKEDIN_API_URL}/posts"


def clean_linkedin_formatting(post_content):
    """Remove Markdown formatting that LinkedIn posts do not render."""
    post_content = post_content.replace("\r\n", "\n").replace("\r", "\n")
    post_content = "".join(
        char for char in post_content
        if char in "\n\t" or ord(char) >= 32
    )
    post_content = re.sub(r"(?m)^#{1,6}\s*", "", post_content)
    post_content = re.sub(r"\*\*(.+?)\*\*", r"\1", post_content)
    post_content = re.sub(r"__(.+?)__", r"\1", post_content)
    post_content = re.sub(r"`([^`]+)`", r"\1", post_content)
    return post_content.strip()


def prepare_linkedin_post(post):
    """Copy the draft to clipboard and open LinkedIn feed."""
    import webbrowser
    import pyperclip

    pyperclip.copy(post)
    webbrowser.open("https://www.linkedin.com/feed/")

    print("LinkedIn opened.")
    print("Post copied to clipboard.")


def post_to_linkedin(post_content):
    """Publish a LinkedIn post using the official LinkedIn REST API."""
    post_content = clean_linkedin_formatting(post_content)

    if not post_content:
        print("Error: Post content is empty")
        return False

    print(f"\n{POST_LOG_START}")
    print(post_content)
    print(POST_LOG_END)
    print(f"LinkedIn post character count: {len(post_content)}")

    if not LINKEDIN_ACCESS_TOKEN:
        print("Error: LINKEDIN_ACCESS_TOKEN not configured in .env")
        return False

    if not LINKEDIN_PERSON_ID:
        print("Error: LINKEDIN_PERSON_ID not configured in .env")
        return False

    print("Posting to LinkedIn using Official API...")

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": LINKEDIN_RESTLI_PROTOCOL_VERSION,
        "LinkedIn-Version": LINKEDIN_VERSION,
    }

    payload = {
        "author": f"urn:li:person:{LINKEDIN_PERSON_ID}",
        "commentary": post_content,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(LINKEDIN_SHARE_URL, json=payload, headers=headers, timeout=30)

    if response.ok:
        print("Post published successfully to LinkedIn.")
        if response.text.strip():
            try:
                print(f"Response: {response.json()}")
            except requests.exceptions.JSONDecodeError:
                print(f"Response: {response.text}")
        else:
            print("Response: No response body returned by LinkedIn.")
        return True

    print(f"Error posting to LinkedIn: {response.status_code}")
    print(f"Response: {response.text}")
    return False
