COMPOSE_YAML = """\
version: '3'

services:

  nginx:
    image: nginx:{version}
    volumes:
      - ./status.conf:/etc/nginx/conf.d/status.conf

  agent:
    image: {image}
    container_name: {container_name}
    environment:
      {api_key}
    volumes:
      {conf_mount}
      {check_mount}
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
