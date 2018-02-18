import os

from di.structures import DockerCheck, File

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
        {api_key}
    volumes:
        {conf_mount}
        {check_mount}
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


class NginxStub(DockerCheck):
    name = 'nginx'
    flavor = 'stub'

    def __init__(self, d, api_key, conf_path, conf_contents, agent_version, check_dir=None,
                 instance_name=None, no_instance=False, direct=False, **options):
        super().__init__(
            d=d, api_key=api_key, conf_path=conf_path, agent_version=agent_version, check_dir=check_dir,
            instance_name=instance_name, no_instance=no_instance, direct=direct, **options
        )

        status_path = os.path.join(self.location, 'status.conf')

        # Correct domain; localhost is per container
        conf_contents = conf_contents.replace('localhost', 'nginx:81', 1)

        self.files.update({
            self.conf_path_local: File(
                self.conf_path_local,
                conf_contents
            ),
            self.compose_path: File(
                self.compose_path,
                COMPOSE_YAML.format(
                    status_path=status_path,
                    image=self.image,
                    api_key=self.api_key,
                    container_name=self.container_name,
                    conf_mount=self.conf_mount,
                    check_mount=self.check_mount,
                    **self.options
                )
            ),
            status_path: File(
                status_path,
                STATUS_CONF
            ),
        })
