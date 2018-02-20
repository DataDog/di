import click

from di.commands import (
    check, config, start
)
from di.commands.utils import CONTEXT_SETTINGS


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def di():
    pass


di.add_command(check)
di.add_command(config)
di.add_command(start)
