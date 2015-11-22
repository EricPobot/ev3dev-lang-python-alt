# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2015 Eric Pascual
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

"""
Fabric (http://www.fabfile.org/) file to automate operations for building
the distribution archive, uploading it to the brick and installing there.
"""

import os

from fabric.api import env, put, sudo, run, local, task, prefix, lcd

from git_version import git_version

_HERE = os.path.dirname(__file__)

# change the hostname of the EV3 if needed
env.hosts = ['ev3dev']
# env.user = 'robot'

env.use_ssh_config = True

# default distribution package format
env.pkg_format = 'egg'

try:
    import fabconfig
except ImportError:
    pass

pkg_meta = {
    'egg': {
        'arch_ext': '-py2.7.egg',
        'build_cmd': 'bdist_egg',
        'install_cmd': 'easy_install -Z -U %s'
    },
    'sdist': {
        'arch_ext': '.tar.gz',
        'build_cmd': 'sdist',
        'install_cmd': 'pip install %s -U'
    },
    'wheel': {
        'arch_ext': '-py2-none-any.whl',
        'build_cmd': 'bdist_wheel',
        'install_cmd': 'pip install %s -U'
    }
}

DIST_REMOTE_DIR = 'dist/'


def _get_pkg_infos():
    """ Returns a dictionary containing the setup() function arguments.

    IMPORTANT: it assumes the usual code formatting is applied for the setup call,
    i.e.:

    >>> setup(
    >>>     arg1=value1,
    >>>     arg2=value2,
    >>>     ...
    >>>     argn=valuen
    >>> )

    """
    return dict([(arg, eval(val)) for arg, val in [
        l.split('=', 1) for l in (l.strip().strip(',') for l in file('setup.py') if '=' in l) if not l.startswith('#')
    ]])


def _archive_name():
    """ Returns the filename of the distribution file, based on information
    extracted from the setup() call
    """
    infos = _get_pkg_infos()
    if env.pkg_format in ('egg', 'wheel'):
        infos["name"] = infos["name"].replace('-', '_')
    infos["arch_ext"] = pkg_meta[env.pkg_format]['arch_ext']

    return '%(name)s-%(version)s%(arch_ext)s' % infos


def _find_project_root():
    while not os.path.isdir('.git'):
        os.chdir(os.path.dirname(os.getcwd()))
    return os.getcwd()

PROJECT_ROOT = _find_project_root()


@task(default=True)
def update():
    """ Chains all the operations to update the brick (executed if fab command is used without argument)
    """
    egg()
    make_setup()
    build()
    deploy()
    install()


@task
def make_setup():
    src = ''.join(file('setup-template.py').readlines())
    with file('setup.py', 'w') as fp:
        fp.write(src % {
            'version': git_version()
        })


@task
def egg():
    env.pkg_format = 'egg'


@task
def sdist():
    env.pkg_format = 'sdist'


@task
def build():
    """ Builds the distribution archive
    """
    local('python setup.py %s' % pkg_meta[env.pkg_format]['build_cmd'])


@task
def deploy():
    """ Deploys the distribution archive
    """
    put(
        local_path=os.path.join(PROJECT_ROOT, 'dist', _archive_name()),
        remote_path=DIST_REMOTE_DIR,
        mirror_local_mode=True
    )


@task
def install():
    """ Installs the package on the EV3
    """
    cmde = pkg_meta[env.pkg_format]['install_cmd'] % os.path.join(DIST_REMOTE_DIR, _archive_name())
    sudo(cmde)


@task
def doc():
    with lcd(os.path.join(PROJECT_ROOT, 'docs')):
        local('make clean html')


@task
def update_demos():
    put(os.path.join(PROJECT_ROOT, 'src', 'demos/'), mirror_local_mode=True)


@task
def demo(name):
    script_name = name + '.py'
    put(os.path.join(PROJECT_ROOT, 'src', 'demos', script_name), remote_path='demos/', mirror_local_mode=True)
    run(os.path.join('demos', script_name))

