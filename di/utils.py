import os
import platform
import shutil
from ast import literal_eval
from contextlib import contextmanager
from copy import deepcopy
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from appdirs import user_data_dir

APP_DIR = user_data_dir('di-dev', '')
CHECKS_BASE_PACKAGE = 'datadog-checks-base'
CHECKS_DIR = os.path.join(APP_DIR, 'checks')
DEFAULT_NAME = 'default'

# Must be a certain length
FAKE_API_KEY = 'a' * 32

__platform = platform.system()
ON_MACOS = os.name == 'mac' or __platform == 'Darwin'
ON_WINDOWS = NEED_SUBPROCESS_SHELL = os.name == 'nt' or __platform == 'Windows'


def get_compose_api_key(api_key):
    evar = api_key[2:-1]
    if api_key.startswith('${') and api_key.endswith('}') and evar not in os.environ:
        api_key = FAKE_API_KEY
    return api_key, evar


def get_check_mount_dir():
    return '/home'


def get_check_dir(check):
    return '{}/{}'.format(get_check_mount_dir(), check)


def copy_dict_merge(d1, d2):
    d1 = deepcopy(d1)
    d1.update(deepcopy(d2))
    return d1


def dict_merge(d1, d2):
    d1.update(d2)
    return d1


def string_to_toml_type(s):
    if s.isdigit():
        s = int(s)
    elif s == 'true':
        s = True
    elif s == 'false':
        s = False
    elif s.startswith('['):
        s = literal_eval(s)

    return s


def find_matching_file(f):
    try:
        return glob('{}*'.format(f))[0]
    except IndexError:
        return ''


def read_file(file):
    with open(file, 'r') as f:
        return f.read()


def file_exists(f):
    return os.path.isfile(f)


def dir_exists(d):
    return os.path.isdir(d)


def ensure_dir_exists(d):
    if not dir_exists(d):
        os.makedirs(d)


def ensure_parent_dir_exists(path):
    ensure_dir_exists(os.path.dirname(os.path.abspath(path)))


def create_file(fname):
    ensure_parent_dir_exists(fname)
    with open(fname, 'a'):
        os.utime(fname, times=None)


def download_file(url, fname):
    req = urlopen(url)
    with open(fname, 'wb') as f:
        while True:
            chunk = req.read(16384)
            if not chunk:
                break
            f.write(chunk)
            f.flush()


def copy_path(path, d):
    if os.path.isdir(path):
        shutil.copytree(
            path,
            os.path.join(d, basepath(path)),
            copy_function=shutil.copy
        )
    else:
        shutil.copy(path, d)


def remove_path(path):
    try:
        shutil.rmtree(path)
    except (FileNotFoundError, OSError):
        try:
            os.remove(path)
        except (FileNotFoundError, PermissionError):
            pass


def resolve_path(path, strict=False):
    path = os.path.expanduser(path or '')

    try:
        path = str(Path(path).resolve())
    # FUTURE: Remove this when we drop 3.5.
    except FileNotFoundError:  # no cov
        path = os.path.realpath(path)

    return '' if strict and not os.path.exists(path) else path


def basepath(path):
    return os.path.basename(os.path.normpath(path))


@contextmanager
def chdir(d, cwd=None):
    origin = cwd or os.getcwd()
    os.chdir(d)

    try:
        yield
    finally:
        os.chdir(origin)


@contextmanager
def temp_chdir(cwd=None):
    with TemporaryDirectory() as d:
        origin = cwd or os.getcwd()
        os.chdir(d)

        try:
            yield resolve_path(d)
        finally:
            os.chdir(origin)


@contextmanager
def env_vars(evars, ignore=None):
    ignore = ignore or {}
    ignored_evars = {}
    old_evars = {}

    for ev in evars:
        if ev in os.environ:
            old_evars[ev] = os.environ[ev]
        os.environ[ev] = evars[ev]

    for ev in ignore:
        if ev in os.environ:  # no cov
            ignored_evars[ev] = os.environ[ev]
            os.environ.pop(ev)

    try:
        yield
    finally:
        for ev in evars:
            if ev in old_evars:
                os.environ[ev] = old_evars[ev]
            else:
                os.environ.pop(ev)

        for ev in ignored_evars:
            os.environ[ev] = ignored_evars[ev]


@contextmanager
def temp_move_path(path, d):
    if os.path.exists(path):
        dst = shutil.move(path, d)

        try:
            yield dst
        finally:
            try:
                os.replace(dst, path)
            except OSError:  # no cov
                shutil.move(dst, path)
    else:
        try:
            yield
        finally:
            remove_path(path)
