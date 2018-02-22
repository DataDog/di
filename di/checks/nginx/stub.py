import os

from di.structures import DockerCheck, File
from .files.stub import COMPOSE_YAML, STATUS_CONF


class NginxStub(DockerCheck):
    name = 'nginx'
    flavor = 'stub'
    requires_build = False

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
