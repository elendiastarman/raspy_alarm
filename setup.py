from setuptools import setup

setup(
    name='RaspyAlarm',
    packages=['raspy_alarm'],
    include_package_data=True,
    install_requires=[
        'flask',
        'bcrypt',
        'gpiozero',
        'ipython',
        'ipdb',
        'flask-shell-ipython',
        'python-dateutil',
        'docopt',
    ],
)
