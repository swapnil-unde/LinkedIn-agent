import os
import re
from datetime import datetime

import boto3

from agents.researcher.prompt import build_research_prompt
from agents.writer.agent import generate_linkedin_post
from config import (
    AWS_REGION,
    BEDROCK_TEXT_MODEL_ID,
    DYNAMODB_TABLE_NAME,
    RESEARCH_DIR,
    TOPIC_ID,
)


dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


def run_research_agent(topic_id=TOPIC_ID):
    response = table.get_item(
        Key={"topicId": topic_id},
    )

    topic = response["Item"]["topicName"]
    topic_id = response["Item"]["topicId"]
    print(f"Researching topic: {topic}")

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
