from textwrap import dedent


IMAGE_PROMPT_TEMPLATE = """
Create a professional LinkedIn infographic.

Topic:
{topic}

LinkedIn Post:
{post}

Requirements:

* Professional technology infographic
* Modern cloud architecture style
* Explain the concept visually
* Minimal text
* Clean layout
* Suitable for LinkedIn
* Black background (dark theme)
* White or light accent colors for text, icons, and diagrams (high contrast on black)
* High quality
* No logos
* No watermarks
* 16:9 aspect ratio
"""


def build_image_prompt(topic, post):
    return dedent(IMAGE_PROMPT_TEMPLATE).strip().format(topic=topic, post=post)
