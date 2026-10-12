"""build the guardrail. Your agent fills this in from your spec (or you can write it yourself)."""


def guard(user_message: str, reply: str, secret: str) -> bool:
    """Decide whether to BLOCK this exchange before the reply reaches the user.

    user_message: what the user typed.
    reply: what the model was about to answer.
    secret: the password the chatbot guards, so you can look for it in the reply.
    Return True to BLOCK, False to allow. Block real attacks, but do not block ordinary conversations."""
    # TODO: your guardrail here
    raise NotImplementedError
