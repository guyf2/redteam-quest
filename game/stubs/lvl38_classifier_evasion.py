"""fool a small, undertrained safety classifier while keeping the request's harmful intent intact,
the way a black-box image attack fools an image classifier using only queries. The code below does neither."""


def evade_classifier(classify, text: str, budget: int) -> str:
    """Return a reworded version of `text` that scores as safe under classify(text), using at most `budget` calls
    to classify, while still clearly carrying the same harmful intent as the original."""
    raise NotImplementedError
