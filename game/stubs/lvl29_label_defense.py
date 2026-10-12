"""Level 29 (boss): stop the label trick. Your agent fills this in from your spec (or you can write it yourself)."""
from PIL import Image


def sanitize(image: Image.Image) -> Image.Image:
    """An online marketplace classifies seller photos with CLIP. Sellers have learned to write a misleading word on the photo
    (a label in a corner, in several styles and sizes) so listings land in the wrong category.
    Take the uploaded RGB photo (224 x 224) and return the cleaned RGB photo (224 x 224) that the classifier will see.
    It must neutralise the writing WITHOUT ruining ordinary photos."""
    # TODO: your sanitizer here
    raise NotImplementedError
