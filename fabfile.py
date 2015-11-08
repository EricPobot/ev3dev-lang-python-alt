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

from fabric.api import env, put, sudo, run, local, task, prefix
from fabvenv import virtualenv

from git_version import git_version

# change the hostname of the EV3 if needed
env.hosts = ['ev3dev']
# EV3 sudo password
# env.password = 'x-f1135@eV3'
env.password = 'x-files'

env.use_ssh_config = True

# default distribution package format
env.pkg_format = 'sdist'

pkg_meta = {
    'egg': {
        'arch_ext': '-py2.7.egg',
        'build_cmd': 'bdist_egg',
        'install_cmd': 'easy_install %s'
    },
    'sdist': {
        'arch_ext': '.tar.gz',
        'build_cmd': 'sdist',
        'install_cmd': 'pip install %s -U'
    }
}


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
    infos["name"] = infos["name"].replace('-', '_')
    infos["arch_ext"] = pkg_meta[env.pkg_format]['arch_ext']

    return '%(name)s-%(version)s-%(arch_ext)s' % infos


@task(default=True)
def make_all():
    """ Chains the 'build', 'deploy' and 'install' tasks (executed if fab command is used without argument)
    """
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
    put('dist/%s' % _archive_name())


@task
def install():
    """ Installs the package on the EV3
    """
    # sudo('pip install %s -U' % _archive_name())
    with virtualenv('/home/eric/.virtualenvs/ev3dev'):
        run(pkg_meta[env.pkg_format]['install_cmd'] % _archive_name())
