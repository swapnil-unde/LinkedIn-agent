import json
import os
import re
from datetime import datetime

import boto3
import requests

from agents.image.prompt import build_news_image_prompt
from agents.linkedin.agent import clean_linkedin_formatting
from agents.news_researcher.prompt import build_linkedin_post_prompt, build_news_prompt
from agents.telegram.agent import send_draft_for_approval
from config import (
    AWS_REGION,
    BEDROCK_TEXT_MODEL_ID,
    DRAFTS_FILE,
    NEWS_API_BASE_URL,
    NEWS_API_KEY,
    NEWS_MAX_ARTICLES,
    POST_DIR,
)


bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def load_drafts():
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_drafts(drafts):
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)


def save_news_draft_and_send(topic, linkedin_post, image_prompt):
    """Save news post to disk, register draft, and send Approve/Reject to Telegram."""
    draft_id = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    os.makedirs(POST_DIR, exist_ok=True)
    filename = os.path.join(
        POST_DIR,
        f"{safe_topic}_news_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(linkedin_post)

    drafts = load_drafts()
    drafts[draft_id] = {
        "filename": filename,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "type": "news",
    }
    save_drafts(drafts)

    send_draft_for_approval(
        draft_id,
        topic,
        linkedin_post,
        image_prompt=image_prompt,
    )
    return draft_id, filename


def _extract_json_block(text):
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Could not parse JSON from Bedrock response.")
    return text[start : end + 1]


def fetch_news(topic, max_articles=NEWS_MAX_ARTICLES):
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY is missing in .env. Add it to use /news command.")

    response = requests.get(
        f"{NEWS_API_BASE_URL}/everything",
        params={
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "apiKey": NEWS_API_KEY,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "ok":
        raise ValueError(f"News API error: {payload}")

    articles = []
    for item in payload.get("articles", []):
        url = item.get("url")
        title = item.get("title")
        if not url or not title:
            continue
        articles.append(
            {
                "title": title.strip(),
                "source": (item.get("source") or {}).get("name", "Unknown Source"),
                "publishedAt": item.get("publishedAt", ""),
                "description": (item.get("description") or "").strip(),
                "url": url.strip(),
            }
        )

    if not articles:
        raise ValueError(f"No recent news results found for: {topic}")

    return articles


def _fallback_writer_prompt(topic, articles):
    lines = [
        "You are writing a LinkedIn post about a current news topic.",
        f"Topic: {topic}",
        "",
        "Use these verified sources and avoid claims outside them:",
    ]
    for idx, article in enumerate(articles, 1):
        lines.append(
            f"{idx}. {article['title']} | {article['source']} | {article['publishedAt']} | {article['url']}"
        )
    lines.extend(
        [
            "",
            "Write a concise, factual post with:",
            "- 1 hook line",
            "- 3-5 key points",
            "- Practical impact for developers/business",
            "- Clear source mention section at end",
        ]
    )
    return "\n".join(lines)


def _fallback_image_prompt(topic, post, brands="", person_name=""):
    return build_news_image_prompt(topic, post, brands=brands, person_name=person_name)


def _bedrock_text(prompt):
    response = bedrock.converse(
        modelId=BEDROCK_TEXT_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
    )
    return response["output"]["message"]["content"][0]["text"]


def generate_linkedin_post(topic, research_notes, writer_prompt):
    prompt = build_linkedin_post_prompt(
        topic=topic,
        research_notes=research_notes,
        writer_prompt=writer_prompt,
    )
    post = clean_linkedin_formatting(_bedrock_text(prompt))
    return post


def build_news_prompt_package(topic, person_name="", logo_text=""):
    articles = fetch_news(topic)
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

    prompt = build_news_prompt(
        topic=topic,
        person_name=person_name or "",
        logo_text=logo_text or "",
        articles_json=articles_json,
    )

    response = _bedrock_text(prompt)
    raw_output = response

    parsed = {}
    try:
        parsed = json.loads(_extract_json_block(raw_output))
    except Exception:
        parsed = {
            "research_notes": "Auto-fallback research notes generated from web sources.",
            "writer_prompt": _fallback_writer_prompt(topic, articles),
            "brands": "",
            "person_name": person_name or "",
        }

    sources = [
        {
            "title": article["title"],
            "source": article["source"],
            "publishedAt": article["publishedAt"],
            "url": article["url"],
        }
        for article in articles
    ]

    writer_prompt = parsed.get(
        "writer_prompt",
        _fallback_writer_prompt(topic, articles),
    )
    brands = parsed.get("brands", "")
    news_person_name = parsed.get("person_name", person_name or "")
    research_notes = parsed.get("research_notes", "")
    linkedin_post = generate_linkedin_post(topic, research_notes, writer_prompt)
    image_prompt = _fallback_image_prompt(
        topic,
        linkedin_post,
        brands=brands,
        person_name=news_person_name,
    )

    print("\n" + "=" * 60)
    print(f"NEWS TOPIC: {topic}")
    print("=" * 60)
    print("\nWRITER PROMPT\n" + "-" * 60)
    print(writer_prompt)
    print("\nLINKEDIN POST\n" + "-" * 60)
    print(linkedin_post)
    print("\nIMAGE PROMPT\n" + "-" * 60)
    print(image_prompt)
    print("=" * 60 + "\n")

    return {
        "topic": topic,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "research_notes": research_notes,
        "writer_prompt": writer_prompt,
        "linkedin_post": linkedin_post,
        "image_prompt": image_prompt,
        "sources": sources,
    }


def finalize_news_draft(topic, package):
    draft_id, filename = save_news_draft_and_send(
        topic=topic,
        linkedin_post=package["linkedin_post"],
        image_prompt=package["image_prompt"],
    )
    return draft_id, filename


def format_sources_for_telegram(sources):
    lines = ["Sources used:"]
    for idx, item in enumerate(sources, 1):
        lines.append(
            f"{idx}. {item.get('title', 'Untitled')}\n"
            f"   {item.get('source', 'Unknown')} | {item.get('publishedAt', '')}\n"
            f"   {item.get('url', '')}"
        )
    return "\n".join(lines)
