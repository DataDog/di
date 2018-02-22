import os
from collections import OrderedDict

import toml
from atomicwrites import atomic_write

from di.utils import (
    APP_DIR, CHECKS_DIR, DEFAULT_NAME, copy_dict_merge, ensure_parent_dir_exists
)

SETTINGS_FILE = os.path.join(APP_DIR, 'settings.toml')

APP_SETTINGS = OrderedDict([
    ('location', CHECKS_DIR),
    ('mode', 'prod'),
    ('agent', 6),
    ('agent6', 'datadog/agent-dev:master'),
    ('agent5', 'datadog/dev-dd-agent:master'),
    ('api_key', '${DD_API_KEY}'),
    ('core', os.path.expanduser(os.path.join('~', 'dd', 'integrations-core'))),
    ('extras', os.path.expanduser(os.path.join('~', 'dd', 'integrations-extras'))),
    ('force', False),
    ('copy_conf', True),
])

CHECK_SETTINGS = OrderedDict([
    ('envoy', OrderedDict([
        ('version', OrderedDict([
            (DEFAULT_NAME, 'latest'),
            ('info', 'The envoyproxy/envoy Docker image tag.'),
            ('supported_flavors', ('front', )),
        ])),
    ])),
    ('nginx', OrderedDict([
        ('version', OrderedDict([
            (DEFAULT_NAME, 'latest'),
            ('info', 'The nginx Docker image tag.'),
            ('supported_flavors', ('stub', )),
        ])),
    ])),
])


def copy_default_settings():
    return copy_dict_merge(APP_SETTINGS, copy_check_defaults())


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


def load_settings():
    default_settings = copy_default_settings()

    try:
        with open(SETTINGS_FILE, 'r') as f:
            default_settings.update(toml.loads(f.read(), OrderedDict))
    except FileNotFoundError:
        pass

    return default_settings


def save_settings(settings):
    ensure_parent_dir_exists(SETTINGS_FILE)
    with atomic_write(SETTINGS_FILE, overwrite=True) as f:
        f.write(toml.dumps(settings))


def restore_settings():
    save_settings(copy_default_settings())


def update_settings():
    save_settings(load_settings())
