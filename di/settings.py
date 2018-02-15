import os
from collections import OrderedDict
from copy import deepcopy

import toml
from atomicwrites import atomic_write

from di.utils import APP_DIR, DEFAULT_NAME, copy_dict_merge, create_file, ensure_dir_exists

SETTINGS_FILE = os.path.join(APP_DIR, 'settings.toml')

APP_SETTINGS = OrderedDict([
    ('mode', 'prod'),
    ('agent', 6),
    ('agent6', 'datadog/agent:latest'),
    ('agent5', 'datadog/dev-dd-agent:master'),
    ('api_key', '$DD_API_KEY'),
    ('core', os.path.expanduser(os.path.join('~', 'dd', 'integrations-core'))),
    ('extras', os.path.expanduser(os.path.join('~', 'dd', 'integrations-extras'))),
    ('dev', OrderedDict([
        ('copy_conf', True),
    ])),
])

CHECK_SETTINGS = OrderedDict([
    ('nginx', OrderedDict([
        ('version', OrderedDict([
            (DEFAULT_NAME, 'latest'),
            ('info', 'The nginx Docker image tag.'),
            ('supported_flavors', ['stub', ]),
        ])),
    ])),
])

DEFAULT_SETTINGS = copy_dict_merge(APP_SETTINGS, CHECK_SETTINGS)


def copy_default_settings():
    return deepcopy(DEFAULT_SETTINGS)


def copy_check_defaults(check_name=None):
    defaults = OrderedDict()

    if check_name:
        options = CHECK_SETTINGS.get(check_name, {})

        for option in options:
            defaults[option] = options[option][DEFAULT_NAME]
    else:
        for check in CHECK_SETTINGS:
            defaults[check] = OrderedDict()
            options = CHECK_SETTINGS[check]

            for option in options:
                defaults[check][option] = options[option][DEFAULT_NAME]

    return defaults


def load_settings(lazy=False):
    if lazy and not os.path.exists(SETTINGS_FILE):
        return OrderedDict()
    with open(SETTINGS_FILE, 'r') as f:
        return toml.loads(f.read(), OrderedDict)


def save_settings(settings):
    ensure_dir_exists(os.path.dirname(SETTINGS_FILE))
    with atomic_write(SETTINGS_FILE, overwrite=True) as f:
        f.write(toml.dumps(settings))


def restore_settings():
    create_file(SETTINGS_FILE)
    save_settings(DEFAULT_SETTINGS)
