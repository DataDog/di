import os
import subprocess
from subprocess import PIPE

from di.agent import A6_CONF_DIR, get_agent_exe_path
from di.utils import NEED_SUBPROCESS_SHELL, chdir, get_check_dir

# Must be a certain length
__API_KEY = 'a' * 32


def run_check(container, check, agent_version_major=None):
    exe_path = (
        get_agent_exe_path(agent_version_major) if agent_version_major
        else get_agent_version(container, running=True)
    )
    process = subprocess.run([
        'docker', 'exec', container, exe_path, 'check', check
    ], shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode().strip(), process.returncode


def pip_install_mounted_check(container, check):
    process = subprocess.run([
        'docker', 'exec', container, 'pip', 'install', '-e', get_check_dir(check)
    ], shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode().strip(), process.returncode


def get_agent_version(image_or_container, running=False):
    if running:
        version = subprocess.run([
            'docker', 'exec', image_or_container, 'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
        ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL).stdout.decode().strip().split()[-1][0]

        if not version.isdigit():
            if dir_exists(os.path.join(A6_CONF_DIR, 'disk'), image_or_container, running=running):
                version = '6'
            else:
                version = '5'
    else:
        version = subprocess.run([
            'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image_or_container,
            'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
        ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL).stdout.decode().strip().split()[-1][0]

        if not version.isdigit():
            if dir_exists(os.path.join(A6_CONF_DIR, 'disk'), image_or_container, running=running):
                version = '6'
            else:
                version = '5'

    return version


def dir_exists(d, image_or_container, running=False):
    if running:
        process = subprocess.run([
            'docker', 'exec', image_or_container, 'python', '-c',
            "import os;print(os.path.isdir('{d}'))".format(d=d)
        ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)
    else:
        process = subprocess.run([
            'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image_or_container,
            'python', '-c', "import os;print(os.path.isdir('{d}'))".format(d=d)
        ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode().strip(), process.returncode


def read_file(path, image):
    process = subprocess.run([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image, 'python', '-c',
        "import sys;sys.stdout.write(open('{path}', 'r').read())".format(path=path)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode(), process.returncode


def read_matching_glob(glob, image):
    process = subprocess.run([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image, 'python', '-c',
        "import glob,sys;sys.stdout.write(open(glob.glob('{glob}')[0], 'r').read())".format(glob=glob)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode(), process.returncode


def container_running(container):
    process = subprocess.run([
        'docker', 'ps', '-f', 'name={container}'.format(container=container)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return len(process.stdout.decode().strip().splitlines()) > 1, process.returncode


def check_dir_active(d):
    with chdir(d):
        process = subprocess.run(['docker-compose', 'top'], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return not not process.stdout.decode().strip(), process.returncode
