import os
import platform
import shutil
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from appdirs import user_data_dir

from di.agent import A5_CONF_DIR, A6_CONF_DIR

APP_DIR = user_data_dir('di-dev', '')

__platform = platform.system()
ON_MACOS = os.name == 'mac' or __platform == 'Darwin'
ON_WINDOWS = NEED_SUBPROCESS_SHELL = os.name == 'nt' or __platform == 'Windows'


def get_conf_example_glob(check, agent_version_major):
    if int(agent_version_major) >= 6:
        return '{conf_dir}/{check}.d/conf*'.format(conf_dir=A6_CONF_DIR, check=check)
    else:
        return '{conf_dir}/{check}*'.format(conf_dir=A5_CONF_DIR, check=check)


def ensure_dir_exists(d):
    if not os.path.exists(d):
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


def resolve_path(path):
    try:
        path = str(Path(path).resolve())
    # FUTURE: Remove this when we drop 3.5.
    except FileNotFoundError:  # no cov
        return ''
    return path if os.path.exists(path) else ''


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
