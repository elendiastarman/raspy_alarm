from setuptools import setup

setup(
    name='RaspyAlarm',
    packages=['raspy_alarm'],
    include_package_data=True,
    install_requires=[
        'flask',
        'bcrypt',
        'gpiozero',
        'IPython',
        'ipdb',
        'flask-shell-ipython',
    ],
)
