Python language bindings for ev3dev
===================================

This is an alternative version of the ev3dev_ Python binding, written without using autogen.

In addition to the library, you'll find :

* small and not small demonstration programs in the ``demos`` sub-directory
* Sphinx generated documentation in the ``demoss`` sub-directory, including
the demonstrator ones

Automation
----------

A ``fabric`` recipe file (``fabfile.py``) if provided for simplifying repetitive tasks. The
available tasks are :

make_setup
    generates the effective ``setup.py`` file, using the ``setup-template.py`` template.
    It updates the version setting using available git tags. This is done this way so
    that the setup script can be run on the target, where git context is not available.

build
    builds the distribution package, according to the format specified in the
    ``pkg_format`` environment variable. Supported formats are : egg, sdist, wheel

deploy
    deploys the generated archive on the connected target, as identified by the
    ``hosts`` environment variable

install
    executes the installation command on the target

doc
    generates the documentation

demos
    deploy the demonstration programs and their data

make_all
    chains ``make_setup`` to ``install`` tasks. It is the default task if the ``fab``
    command is invoked without a task name

To customize the fabfile without modifying it, you can add settings such as sudo passwords or
hostname overrides in a plain Python file name ``fabconfig.py`` located in the same directory.
If it exists, it is imported after the definitions of environment variables and before the tasks
definitions.

.. _ev3dev: http://ev3dev.org

