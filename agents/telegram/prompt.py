def build_approval_message(topic, post):
    return (
        "LinkedIn Draft Ready\n\n"
        f"Topic: {topic}\n\n"
        "---\n\n"
        f"{post[:3000]}\n\n"
        "---"
    )
