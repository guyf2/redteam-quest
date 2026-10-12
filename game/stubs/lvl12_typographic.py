"""Level 12: typographic attack. Your agent fills this in from your spec (or you can write it yourself)."""
from PIL import Image, ImageDraw, ImageFont


def typographic_attack(image: Image.Image, target_name: str) -> Image.Image:
    """image: an RGB photo (224 x 224). target_name: the class you want the vision-language model to see,
    for example 'dog'. Return a new RGB image of the SAME size.
    Rules: you may only add a small label. At most 8% of the pixels may differ from the original."""
    # TODO: your attack here
    raise NotImplementedError
