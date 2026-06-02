from textwrap import dedent


NEWS_PROMPT_TEMPLATE = """
You are a technical news research assistant.

Topic: {topic}
Provided person name for image branding (optional): {person_name}
Provided logo text for image branding (optional): {logo_text}

You are given recent web/news results as JSON:
{articles_json}

Task:
1. Build concise research notes for LinkedIn post drafting.
2. Create a writer prompt that can be sent to a post-writer model.
3. Identify brands and people for image branding:
   - "brands": comma-separated company/brand names central to the news (e.g. "NVIDIA, HP, Microsoft, ASUS"), or empty string if none
   - "person_name": name of a person central to the story (CEO, founder, speaker), or empty string if none
4. Keep all facts grounded in sources and avoid unverifiable claims.

Output format requirements:
- Return ONLY strict JSON.
- Keys: "research_notes", "writer_prompt", "brands", "person_name".
- "research_notes" must include a "Sources:" section with URLs.
"""


def build_news_prompt(topic, person_name, logo_text, articles_json):
    return dedent(NEWS_PROMPT_TEMPLATE).strip().format(
        topic=topic,
        person_name=person_name,
        logo_text=logo_text,
        articles_json=articles_json,
    )


LINKEDIN_POST_PROMPT_TEMPLATE = """
You are writing a LinkedIn post about a current news topic.

Topic: {topic}

Research notes:
{research_notes}

Writer guidance:
{writer_prompt}

Rules:
- Factual, concise, and easy to scan on LinkedIn
- Start with a hook line, then key points and practical impact
- Plain text only — no Markdown bold, headings, or backticks
- Mention sources or publication names at the end
- About 800-1200 characters
- Do not invent facts beyond the research notes

Output only the complete LinkedIn post.
"""


def build_linkedin_post_prompt(topic, research_notes, writer_prompt):
    return dedent(LINKEDIN_POST_PROMPT_TEMPLATE).strip().format(
        topic=topic,
        research_notes=research_notes,
        writer_prompt=writer_prompt,
    )
