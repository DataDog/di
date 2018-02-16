import click

import toml

from di.commands.utils import CONTEXT_SETTINGS, echo_info, echo_success
from di.settings import (
    SETTINGS_FILE, copy_default_settings, load_settings, restore_settings,
    save_settings, update_settings
)
from di.utils import string_to_toml_type


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True,
             short_help='Locates, updates, or restores the config file')
@click.option('-u', '--update', is_flag=True,
              help='Updates the config file with any new fields.')
@click.option('--restore', is_flag=True,
              help='Restores the config file to default settings.')
@click.pass_context
def config(ctx, update, restore):
    """Locates, updates, or restores the config file.

    \b
    $ di config
    Settings location: /home/ofek/.local/share/di-dev/settings.toml
    """
    if update:
        update_settings()
        echo_success('Settings were successfully updated.')

    if restore:
        restore_settings()
        echo_success('Settings were successfully restored.')

    if not ctx.invoked_subcommand:
        echo_info('Settings location: ' + SETTINGS_FILE)


@config.command('set', context_settings=CONTEXT_SETTINGS,
                short_help='Assigns values to config file entries')
@click.argument('key')
@click.argument('value')
def set_value(key, value):
    """Assigns values to config file entries.

    \b
    $ di config set nginx.version 1.13.8
    New setting:
    [nginx]
    version = "1.13.8"
    """
    user_settings = load_settings()

    updated_settings = {}
    new_settings = updated_settings
    data = [value, *key.split('.')[::-1]]
    key = data.pop()
    value = data.pop()

    # Consider dots as keys
    while data:
        new_settings[key] = {value: ''}
        new_settings = new_settings[key]
        key = value
        value = data.pop()
    new_settings[key] = string_to_toml_type(value)

    user_settings.update(updated_settings)
    save_settings(user_settings)

    echo_success('New setting:')
    echo_info(toml.dumps(updated_settings))
