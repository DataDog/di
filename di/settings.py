import os
from collections import OrderedDict
from copy import deepcopy

import toml
from atomicwrites import atomic_write

from di.utils import APP_DIR, create_file, ensure_dir_exists

SETTINGS_FILE = os.path.join(APP_DIR, 'settings.toml')

DEFAULT_SETTINGS = OrderedDict([
    ('agent5', 'datadog/dev-dd-agent:master'),
    ('agent6', 'datadog/agent:latest'),
    ('api_key', '$DD_API_KEY'),
    ('core', os.path.expanduser(os.path.join('~', 'integrations-core'))),
    ('extras', os.path.expanduser(os.path.join('~', 'integrations-extras'))),
])


def copy_default_settings():
    return deepcopy(DEFAULT_SETTINGS)


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
