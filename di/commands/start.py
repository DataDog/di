import sys

import click

from di.checks import Checks
from di.commands.utils import (
    UNKNOWN_OPTIONS, echo_failure, echo_info, echo_success
)
from di.settings import load_settings
from di.structures import DockerCheck, VagrantCheck
from di.utils import DEFAULT_NAME, resolve_path


@click.command(context_settings=UNKNOWN_OPTIONS,
               short_help='Starts a fully functioning integration')
@click.argument('check_name')
@click.argument('flavor', required=False, default=DEFAULT_NAME)
@click.argument('instance_name', required=False, default=DEFAULT_NAME)
@click.option('--options', '-o', nargs=2, multiple=True)
@click.option('--api_key', '-key')
@click.option('--location', '-l', default='')
@click.option('--dev', is_flag=True)
@click.option('--core', default='')
@click.option('--extras', default='')
@click.option('--agent', '-a', type=click.INT)
@click.option('--image', '-i', default='')
def start(check_name, flavor, instance_name, options, api_key, location, dev, core, extras, agent, image):
    """Starts a fully functioning integration.

    \b
    $ di config set nginx.version 1.13.8
    New setting:
    [nginx]
    version = "1.13.8"
    """
    if check_name not in Checks:
        echo_failure('Check `{}` is not yet supported.'.format(check_name))
        sys.exit(1)

    if flavor not in Checks[check_name]:
        echo_failure('Flavor `{}` is not yet supported.'.format(flavor))
        sys.exit(1)

    check_class = Checks[check_name][flavor]
    settings = load_settings()














