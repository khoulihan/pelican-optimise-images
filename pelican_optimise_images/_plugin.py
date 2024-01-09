
from pathlib import Path
# TODO: Imports are supposed to be wrapped in try catch blocks, with the
# plugin disabled on failure
import bs4
from pelican import signals
from ._optimise import optimise

__all__ = ['register']

# Settings and context
_output_path = None
_root_url = None
_optimisation_specs = {}
_create_captions = True


def _retrieve_settings(p):
    global _output_path, _root_url, _optimisation_specs, _create_captions

    _output_path = Path(p.output_path)
    _root_url = p.settings.get('SITEURL', '')
    _optimisation_specs = p.settings.get('POI_OPTIMISATIONS', {})
    _create_captions = p.settings.get('POI_CREATE_CAPTIONS', True)


def _process_file(f):
    soup = None
    modified = False

    def _handle_imgs(imgs):
        nonlocal modified, soup
        global _output_path, _root_url, _optimisation_specs, _create_captions

        for img in imgs:
            src = img['src']
            classes = img.get('class', [])
            if 'poi-no-optimise' not in classes and src.endswith(('.png', '.jpg', '.jpeg')):
                if _root_url and src.startswith(_root_url):
                    src = src[len(_root_url):]
                elif src.startswith("http"):
                    # If the src was absolute but didn't match the root url
                    # or no root url is set, then we can't tell if it is a
                    # local image or not
                    continue
                src = src.lstrip('/')
                src_path = _output_path / src

                relevant_classes = [c[4:] for c in classes if c.startswith('poi-') ]
                optimisations = _optimisation_specs.get('default', {}).copy()
                for c in relevant_classes:
                    optimisations.update(_optimisation_specs.get(c, {}))

                compat, optimal = optimise(src_path, **optimisations)

                replacement = None
                new_img = None
                if 'title' in img.attrs and _create_captions:
                    replacement, new_img = _create_figure(compat, optimal, img.attrs['title'])
                else:
                    replacement, new_img = _create_picture(compat, optimal)

                for att in img.attrs.keys():
                    if att != 'src':
                        new_img[att] = img[att]

                img.replace_with(replacement)
                modified = True

    def _create_picture(compat, optimal):
        picture = bs4.BeautifulSoup("""
            <picture>
                <source type="image/webp" srcset="{optimal}"/>
                <source type="{compat_type}" srcset="{compat}"/>
                <img src="{compat}"/>
            </picture>
            """.format(
                optimal="{}/{}".format(_root_url, str(optimal)[len(str(_output_path)):].lstrip('/')),
                compat="{}/{}".format(_root_url, str(compat)[len(str(_output_path)):].lstrip('/')),
                compat_type="image/png" if compat.suffix == '.png' else "image/jpeg"
            ),
            features="lxml"
        )
        return picture.picture, picture.img

    def _create_figure(compat, optimal, caption):
        picture, img = _create_picture(compat, optimal)
        figure = bs4.BeautifulSoup("""
                <figure>
                    <figcaption>{caption}</figcaption>
                </figure>
            """.format(caption=caption),
            features="lxml"
        )
        figure.figure.insert(0, picture)
        return figure.figure, img

    def _process():
        nonlocal soup, modified
        with open(f) as input:
            soup = bs4.BeautifulSoup(input.read(), features="lxml")

        imgs = soup.find_all('img')
        _handle_imgs(imgs)

        if modified:
            with open(f, 'w') as output:
                output.write(str(soup))

    _process()


# Signal handler
def _finalized(p):
    _retrieve_settings(p)

    for f in _output_path.glob('**/*.htm*'):
        _process_file(f)


# Register function expected by pelican
def register():
    signals.finalized.connect(_finalized)
