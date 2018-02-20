import os
import sys
from collections import OrderedDict

import click

from di.checks import Checks
from di.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting, echo_warning
)
from di.docker import (
    check_dir_start, get_agent_version, pip_install_mounted_check, read_check_example_conf
)
from di.settings import load_settings
from di.structures import DockerCheck, VagrantCheck
from di.utils import (
    CHECKS_DIR, DEFAULT_NAME, dir_exists, file_exists, find_matching_file, get_check_dir,
    get_compose_api_key, read_file, remove_path, resolve_path
)


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Starts a fully functioning integration')
@click.argument('check_name')
@click.argument('flavor', required=False, default=DEFAULT_NAME)
@click.argument('instance_name', required=False, default=DEFAULT_NAME)
@click.option('--options', '-o', nargs=2, multiple=True)
@click.option('--no-instance', '-ni', is_flag=True)
@click.option('--direct', '-d', is_flag=True)
@click.option('--location', '-l', default='')
@click.option('--force', '-f', is_flag=True)
@click.option('--api_key', '-key')
@click.option('--ignore-missing', '-im', is_flag=True)
@click.option('--prod/--dev', default=None)
@click.option('--copy-conf/--use-conf', default=None)
@click.option('--core', default='')
@click.option('--extras', default='')
@click.option('--agent', '-a', type=click.INT)
@click.option('--image', '-i', default='')
def start(check_name, flavor, instance_name, options, no_instance, direct, location, force,
          api_key, ignore_missing, prod, copy_conf, core, extras, agent, image):
    """Starts a fully functioning integration.

    \b
    $ di start nginx
    Using docker image `datadog/agent-dev:master`

    Detecting the agent's major version...
    Agent 6 detected
    Reading the configuration file for `nginx`...

    Creating necessary files...
    Successfully wrote:
      C:\\Users\\Ofek\\AppData\\Local\\di-dev\\checks\\nginx\\stub\\default\\nginx.yaml
      C:\\Users\\Ofek\\AppData\\Local\\di-dev\\checks\\nginx\\stub\\default\\docker-compose.yaml
      C:\\Users\\Ofek\\AppData\\Local\\di-dev\\checks\\nginx\\stub\\default\\status.conf

    Starting containers...
    Success!

    To run this check, do `di check nginx`.
    """
    if check_name not in Checks:
        echo_failure('Check `{}` is not yet supported.'.format(check_name))
        sys.exit(1)

    if flavor not in Checks[check_name]:
        echo_failure('Flavor `{}` is not yet supported.'.format(flavor))
        sys.exit(1)

    check_class = Checks[check_name][flavor]
    options = OrderedDict(options)
    settings = load_settings()

    user_api_key = api_key or settings.get('api_key', '${DD_API_KEY}')
    api_key, evar = get_compose_api_key(user_api_key)
    if not ignore_missing and api_key != user_api_key:
        echo_warning(
            "Environment variable {} doesn't exist; a well-formatted "
            "fake API key will be used instead.".format(evar)
        )
    else:
        api_key = user_api_key

    given_location = location
    location = resolve_path(given_location or settings.get('location', CHECKS_DIR))
    prod = prod if prod is not None else settings.get('mode', 'prod') == 'prod'
    copy_conf = copy_conf if copy_conf is not None else settings.get('copy_conf', True)

    if prod:
        check_dir = None
        conf_path = ''
    else:
        core = core or settings.get('core', '')
        extras = extras or settings.get('extras', '')
        core_check_dir = os.path.join(resolve_path(core), check_name)
        extras_check_dir = os.path.join(resolve_path(extras), check_name)

        if dir_exists(core_check_dir):
            check_dir = core_check_dir
        elif dir_exists(extras_check_dir):
            check_dir = extras_check_dir
        else:
            echo_failure('Local check `{}` cannot be found in core nor extras.'.format(check_name))
            echo_info('Auto-generation of new checks will be a feature soon!')
            sys.exit(1)

        if not file_exists(os.path.join(check_dir, 'setup.py')):
            echo_failure('No `setup.py` detected.')
            sys.exit(1)

        conf_path = find_matching_file(os.path.join(check_dir, 'conf.yaml*'))
        if not conf_path:
            echo_failure('No `conf.yaml*` detected.')
            sys.exit(1)

    if issubclass(check_class, DockerCheck):
        agent_version = agent or settings.get('agent', '')
        image = options.get('image') or image or settings.get('agent{}'.format(agent_version), '')
        options['image'] = image
        echo_info('Using docker image `{}`'.format(image))
        click.echo()

        echo_waiting("Detecting the agent's major version...")
        agent_version = get_agent_version(image)
        echo_info('Agent {} detected'.format(agent_version))

        if prod:
            echo_waiting('Reading the configuration file for `{}`...'.format(check_name))
            conf_contents, error = read_check_example_conf(check_name, image, agent_version)
        else:
            conf_contents = read_file(conf_path)
            if copy_conf:
                conf_path = ''
    elif issubclass(check_class, VagrantCheck):
        echo_failure('Vagrant checks are currently unsupported, "check" back soon!')
        sys.exit(1)
    else:
        echo_failure('Local checks are currently unsupported, "check" back soon!')
        sys.exit(1)

    check_class = check_class(
        d=location, api_key=api_key, conf_path=conf_path, conf_contents=conf_contents,
        agent_version=agent_version, check_dir=check_dir, instance_name=instance_name,
        no_instance=no_instance, direct=direct, **options
    )
    files = check_class.files.keys()

    location = check_class.location
    if dir_exists(location):
        force = force or settings.get('force', False)
        if force or click.confirm('`{}` already exists. Do you want to recreate it?'.format(location)):
            for file in files:
                remove_path(file)
        else:
            sys.exit(2)

    click.echo()
    echo_waiting('Creating necessary files...')
    check_class.write()

    echo_success('Successfully wrote:')
    for file in files:
        echo_info('  {}'.format(file))

    click.echo()
    echo_waiting('Starting containers...')
    output, error = check_dir_start(location)
    if error:
        click.echo()
        click.echo(output.rstrip())
        echo_failure('An unexpected Docker error (status {}) has occurred.'.format(error))
        sys.exit(error)
    echo_success('Success!')
    click.echo()

    if not prod:
        echo_waiting('Upgrading `{}` check to the development version...'.format(check_name))
        error = pip_install_mounted_check(check_class.container_name, check_name)
        if error:
            echo_warning(
                'The development check mounted at `{}` may have not installed properly. '
                'You might need to try it again yourself.'.format(get_check_dir(check_name))
            )

    click.echo()
    if direct:
        echo_info('To run this check, do `di check -d {}{}{}{}`.'.format(
            '-l {} '.format(location) if given_location else '',
            check_name,
            ' {}'.format(flavor) if flavor != DEFAULT_NAME else '',
            ' {}'.format(instance_name) if instance_name != DEFAULT_NAME else ''
        ))
    else:
        echo_info('To run this check, do `di check {}{}{}`.'.format(
            check_name,
            ' {}'.format(flavor) if flavor != DEFAULT_NAME else '',
            ' {}'.format(instance_name) if instance_name != DEFAULT_NAME else ''
        ))
