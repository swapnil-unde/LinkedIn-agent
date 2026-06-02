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


NEWS_IMAGE_PROMPT_TEMPLATE = """
Create a professional LinkedIn infographic.

Topic:
{topic}

LinkedIn Post:
{post}

Branding guidance:
{branding}

Requirements:

* Professional technology infographic
* Modern cloud architecture style
* Explain the news story visually
* Minimal text
* Clean layout
* Suitable for LinkedIn
* Black background (dark theme)
* White or light accent colors for text, icons, and diagrams (high contrast on black)
* High quality
* No watermarks
* 16:9 aspect ratio
* When companies or brands are central to this news, include their name and stylized logo text in the visual
* When a specific person is central to the story, include their name subtly
* Do not refuse branding when the story is about those companies or people
"""


def build_news_image_prompt(topic, post, brands="", person_name=""):
    branding_lines = []
    if brands:
        branding_lines.append(
            f"* Include stylized logo text and branding for: {brands}"
        )
    if person_name:
        branding_lines.append(
            f"* Include person name subtly when relevant: {person_name}"
        )
    if not branding_lines:
        branding_lines.append(
            "* Include stylized logo text for any companies central to this news story"
        )

    return dedent(NEWS_IMAGE_PROMPT_TEMPLATE).strip().format(
        topic=topic,
        post=post,
        branding="\n".join(branding_lines),
    )
