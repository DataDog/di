import sys

import click

from di.checks import Checks
from di.commands.utils import CONTEXT_SETTINGS, echo_failure, echo_success, echo_waiting
from di.docker import check_dir_remove_containers, check_dir_stop
from di.settings import load_settings
from di.utils import CHECKS_DIR, DEFAULT_NAME


@click.command(context_settings=CONTEXT_SETTINGS, short_help='Stops an integration')
@click.argument('check_name')
@click.argument('flavor', required=False, default=DEFAULT_NAME)
@click.argument('instance_name', required=False, default=DEFAULT_NAME)
@click.option('--remove', '-r', is_flag=True)
@click.option('--direct', '-d', is_flag=True)
@click.option('--location', '-l', default='')
def stop(check_name, flavor, instance_name, remove, direct, location):
    """Stops an integration.

    \b
    $ di stop -r nginx
    Stopping containers... success!
    Removing containers... success!
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

    echo_waiting('Stopping containers... ', nl=False)
    output, error = check_dir_stop(location)
    if error:
        click.echo()
        click.echo(output.rstrip())
        echo_failure('An unexpected Docker error (status {}) has occurred.'.format(error))
        sys.exit(error)
    echo_success('success!')

    if remove:
        echo_waiting('Removing containers... ', nl=False)
        output, error = check_dir_remove_containers(location)
        if error:
            click.echo()
            click.echo(output.rstrip())
            echo_failure('An unexpected Docker error (status {}) has occurred.'.format(error))
            sys.exit(error)
        echo_success('success!')
