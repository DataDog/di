import os

from di.settings import copy_check_defaults
from di.structures import Check, File
from di.utils import dict_merge, get_check_mount_dir, get_conf_path

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


class NginxStub(Check):
    name = 'nginx'
    flavor = 'stub'

    def __init__(self, d, image, agent_version, api_key, conf_path, conf_contents,
                 dev_check_dir=None, instance_name=None, no_instance=False, direct=False, **options):
        super().__init__(d, conf_path, instance_name, no_instance, direct)

        status_path = os.path.join(self.location, 'status.conf')

        # Correct domain; localhost is per container
        conf_contents = conf_contents.replace('localhost', 'nginx:81', 1)

        check_mount = '' if not dev_check_dir else (
            '        - {check_dir_local}:{check_dir_mount}'.format(
                check_dir_local=dev_check_dir,
                check_dir_mount=get_check_mount_dir()
            )
        )

        self.files.update({
            self.compose_path: File(
                self.compose_path,
                COMPOSE_YAML.format(
                    image=image,
                    status_path=status_path,
                    container_name=self.get_container_name(instance_name),
                    api_key=api_key,
                    conf_path_local=self.conf_path_local,
                    conf_path_mount=get_conf_path(self.name, agent_version),
                    check_mount=check_mount,
                    **dict_merge(copy_check_defaults(self.name), options)
                )
            ),
            self.conf_path_local: File(
                self.conf_path_local,
                conf_contents
            ),
            status_path: File(
                status_path,
                STATUS_CONF
            ),
        })
