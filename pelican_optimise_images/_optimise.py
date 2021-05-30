
import math
from PIL import Image
import hitherdither


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


def _try_variations(image, image_file, description):
    image = image.resize((640, math.floor(image.height * (640 / image.width))))
    rgbimage = image.convert('RGB')
    out_file = image_file.with_name("{}_{}_baseline{}".format(image_file.stem, description, image_file.suffix)).with_suffix('.jpg')
    rgbimage.save(out_file, optimize=True)

    size = round(out_file.stat().st_size / 1024, 1)
    print("Baseline 75% JPEG, Size: {size}kb".format(size=size))
    print()
    print("![{file_name}]({{static}}/images/image-optimisation/{file_name} \"{file_name}: {size}kb\")".format(file_name=out_file.name, size=size))
    print()

    out_file = image_file.with_name("{}_{}_baseline{}".format(image_file.stem, description, image_file.suffix)).with_suffix('.webp')
    rgbimage.save(out_file, lossless=False, method=6)
    size = round(out_file.stat().st_size / 1024, 1)
    print("Baseline 80% WEBP, Size: {size}kb".format(size=size))
    print()
    print("![{file_name}]({{static}}/images/image-optimisation/{file_name} \"{file_name}: {size}kb\")".format(file_name=out_file.name, size=size))
    print()

    out_file = image_file.with_name("{}_{}_q65{}".format(image_file.stem, description, image_file.suffix)).with_suffix('.webp')
    rgbimage.save(out_file, lossless=False, method=6, quality=70)
    size = round(out_file.stat().st_size / 1024, 1)
    print("65% WEBP, Size: {size}kb".format(size=size))
    print()
    print("![{file_name}]({{static}}/images/image-optimisation/{file_name} \"{file_name}: {size}kb\")".format(file_name=out_file.name, size=size))
    print()

    halved = rgbimage.resize((320, math.floor(image.height * (320 / image.width))))

    for palette_size in (32,):
        palette = hitherdither.palette.Palette.create_by_median_cut(halved, n=palette_size)
        for dither in ['bayer']:
            for order in (2,):
                if dither == 'bayer':
                    thresholds = {
                        '8-1-8': [256/8, 256, 256/8],
                    }
                    for threshold in thresholds:
                        img_dithered = hitherdither.ordered.bayer.bayer_dithering(halved, palette, thresholds[threshold], order=order)
                        for format in ('.webp', '.png'):
                            out_file = image_file.with_name("{}_{}_halved_pal{}_dith{}_order{}_thresh{}".format(
                                image_file.stem,
                                description,
                                palette_size,
                                dither,
                                order,
                                threshold,
                                image_file.suffix
                            )).with_suffix(format)
                            img_dithered.save(
                                out_file,
                                optimize=True,
                                lossless=False,
                                method=6,
                                quality=80
                            )
                            size = round(out_file.stat().st_size / 1024, 1)
                            print("Palette: {palette}, Dither: {dither}, Threshold: {threshold}, Order: {order}, Size: {size}kb".format(palette=palette_size, dither=dither, threshold=threshold, order=order, size=size))
                            print()
                            print("![{file_name}]({{static}}/images/image-optimisation/{file_name} \"{file_name}: {size}kb\")".format(file_name=out_file.name, size=size))
                            print()
                else:
                    if dither == 'yliluomas':
                        img_dithered = hitherdither.ordered.yliluoma.yliluomas_1_ordered_dithering(halved, palette, order=order)
                    elif dither in ('floyd-steinberg', 'atkinson', 'sierra3', 'stucki', 'burkes'):
                        img_dithered = hitherdither.diffusion.error_diffusion_dithering(halved, palette, method=dither, order=order)
                    out_file = image_file.with_name("{}_{}_halved_pal{}_dith{}_order{}".format(
                        image_file.stem,
                        description,
                        palette_size,
                        dither,
                        order,
                        image_file.suffix
                    )).with_suffix('.png')
                    img_dithered.save(
                        out_file,
                        optimize=True
                    )
                    size = round(out_file.stat().st_size / 1024, 1)
                    print("Palette: {palette}, Dither: {dither}, Order: {order}, Size: {size}kb".format(palette=palette_size, dither=dither, order=order, size=size))
                    print()
                    print("![{file_name}]({{static}}/images/image-optimisation/{file_name} \"{file_name}: {size}kb\")".format(file_name=out_file.name, size=size))
                    print()


def prepare_samples(image_file):
    with Image.open(image_file) as image:
        _try_variations(
            image,
            image_file,
            "alpha"
        )
