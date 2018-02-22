from di.structures import DockerCheck, File
from .files.front import (
    COMPOSE_YAML, DOCKERFILE_FRONT, DOCKERFILE_SERVICE, FRONT_CONFIG,
    SERVICE_CONFIG, START_SERVICE_SCRIPT, SERVICE_APP
)


class EnvoyFront(DockerCheck):
    name = 'envoy'
    flavor = 'front'
    requires_build = True

    def __init__(self, d, api_key, conf_path, conf_contents, agent_version, check_dir=None,
                 instance_name=None, no_instance=False, direct=False, **options):
        super().__init__(
            d=d, api_key=api_key, conf_path=conf_path, agent_version=agent_version, check_dir=check_dir,
            instance_name=instance_name, no_instance=no_instance, direct=direct, **options
        )

        # Correct domain; localhost is per container
        conf_contents = conf_contents.replace('localhost:80', 'front-envoy:8001', 1)

        dockerfile_front = self.locate_file('Dockerfile-frontenvoy')
        dockerfile_service = self.locate_file('Dockerfile-service')
        front_config = self.locate_file('front-envoy.yaml')
        service_config = self.locate_file('service-envoy.yaml')
        start_service_script = self.locate_file('start_service.sh')
        service_app = self.locate_file('service.py')

        self.files.update({
            self.conf_path_local: File(
                self.conf_path_local,
                conf_contents
            ),
            self.compose_path: File(
                self.compose_path,
                self.format_compose_file(COMPOSE_YAML)
            ),
            dockerfile_front: File(
                dockerfile_front,
                DOCKERFILE_FRONT.format(**self.options)
            ),
            dockerfile_service: File(
                dockerfile_service,
                DOCKERFILE_SERVICE
            ),
            front_config: File(
                front_config,
                FRONT_CONFIG
            ),
            service_config: File(
                service_config,
                SERVICE_CONFIG
            ),
            start_service_script: File(
                start_service_script,
                START_SERVICE_SCRIPT
            ),
            service_app: File(
                service_app,
                SERVICE_APP
            ),
        })
