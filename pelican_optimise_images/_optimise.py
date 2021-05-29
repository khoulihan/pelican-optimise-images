
import math
from PIL import Image


def optimise(image_file, max_width=640, jpeg_quality=75, webp_quality=65, lossless=None):
    """
    Optimise a single image into a set for progressive delivery to a web
    browser.
    """
    with Image.open(image_file) as image:
        if max_width < image.width:
            image = image.resize((max_width, math.floor(image.height * (max_width / image.width))))
        rgbimage = image.convert('RGB')

        if lossless == None:
            lossless = image_file.suffix.lower() == '.png'
        else:
            lossless = False

        if not lossless:
            compatible_file = image_file.with_name("{}_{}{}".format(image_file.stem, max_width, image_file.suffix)).with_suffix('.jpg')
            rgbimage.save(compatible_file, quality=jpeg_quality, optimize=True)
        else:
            compatible_file = image_file.with_name("{}_{}{}".format(image_file.stem, max_width, image_file.suffix)).with_suffix('.png')
            # Original rather than RGB image is used here, as the original might
            # have been indexed.
            image.save(compatible_file, optimize=True)

        optimised_file = image_file.with_name("{}_{}{}".format(image_file.stem, max_width, image_file.suffix)).with_suffix('.webp')
        rgbimage.save(optimised_file, quality=webp_quality, method=6, lossless=lossless)

    return compatible_file, optimised_file
