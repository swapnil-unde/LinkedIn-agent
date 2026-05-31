import mimetypes
import os
import re
from pathlib import Path

import requests

from config import (
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_API_URL,
    LINKEDIN_PERSON_ID,
    LINKEDIN_RESTLI_PROTOCOL_VERSION,
    LINKEDIN_VERSION,
)
from agents.linkedin.prompt import POST_LOG_END, POST_LOG_START


LINKEDIN_POSTS_URL = f"{LINKEDIN_API_URL}/posts"
LINKEDIN_IMAGES_URL = f"{LINKEDIN_API_URL}/images"
MAX_IMAGE_BYTES = 5 * 1024 * 1024


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


def linkedin_headers(content_type="application/json"):
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": LINKEDIN_RESTLI_PROTOCOL_VERSION,
        "LinkedIn-Version": LINKEDIN_VERSION,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def validate_linkedin_credentials():
    if not LINKEDIN_ACCESS_TOKEN:
        print("Error: LINKEDIN_ACCESS_TOKEN not configured in .env")
        return False

    if not LINKEDIN_PERSON_ID:
        print("Error: LINKEDIN_PERSON_ID not configured in .env")
        return False

    return True


def upload_image_to_linkedin(image_path, alt_text=""):
    """
    Register, upload, and return a LinkedIn image URN for use in a post.
    https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is too large ({file_size} bytes). LinkedIn limit is {MAX_IMAGE_BYTES} bytes."
        )

    owner = f"urn:li:person:{LINKEDIN_PERSON_ID}"
    init_response = requests.post(
        f"{LINKEDIN_IMAGES_URL}?action=initializeUpload",
        headers=linkedin_headers(),
        json={"initializeUploadRequest": {"owner": owner}},
        timeout=30,
    )

    if not init_response.ok:
        raise RuntimeError(
            f"LinkedIn initializeUpload failed ({init_response.status_code}): {init_response.text}"
        )

    init_data = init_response.json().get("value", {})
    upload_url = init_data.get("uploadUrl")
    image_urn = init_data.get("image")

    if not upload_url or not image_urn:
        raise RuntimeError(f"LinkedIn initializeUpload missing uploadUrl/image: {init_response.text}")

    image_bytes = path.read_bytes()
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    upload_response = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": mime_type,
        },
        data=image_bytes,
        timeout=120,
    )

    if upload_response.status_code not in (200, 201):
        raise RuntimeError(
            f"LinkedIn image upload failed ({upload_response.status_code}): {upload_response.text}"
        )

    print(f"Image uploaded to LinkedIn: {image_urn}")
    if alt_text:
        print(f"Image alt text: {alt_text[:120]}")

    return image_urn


def build_post_payload(post_content, image_urn=None, alt_text=""):
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

    if image_urn:
        media = {"id": image_urn}
        if alt_text:
            media["altText"] = alt_text[:4086]
        payload["content"] = {"media": media}

    return payload


def prepare_linkedin_post(post):
    """Copy the draft to clipboard and open LinkedIn feed."""
    import webbrowser
    import pyperclip

    pyperclip.copy(post)
    webbrowser.open("https://www.linkedin.com/feed/")

    print("LinkedIn opened.")
    print("Post copied to clipboard.")


def post_to_linkedin(post_content, image_path=None, image_alt_text=""):
    """Publish a LinkedIn post with optional image using the REST API."""
    post_content = clean_linkedin_formatting(post_content)

    if not post_content:
        print("Error: Post content is empty")
        return False

    if not validate_linkedin_credentials():
        return False

    print(f"\n{POST_LOG_START}")
    print(post_content)
    print(POST_LOG_END)
    print(f"LinkedIn post character count: {len(post_content)}")

    image_urn = None
    if image_path:
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return False

        print(f"Uploading image: {image_path}")
        try:
            image_urn = upload_image_to_linkedin(image_path, alt_text=image_alt_text)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Error uploading image to LinkedIn: {exc}")
            return False
    else:
        print("No image provided; posting text only.")

    print("Posting to LinkedIn using Official API...")

    payload = build_post_payload(post_content, image_urn=image_urn, alt_text=image_alt_text)
    response = requests.post(
        LINKEDIN_POSTS_URL,
        json=payload,
        headers=linkedin_headers(),
        timeout=30,
    )

    if response.ok:
        print("Post published successfully to LinkedIn.")
        if image_urn:
            print(f"Posted with image: {image_urn}")
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
