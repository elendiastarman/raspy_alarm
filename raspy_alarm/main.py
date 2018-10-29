"""Raspy Alarm

Usage:
  main.py [--shell]
  main.py (-h | --help)

Options:
  -h --help  Show this help text
  --shell    Start an IPython shell with access to scheduler, rouser, and interface instances
"""

from threading import Thread
from docopt import docopt
import IPython
import signal

from interface import EmailInterface
from scheduler import Scheduler
from rouser import Rouser

try:
  from alarm_configuration import rouser_configs, emails, alarms
except ImportError as e:
  raise ValueError("No configuration found in alarm_configuration.py; look at alarm_configuration.example for ideas.")

rousers = None
scheduler = None


def shutdown(signum=None, frame=None):
  global rousers, scheduler

  if rousers:
    for rouser in rousers:
      try:
        rouser.shutdown()
      except Exception as e:
        print("Error shutting down rouser: {}".format(str(e)))

    rousers = None

  if scheduler:
    scheduler.shutdown()
    scheduler = None


def run():
  global rousers, scheduler
  args = docopt(__doc__)

  interfaces = []
  for key, email_info in emails.items():
    interface = EmailInterface(**email_info)
    interface.startup()
    interfaces.append(interface)

  rousers = []
  for rouser_name, rouser_config in rouser_configs.items():
    rouser_config['name'] = rouser_name
    rouser_config['alarms'] = alarms.get(rouser_name, {})

    rouser = Rouser(**rouser_config)
    rousers.append(rouser)

    rouser_thread = Thread(target=rouser.main_loop)
    rouser_thread.start()

  scheduler = Scheduler('schedule_rules.json', rousers=rousers, interfaces=interfaces)
  scheduler_thread = Thread(target=scheduler.main_loop)
  scheduler_thread.start()

  signal.signal(signal.SIGINT, shutdown)
  signal.signal(signal.SIGTERM, shutdown)

  if args.get('--shell'):
    IPython.embed()
    shutdown()


if __name__ == '__main__':
  run()
