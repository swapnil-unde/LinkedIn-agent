import os
import re
from datetime import datetime

import boto3

from agents.researcher.prompt import build_research_prompt
from agents.writer.agent import generate_linkedin_post
from config import (
    AWS_REGION,
    BEDROCK_TEXT_MODEL_ID,
    RESEARCH_DIR,
)
from topics_store import get_active_topic, get_next_active_topic

# --- DynamoDB (replaced by topics.json) ---
# from config import DYNAMODB_TABLE_NAME
# dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
# table = dynamodb.Table(DYNAMODB_TABLE_NAME)
#
# response = table.get_item(Key={"topicId": topic_id})
# topic = response["Item"]["topicName"]
# topic_id = response["Item"]["topicId"]

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


def run_research_agent(topic_id=None):
    """
    Run pipeline for one topic.
    Default: first active row in topics.json (line-by-line order).
    Pass topic_id only to force a specific active topic.
    """
    if topic_id is not None:
        topic_record = get_active_topic(topic_id)
    else:
        topic_record = get_next_active_topic()
    topic_id = topic_record["topicId"]
    topic = topic_record["topicName"]
    print(f"Researching topic: {topic} (id={topic_id}, status={topic_record['status']})")

    prompt = build_research_prompt(topic)
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

    research = response["output"]["message"]["content"][0]["text"]

    print(research)
    safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    filename = os.path.join(
        RESEARCH_DIR,
        f"{safe_topic}_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(research)

    print(f"\nSaved research to {filename}")
    print("\nPassing research to Writer Agent...\n")

    generate_linkedin_post(topic_id, topic, research)
    return research


if __name__ == "__main__":
    run_research_agent()
