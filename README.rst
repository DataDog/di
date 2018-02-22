di
==

.. image:: https://img.shields.io/pypi/v/di.svg?style=flat-square
    :target: https://pypi.org/project/di
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/ofek/di/master.svg?style=flat-square
    :target: https://travis-ci.org/ofek/di
    :alt: Travis CI

.. image:: https://img.shields.io/codecov/c/github/ofek/di/master.svg?style=flat-square
    :target: https://codecov.io/gh/ofek/di
    :alt: Codecov

.. image:: https://img.shields.io/pypi/pyversions/di.svg?style=flat-square
    :target: https://pypi.org/project/di
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/di.svg?style=flat-square
    :target: https://choosealicense.com/licenses
    :alt: License

-----

.. contents:: **Table of Contents**
    :backlinks: none

Installation
------------

di is distributed on `PyPI <https://pypi.org>`_ as a universal
wheel and is available on Linux/macOS and Windows and supports
Python 3.5+ and PyPy.

.. code-block:: bash

    $ pip3 install di

If you'd like to use the master branch instead, do:

.. code-block:: bash

    $ pip3 install https://github.com/DataDog/di/archive/master.tar.gz

You **must** have `Docker <https://docs.docker.com/install>`_ installed.

*Note:* If you're using the older `Docker Toolbox <https://docs.docker.com/toolbox/overview>`_
and are on Windows, you may need to run the command shown when you do ``docker-machine env``.
The command will likely be ``@FOR /f "tokens=*" %i IN ('docker-machine env') DO @%i``.

License
-------

di is distributed under the terms of both

- `MIT License <https://choosealicense.com/licenses/mit>`_
- `Apache License, Version 2.0 <https://choosealicense.com/licenses/apache-2.0>`_

at your option.
