from setuptools import setup

setup(
    name='python-ev3dev-ep',
    namespace_packages=['ev3dev'],
    version='%(version)s',
    description='Python language bindings for ev3dev',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    license='MIT',
    url='https://github.com/rhempel/ev3dev-lang-python',
    include_package_data=True,
    packages=['ev3dev', 'ev3dev.ev3', 'ev3dev.brickpi'],
    package_dir={'': 'src'},
    )

