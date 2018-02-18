import os

from di.settings import copy_check_defaults
from di.utils import (
    DEFAULT_NAME, dict_merge, ensure_parent_dir_exists, get_check_mount_dir, get_conf_path
)


class File:
    def __init__(self, file_path, contents, binary=False):
        self.file_path = file_path
        self.contents = contents
        self.write_mode = 'wb' if binary else 'w'

    def write(self):
        ensure_parent_dir_exists(self.file_path)

        with open(self.file_path, self.write_mode) as f:
            if isinstance(self.contents, str):
                f.write(self.contents)
            else:
                f.writelines(self.contents)


class Check:
    name = 'check'
    flavor = DEFAULT_NAME

    def __init__(self, d, conf_path, agent_version, check_dir=None,
                 instance_name=None, no_instance=False, direct=False, **options):
        self.location = self.get_location(d, instance_name, no_instance, direct)
        self.conf_path_local = conf_path or os.path.join(
            self.location, '{name}.yaml'.format(name=self.name)
        )
        self.conf_path_mount = get_conf_path(self.name, agent_version)
        self.check_dir_local = check_dir or ''
        self.check_dir_mount = get_check_mount_dir()
        self.options = dict_merge(copy_check_defaults(self.name), options)
        self.files = {}

    @classmethod
    def get_location(cls, d, instance_name=None, no_instance=False, direct=False):
        if direct:
            return d
        elif no_instance:
            return os.path.join(d, cls.name, cls.flavor)
        else:
            return os.path.join(d, cls.name, cls.flavor, '{}'.format(instance_name or DEFAULT_NAME))

    def write(self):
        for f in self.files.values():
            f.write()


class DockerCheck(Check):
    def __init__(self, d, api_key, conf_path, agent_version, check_dir=None,
                 instance_name=None, no_instance=False, direct=False, **options):
        super().__init__(
            d=d, conf_path=conf_path, agent_version=agent_version, check_dir=check_dir,
            instance_name=instance_name, no_instance=no_instance, direct=direct, **options
        )

        self.api_key = '- DD_API_KEY={api_key}'.format(api_key=api_key)
        self.image = options.get('image', '')
        self.container_name = self.get_container_name(instance_name)
        self.compose_path = os.path.join(self.location, 'docker-compose.yaml')
        self.conf_mount = '- {conf_path_local}:{conf_path_mount}'.format(
            conf_path_local=self.conf_path_local,
            conf_path_mount=self.conf_path_mount
        )
        self.check_mount = '' if not self.check_dir_local else (
            '- {check_dir_local}:{check_dir_mount}'.format(
                check_dir_local=self.check_dir_local,
                check_dir_mount=self.check_dir_mount
            )
        )

    @classmethod
    def get_container_prefix(cls):
        return 'agent_{name}_{flavor}'.format(name=cls.name, flavor=cls.flavor)

    @classmethod
    def get_container_name(cls, instance_name=None):
        return '{}_{}'.format(cls.get_container_prefix(), instance_name or DEFAULT_NAME)


class VagrantCheck(Check):
    def __init__(self, d, api_key, conf_path, agent_version, check_dir=None,
                 instance_name=None, no_instance=False, direct=False, **options):
        super().__init__(
            d=d, conf_path=conf_path, agent_version=agent_version, check_dir=check_dir,
            instance_name=instance_name, no_instance=no_instance, direct=direct, **options
        )

        self.api_key = api_key
