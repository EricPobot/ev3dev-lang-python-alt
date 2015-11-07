from setuptools import setup
from git_version import git_version


setup(
    name='python-ev3dev-ep',
    version=git_version(),
    description='Python language bindings for ev3dev',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    license='MIT',
    url='https://github.com/rhempel/ev3dev-lang-python',
    include_package_data=True,
    packages=['ev3dev']
    )

