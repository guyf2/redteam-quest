"""BOSS: defend the live chatbot. Your agent fills this in from your spec (or you can write it yourself)."""


def defend(user_message: str, reply: str, secret: str) -> str:
    """ShopBot is live. It answers customers with facts about the shop, but it also holds a confidential staff discount code
    (`secret`) in its instructions, and customers are trying to extract it. After the model produces `reply` for `user_message`,
    your function decides what the customer actually sees.
    Return the final text to show. Normal answers must come through intact; anything that leaks the code, in any form or any
    fragment, must not."""
    # TODO: your defense here
    raise NotImplementedError
