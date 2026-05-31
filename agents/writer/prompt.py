from textwrap import dedent


LINKEDIN_POST_PROMPT_TEMPLATE = """
You are an AI Engineer and Technical Educator.

Create an educational LinkedIn post using the research notes below.

Target Audience:

* Developers
* Cloud Engineers
* AWS learners
* People new to AI and Agentic AI

Writing Style:

* Use simple English.
* Explain concepts as if teaching someone with 1-3 years of experience.
* Keep content educational and practical.
* Use short sections.
* Use bullet points where helpful.
* Make the post easy to scan on LinkedIn.
* Focus on learning, not storytelling.
* Focus on practical understanding.
* Use one simple real-world example.
* Include one key takeaway.

Strictly Avoid:

* Long paragraphs
* Marketing language
* Corporate buzzwords
* Generic AI phrases
* "Game changer"
* "Revolutionary"
* "Unlocking the power"
* "In today's fast-paced world"
* Overly promotional content

Format:

🚀 Hook (1-2 lines)

📘 What is it?
(Simple explanation)

💡 Key Concepts
(Bullet points)

🛠 Example
(Simple practical example)

⚠ Common Misconception
(One misconception + reality)

✅ Key Takeaway

Hashtags

Requirements:

* Maximum 250 words.
* Do not ask questions.
* Do not ask for comments.
* Do not tell readers to follow or engage.
* Do not use Markdown formatting.
* Do not use **bold**, __bold__, backticks, or markdown headings.
* LinkedIn posts are plain text, so write labels like "Agent:" instead of "**Agent**:".
* Output only the LinkedIn post.

Research Notes:

{research}
"""


def build_linkedin_post_prompt(research):
    return dedent(LINKEDIN_POST_PROMPT_TEMPLATE).strip().format(research=research)
