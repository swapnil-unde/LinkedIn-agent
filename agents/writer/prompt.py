from textwrap import dedent


FEW_SHOT_EXAMPLES = """
--- EXAMPLE POST 1 (Stop Words) ---

Some of the most common words in English are completely ignored by AI models.

🚀 Post 14 of my Generative AI learning series

In many sentences, some words appear very frequently but add little meaning.

These are called stop words.

Examples include:

• the
• is
• and
• a
• to

For humans these words help grammar.

But for AI models, they often add noise.

Example:

Original sentence:
"AI is transforming the world"

After removing stop words:
["AI", "transforming", "world"]

Real-world analogy:

Imagine highlighting only the important words in a sentence while ignoring filler words.

Key takeaway:
Stop words are common words removed from text so AI models focus on meaningful information.

Next I'll explain:
👉 Stemming vs Lemmatization

Follow the series if you're learning Generative AI.

--- EXAMPLE POST 2 (Bag of Words) ---

One of the earliest NLP techniques ignores grammar completely — and it still works surprisingly well.

🚀 Post 16 of my Generative AI learning series

One of the earliest NLP techniques is called Bag of Words.

It converts text into numbers so machines can analyze it.

How it works:

Step 1:
Create a vocabulary of all words in a dataset.

Step 2:
Count how many times each word appears in a document.

Example:

Sentence:
"AI is powerful"

Vocabulary:
AI | is | powerful

Vector:
[1,1,1]

Real-world analogy:

Think of a bag filled with words.
We ignore grammar and only count how many times each word appears.

Key takeaway:
Bag of Words converts text into numerical vectors based on word frequency.

Next I'll explain:
👉 TF-IDF

Follow the series if you're learning Generative AI.
"""


LINKEDIN_POST_PROMPT_TEMPLATE = """
You are an AI Engineer and Technical Educator writing a LinkedIn learning series.

Create a new post in the SAME style, structure, and tone as the few-shot examples below.

Today's topic: {topic_name}
Post number: {post_number}
Next topic (teaser): {next_topic_name}

Target audience:
• Developers and engineers learning Generative AI
• Readers with about 1-3 years of experience

Required structure (match the examples closely):

1. Opening hook (1-2 short lines that create curiosity about today's topic)
2. Blank line
3. 🚀 Post {post_number} of my Generative AI learning series
4. Blank line
5. Short intro explaining the concept in simple English
6. Core explanation (use bullets, numbered steps, or short sections as needed)
7. Example: (concrete, simple example from the research notes)
8. Real-world analogy: (one relatable analogy)
9. Key takeaway: (one clear sentence starting with "Key takeaway:")
10. Next I'll explain:
    👉 {next_topic_name}
11. Blank line
12. Follow the series if you're learning Generative AI.
13. Blank line
14. Hashtags (final line): 4-6 relevant hashtags for today's topic and this series
    Example: #GenerativeAI #NLP #MachineLearning #AI #TFIDF

Writing rules:
• Use simple English; teach, do not market
• Short lines and whitespace; easy to scan on LinkedIn
• Plain text only — no Markdown bold, headings, or backticks
• Match the examples in length: about 900-1100 characters including hashtags (roughly 150-220 words)
• Keep the Example section short (one mini example only, max 6-8 lines — no long math chains)
• Do not use parentheses in bullets or labels — write "TF:" not "(TF):" (LinkedIn API breaks on unescaped parentheses)
• Use simple dashes for bullets: "- item" not "• item" is also fine
• Hashtags: every tag must start with # (example: #GenerativeAI #NLP #AI)
• Do not ask questions or ask for comments
• Always include the full closing: Next I'll explain, Follow the series, and hashtags (never end mid-post)
• Always end with the hashtag line (step 14)
• Output only the complete LinkedIn post — nothing may be cut off

Strictly avoid:
• Marketing buzzwords ("game changer", "revolutionary", "unlock the power")
• Long dense paragraphs
• Multiple worked calculations or step-by-step formulas (one simple example only)
• Deviating from the example structure

Few-shot examples (follow this pattern):

{few_shot_examples}

Research notes for today's post:

{research}
"""


def build_linkedin_post_prompt(research, topic_name, post_number, next_topic_name):
    next_topic_name = next_topic_name or "the next topic in this series"
    return dedent(LINKEDIN_POST_PROMPT_TEMPLATE).strip().format(
        topic_name=topic_name,
        post_number=post_number,
        next_topic_name=next_topic_name,
        few_shot_examples=dedent(FEW_SHOT_EXAMPLES).strip(),
        research=research,
    )
