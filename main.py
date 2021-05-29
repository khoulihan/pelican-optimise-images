
import shutil
from pathlib import Path
import click
from pelican_optimise_images import optimise as _opt


def backup_file(file_path):
    destination = file_path.with_name("{}.bak".format(file_path.name))
    shutil.copyfile(file_path, destination)


def _style_saving_percentage(saving):
    return click.style(
        "{:.1%}".format(saving),
        fg='red' if saving > 1.0 else 'green'
    )


@click.command()
@click.option(
    '--max-width',
    default=640,
    help="the width to resize the image to"
)
@click.option(
    '--webp-quality',
    default=65,
    help="quality setting to use for WEBP export"
)
@click.option(
    '--jpeg-quality',
    default=75,
    help="quality setting to use for JPEG export"
)
@click.option(
    '--force-lossless',
    is_flag=True,
    help="force lossless output format"
)
@click.option(
    '--force-lossy',
    is_flag=True,
    help="force lossy output format"
)
@click.argument(
    'image_file',
    type=click.Path(exists=True, dir_okay=False)
)
def optimise(image_file, max_width, webp_quality, jpeg_quality, force_lossless, force_lossy):
    """
    Optimise the specified IMAGE_FILE.
    """
    if force_lossy and force_lossless:
        raise click.BadParameter(
            "--force-lossy and --force-lossless are mutually exclusive"
        )
    image_file_path = Path(image_file)
    if not force_lossy and not force_lossless:
        lossless = image_file_path.suffix.lower() == '.png'
    else:
        lossless = force_lossless
    compatible_file, optimised_file = _opt(
        image_file_path,
        max_width=max_width,
        webp_quality=webp_quality,
        jpeg_quality=jpeg_quality,
        lossless=lossless,
    )
    (original_size, baseline_size, optimal_size) = map(
        lambda i: round(i.stat().st_size / 1024, 1),
        (image_file_path, compatible_file, optimised_file)
    )

    # Analysis of results
    if baseline_size > original_size:
        click.secho(
            "Warning: the output compatible format file ({}kB) is larger than" \
            " the original ({}kB)".format(baseline_size, original_size),
            fg='yellow',
        )
    if optimal_size > baseline_size:
        click.secho(
            "Warning: the output optimised format file ({}kB) is larger than" \
            " the compatible version ({}kB)".format(optimal_size, baseline_size),
            fg='yellow',
        )
    click.echo("Optimisation results:")
    click.echo("")
    click.echo("Original size:\t\t{}kB".format(
        click.style(original_size, fg='cyan')
    ))
    click.echo("Compatible size:\t{}kB ({})".format(
        click.style(baseline_size, fg='cyan'),
        _style_saving_percentage((original_size - baseline_size) / original_size)
    ))
    click.echo("Optimised size:\t\t{}kB ({})".format(
        click.style(optimal_size, fg='cyan'),
        _style_saving_percentage((original_size - optimal_size) / original_size)
    ))
