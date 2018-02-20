import sys

import click

from di.checks import Checks
from di.commands.utils import CONTEXT_SETTINGS, echo_failure
from di.docker import run_check
from di.settings import load_settings
from di.utils import CHECKS_DIR, DEFAULT_NAME


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Runs a check')
@click.argument('check_name')
@click.argument('flavor', required=False, default=DEFAULT_NAME)
@click.argument('instance_name', required=False, default=DEFAULT_NAME)
@click.option('--direct', '-d', is_flag=True)
@click.option('--location', '-l', default='')
def check(check_name, flavor, instance_name, direct, location):
    """Runs a check.

    \b
    $ di check nginx
    """
    if check_name not in Checks:
        echo_failure('Check `{}` is not yet supported.'.format(check_name))
        sys.exit(1)

    if flavor not in Checks[check_name]:
        echo_failure('Flavor `{}` is not yet supported.'.format(flavor))
        sys.exit(1)

    check_class = Checks[check_name][flavor]
    settings = load_settings()
    location = location or settings.get('location', CHECKS_DIR)

    location = check_class.get_location(
        location, instance_name=instance_name, direct=direct
    )
    container_name = check_class.get_container_name(
        instance_name=instance_name, location=location, direct=direct
    )

    error = run_check(container_name, check_name)
    if error:
        echo_failure('An unexpected Docker error (status {}) has occurred.'.format(error))
        sys.exit(error)
