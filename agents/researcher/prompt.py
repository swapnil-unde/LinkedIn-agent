from textwrap import dedent


RESEARCH_PROMPT_TEMPLATE = """
You are a senior cloud architect and technical researcher.

Topic: {topic}

Create research notes.

Provide:

1. What is it?
2. Why does it matter?
3. Key concepts
4. Common misconceptions
5. Real-world use cases
6. Practical implementation considerations
7. Interesting facts
8. Lessons a developer should know
9. Explain it as if teaching a developer with 1 year experience.
10. Include simple examples.
11. Avoid vendor marketing language.
12. Focus on practical understanding rather than feature lists.

Use simple language.

Output as structured research notes.
"""


def build_research_prompt(topic):
    return dedent(RESEARCH_PROMPT_TEMPLATE).strip().format(topic=topic)
