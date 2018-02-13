import os
import subprocess

from di.agent import A6_CONF_DIR
from di.utils import NEED_SUBPROCESS_SHELL

# Must be a certain length
__API_KEY = 'a' * 32


def get_agent_version(image):
    version = subprocess.check_output([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image,
        'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
    ], shell=NEED_SUBPROCESS_SHELL).decode().strip().split()[-1]

    if not version[0].isdigit():
        if dir_exists(os.path.join(A6_CONF_DIR, 'disk'), image):
            version = '6'
        else:
            version = '5'

    return version


def dir_exists(d, image):
    output = subprocess.check_output([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image,
        'python', '-c', "import os;print(os.path.isdir('{d}'))".format(d=d)
    ], shell=NEED_SUBPROCESS_SHELL).decode().strip()

    return output == 'True'


def read_file(path, image):
    output = subprocess.check_output([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image, 'python', '-c',
        "import sys;sys.stdout.write(open('{path}', 'r').read())".format(path=path)
    ], shell=NEED_SUBPROCESS_SHELL).decode()

    return output


def read_matching_glob(glob, image):
    output = subprocess.check_output([
        'docker', 'run', '-e', 'DD_API_KEY={ak}'.format(ak=__API_KEY), image, 'python', '-c',
        "import glob,sys;sys.stdout.write(open(glob.glob('{glob}')[0], 'r').read())".format(glob=glob)
    ], shell=NEED_SUBPROCESS_SHELL).decode()

    return output
