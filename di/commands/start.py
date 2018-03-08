import os
import sys
from collections import OrderedDict

import click

from di.checks import Checks
from di.commands.utils import (
    CONTEXT_SETTINGS, echo_failure, echo_info, echo_success, echo_waiting, echo_warning
)
from di.docker import (
    check_dir_start, get_agent_version, pip_install_dev_deps,
    pip_install_mounted_check, read_check_example_conf
)
from di.settings import load_settings
from di.structures import DockerCheck, VagrantCheck
from di.utils import (
    CHECKS_BASE_PACKAGE, CHECKS_DIR, DEFAULT_NAME, dir_exists, file_exists, find_matching_file,
    get_check_mount_dir, get_compose_api_key, read_file, remove_path, resolve_path
)


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Starts a fully functioning integration')
@click.argument('check_name')
@click.argument('flavor', required=False, default=DEFAULT_NAME)
@click.argument('instance_name', required=False, default=DEFAULT_NAME)
@click.option('--options', '-o', nargs=2, multiple=True)
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
def start(check_name, flavor, instance_name, options, direct, location, force,
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
    location = given_location or settings.get('location', CHECKS_DIR)
    prod = prod if prod is not None else settings.get('mode', 'prod') == 'prod'
    copy_conf = copy_conf if copy_conf is not None else settings.get('copy_conf', True)

    if prod:
        conf_path = ''
        check_dirs = None
    else:
        core = resolve_path(core or settings.get('core', ''))
        extras = resolve_path(extras or settings.get('extras', ''))

        if not dir_exists(core):
            echo_failure(
                'All checks running in dev mode require `integrations-core` '
                'for its {} dependency.'.format(CHECKS_BASE_PACKAGE)
            )
            sys.exit(1)

        core_check_dir = os.path.join(core, check_name)
        extras_check_dir = os.path.join(extras, check_name)

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

        check_dirs = check_dir, os.path.join(core, CHECKS_BASE_PACKAGE)

    if issubclass(check_class, DockerCheck):
        agent_version = agent or settings.get('agent', '')
        image = options.get('image') or image or settings.get('agent{}'.format(agent_version), '')
        options['image'] = image
        echo_info('Using docker image `{}`'.format(image))
        click.echo()

        echo_waiting("Detecting the agent's major version...")
        agent_version = get_agent_version(image)
        echo_info('Agent {} detected'.format(agent_version))
        click.echo()

        echo_waiting('Reading the configuration file for `{}`... '.format(check_name), nl=False)
        if prod:
            conf_contents, error = read_check_example_conf(check_name, image, agent_version)
            if error:
                click.echo()
                echo_failure(
                    'Unable to locate a configuration file. If this '
                    'is a new check, please use the --dev flag.'
                )
                sys.exit(1)
        else:
            conf_contents = read_file(conf_path)
            if copy_conf:
                conf_path = ''
        echo_success('success!')

    elif issubclass(check_class, VagrantCheck):
        echo_failure('Vagrant checks are currently unsupported, "check" back soon!')
        sys.exit(1)
    else:
        echo_failure('Local checks are currently unsupported, "check" back soon!')
        sys.exit(1)

    check_class = check_class(
        d=location, api_key=api_key, conf_path=conf_path, conf_contents=conf_contents,
        agent_version=agent_version, check_dirs=check_dirs, instance_name=instance_name,
        direct=direct, **options
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
    if isinstance(check_class, DockerCheck):
        echo_waiting('Starting containers... ', nl=False)
        output, error = check_dir_start(location, build=check_class.requires_build)
        if error:
            click.echo()
            click.echo(output.rstrip())
            echo_failure('An unexpected Docker error (status {}) has occurred.'.format(error))
            sys.exit(error)
        echo_success('success!')

        if not prod:
            click.echo()
            echo_waiting('Upgrading `{}` check to the development version...'.format(check_name))
            error = pip_install_mounted_check(check_class.container_name, check_name)
            if error:
                echo_warning(
                    'The development check mounted at `{}` may have not installed properly. '
                    'You might need to try it again yourself.'.format(get_check_mount_dir(check_name))
                )

            click.echo()
            echo_waiting('Installing development dependencies...')
            error = pip_install_dev_deps(check_class.container_name)
            if error:
                echo_warning(
                    'The development dependencies may have not installed properly. '
                    'You might need to try installing them again yourself.'
                )
    elif isinstance(check_class, VagrantCheck):
        echo_failure('Vagrant checks are currently unsupported, "check" back soon!')
        sys.exit(1)
    else:
        echo_failure('Local checks are currently unsupported, "check" back soon!')
        sys.exit(1)

    # Show how to use it
    click.echo()

    echo_info('Location: `{}`'.format(check_class.location))
    if isinstance(check_class, DockerCheck):
        echo_info('Container name: `{}`'.format(check_class.container_name))
    elif isinstance(check_class, VagrantCheck):
        echo_failure('Vagrant checks are currently unsupported, "check" back soon!')
        sys.exit(1)
    else:
        echo_failure('Local checks are currently unsupported, "check" back soon!')
        sys.exit(1)

    location_arg = '-l {} '.format(location) if given_location else ''
    instance_arg = ' {}'.format(instance_name) if instance_name != DEFAULT_NAME else ''
    flavor_arg = ' {}'.format(flavor) if flavor != DEFAULT_NAME or instance_arg else ''

    if direct:
        if not prod:
            echo_info('To test this check, do `di test -d {}{}{}{}`.'.format(
                location_arg, check_name, flavor_arg, instance_arg
            ))
        echo_info('To run this check, do `di check -d {}{}{}{}`.'.format(
            location_arg, check_name, flavor_arg, instance_arg
        ))
        echo_info('To stop this check, do `di stop -d {}{}{}{}`.'.format(
            location_arg, check_name, flavor_arg, instance_arg
        ))
    else:
        if not prod:
            echo_info('To test this check, do `di test {}{}{}`.'.format(
                check_name, flavor_arg, instance_arg
            ))
        echo_info('To run this check, do `di check {}{}{}`.'.format(
            check_name, flavor_arg, instance_arg
        ))
        echo_info('To stop this check, do `di stop {}{}{}`.'.format(
            check_name, flavor_arg, instance_arg
        ))
