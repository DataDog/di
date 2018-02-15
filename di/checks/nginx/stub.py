import os
from collections import OrderedDict

from di.structures import File
from di.utils import DEFAULT_NAME, copy_dict_update, get_check_mount_dir, get_conf_path

COMPOSE_YAML = """\
version: '3'

services:
  nginx:
    image: nginx:{version}
    volumes:
        - {status_path}:/etc/nginx/conf.d/status.conf

  agent:
    image: {image}
    container_name: {container_name}
    environment:
        - DD_API_KEY={api_key}
    volumes:
        - {conf_path_local}:{conf_path_mount}{check_mount}
    links:
        - nginx
"""

STATUS_CONF = """\
server {
  listen 81;
  server_name nginx;

  access_log off;
  allow all;

  location /nginx_status {
    # Choose your status module

    # freely available with open source NGINX
    stub_status;

    # for open source NGINX < version 1.7.5
    # stub_status on;

    # available only with NGINX Plus
    # status;
  }
}
"""


class NginxStub:
    name = 'nginx'
    flavor = 'stub'
    container_prefix = 'agent_{name}_{flavor}'.format(name=name, flavor=flavor)
    option_defaults = OrderedDict([
        ('version', 'latest'),
    ])
    option_info = OrderedDict([
        ('version', (
            'The docker image version e.g. the `1.13.8` in `nginx:1.13.8`. '
            'The default is `latest`.'
        )),
    ])

    def __init__(self, d, image, agent_version, api_key, conf_path, conf_contents,
                 dev_check_dir=None, instance_name=None, no_instance=False, **options):
        self.location = self.get_location(d, instance_name, no_instance)
        compose_path = os.path.join(self.location, 'docker-compose.yaml')
        status_path = os.path.join(self.location, 'status.conf')
        conf_path_local = conf_path or os.path.join(
            self.location, '{name}.yaml'.format(name=self.name)
        )

        # Correct domain; localhost is per container
        conf_contents = conf_contents.replace('localhost', 'nginx:81', 1)

        check_mount = '' if not dev_check_dir else (
            '        - {check_dir_local}:{check_dir_mount}'.format(
                check_dir_local=dev_check_dir,
                check_dir_mount=get_check_mount_dir()
            )
        )

        self.files = {
            compose_path: File(
                compose_path,
                COMPOSE_YAML.format(
                    image=image,
                    status_path=status_path,
                    container_name=self.get_container_name(instance_name),
                    api_key=api_key,
                    conf_path_local=conf_path_local,
                    conf_path_mount=get_conf_path(self.name, agent_version),
                    check_mount=check_mount,
                    **copy_dict_update(self.option_defaults, options)
                )
            ),
            status_path: File(
                status_path,
                STATUS_CONF
            ),
            conf_path_local: File(
                conf_path_local,
                conf_contents
            )
        }

    @classmethod
    def get_container_name(cls, instance_name=None):
        return '{}_{}'.format(cls.container_prefix, instance_name or DEFAULT_NAME)

    @classmethod
    def get_location(cls, d, instance_name=None, no_instance=False):
        if no_instance:
            return os.path.join(d, cls.name, cls.flavor)
        else:
            return os.path.join(d, cls.name, cls.flavor, '{}'.format(instance_name or DEFAULT_NAME))

    def write(self):
        for f in self.files.values():
            f.write()
