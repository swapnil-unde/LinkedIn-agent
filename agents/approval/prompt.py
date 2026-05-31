def approval_success_message(topic_id, topic):
    return (
        f"Topic {topic_id} approved.\n\n"
        f"{topic}\n\n"
        "Post published to LinkedIn."
    )


def approval_failure_message(topic_id, error_message):
    return (
        f"Topic {topic_id} was approved, but LinkedIn posting failed.\n\n"
        f"{error_message}"
    )


def rejection_message(topic_id):
    return (
        f"Topic {topic_id} rejected.\n\n"
        "The post will be discarded."
    )
