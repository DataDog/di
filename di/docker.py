import subprocess
from subprocess import PIPE

from di.agent import A6_CONF_DIR, get_agent_exe_path, get_conf_example_glob
from di.utils import FAKE_API_KEY, NEED_SUBPROCESS_SHELL, chdir, get_check_dir


def check_dir_start(d):
    with chdir(d):
        process = subprocess.run(['docker-compose', 'up', '-d'], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode() + process.stderr.decode(), process.returncode


def check_dir_kill(d):
    with chdir(d):
        process = subprocess.run(['docker-compose', 'kill'], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode() + process.stderr.decode(), process.returncode


def check_dir_active(d):
    with chdir(d):
        process = subprocess.run(['docker-compose', 'top'], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return not not process.stdout.decode().strip() + process.stderr.decode().strip(), process.returncode


def run_check(container, check, agent_version_major=None):
    exe_path = get_agent_exe_path(agent_version_major or get_agent_version(container, running=True))
    process = subprocess.run([
        'docker', 'exec', container, exe_path, 'check', check
    ], shell=NEED_SUBPROCESS_SHELL)

    return process.returncode


def pip_install_mounted_check(container, check):
    process = subprocess.run([
        'docker', 'exec', container, 'pip', 'install', '-e', get_check_dir(check)
    ], shell=NEED_SUBPROCESS_SHELL)

    return process.returncode


def get_agent_version(image_or_container, running=False):
    if running:
        try:
            version = subprocess.run([
                'docker', 'exec', image_or_container, 'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
            ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL).stdout.decode().strip().split()[-1][0]
        except IndexError:
            version = ''

        if not version.isdigit():
            if dir_exists('{}/disk'.format(A6_CONF_DIR), image_or_container, running=running):
                version = '6'
            else:
                version = '5'
    else:
        try:
            version = subprocess.run([
                'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=FAKE_API_KEY), image_or_container,
                'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
            ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL).stdout.decode().strip().split()[-1][0]
        except IndexError:
            version = ''

        if not version.isdigit():
            if dir_exists('{}/disk'.format(A6_CONF_DIR), image_or_container, running=running):
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
            'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=FAKE_API_KEY), image_or_container,
            'python', '-c', "import os;print(os.path.isdir('{d}'))".format(d=d)
        ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode().strip() == 'True', process.returncode


def read_file(path, image):
    process = subprocess.run([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=FAKE_API_KEY), image, 'python', '-c',
        "import sys;sys.stdout.write(open('{path}', 'r').read())".format(path=path)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode(), process.returncode


def read_matching_glob(glob, image):
    process = subprocess.run([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=FAKE_API_KEY), image, 'python', '-c',
        "import glob,sys;sys.stdout.write(open(glob.glob('{glob}')[0], 'r').read())".format(glob=glob)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode(), process.returncode


def read_check_example_conf(check, image, agent_version_major=None):
    agent_version_major = agent_version_major or get_agent_version(image)
    glob = get_conf_example_glob(check, agent_version_major)
    process = subprocess.run([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=FAKE_API_KEY), image, 'python', '-c',
        "import glob,sys;sys.stdout.write(open(glob.glob('{glob}')[0], 'r').read())".format(glob=glob)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return process.stdout.decode(), process.returncode


def container_running(container):
    process = subprocess.run([
        'docker', 'ps', '-f', 'name={container}'.format(container=container)
    ], stdout=PIPE, stderr=PIPE, shell=NEED_SUBPROCESS_SHELL)

    return len(process.stdout.decode().strip().splitlines()) > 1, process.returncode
