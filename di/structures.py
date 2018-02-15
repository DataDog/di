import os

from di.utils import DEFAULT_NAME, ensure_parent_dir_exists


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

    def __init__(self, d, instance_name=None, no_instance=False, direct=False):
        self.location = self.get_location(d, instance_name, no_instance, direct)
        self.compose_path = os.path.join(self.location, 'docker-compose.yaml')
        self.files = {}

    @classmethod
    def get_container_prefix(cls):
        return 'agent_{name}_{flavor}'.format(name=cls.name, flavor=cls.flavor)

    @classmethod
    def get_container_name(cls, instance_name=None):
        return '{}_{}'.format(cls.get_container_prefix(), instance_name or DEFAULT_NAME)

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
