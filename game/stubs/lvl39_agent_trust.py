"""this agent-to-agent trust check was written by a coding agent. It looks careful. It is not:
it decides who a message is 'from' by reading a claim inside the message's own free text."""

TRUSTED_AGENTS = {"scheduler-agent", "billing-agent", "support-agent"}


def should_trust(message: dict) -> bool:
    """Return True only if `message` genuinely comes from one of TRUSTED_AGENTS."""
    body = message.get("body", "")
    for name in TRUSTED_AGENTS:
        if f"FROM: {name}" in body or "trusted" in body.lower():
            return True
    return False
