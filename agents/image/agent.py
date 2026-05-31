import base64
import json
import os
import re
from datetime import datetime

import boto3

from agents.image.prompt import build_image_prompt
from config import AWS_REGION, BEDROCK_IMAGE_MODEL_ID, IMAGES_DIR


bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


def generate_image(topic, post):
    prompt = build_image_prompt(topic, post)

    print("\nGenerated Image Prompt:\n")
    print(prompt)

    # response = bedrock.invoke_model(
    #     modelId=BEDROCK_IMAGE_MODEL_ID,
    #     body=json.dumps({
    #         "taskType": "TEXT_IMAGE",
    #         "textToImageParams": {
    #             "text": prompt,
    #         },
    #         "imageGenerationConfig": {
    #             "numberOfImages": 1,
    #             "height": 1024,
    #             "width": 1792,
    #         },
    #     }),
    # )
    #
    # response_body = json.loads(response["body"].read())
    # image_bytes = base64.b64decode(response_body["images"][0])
    #
    # os.makedirs(IMAGES_DIR, exist_ok=True)
    # safe_topic = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    # filename = os.path.join(
    #     IMAGES_DIR,
    #     f"{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
    # )
    #
    # with open(filename, "wb") as f:
    #     f.write(image_bytes)
    #
    # print(f"\nImage saved: {filename}")

    return prompt
