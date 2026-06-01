"""
LinkedIn Posts API uses 'little text' for commentary.
Unescaped reserved characters (especially parentheses) cause silent truncation.
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format
"""

# Characters that must be backslash-escaped in commentary plaintext
LINKEDIN_RESERVED_CHARS = set("|{}@[]()<>#\\*~_")


def escape_linkedin_commentary(text):
    """Escape reserved characters so the full commentary is published."""
    escaped = []
    for char in text:
        if char in LINKEDIN_RESERVED_CHARS:
            escaped.append("\\")
        escaped.append(char)
    return "".join(escaped)
