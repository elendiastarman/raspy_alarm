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
  from alarm_configuration import hardware, emails, alarms
except ImportError as e:
  print("Error:", str(e))
  print("No configuration found in alarm_configuration.py; using defaults. Look at alarm_configuration.example for ideas.")
  hardware = {
    'output_pins': [2],
    'input_pins': [21],
    'invert_on_off': True,
  }
  emails = {}
  alarms = {}

rouser = None
scheduler = None


def shutdown(signum=None, frame=None):
  global rouser, scheduler

  if rouser:
    rouser.shutdown()
    rouser = None

  if scheduler:
    scheduler.shutdown()
    scheduler = None


def run():
  global rouser, scheduler
  args = docopt(__doc__)

  interfaces = []
  for key, email_info in emails.items():
    interface = EmailInterface(**email_info)
    interface.startup()
    interfaces.append(interface)

  rouser = Rouser(hardware['output_pins'][0], hardware['input_pins'], invert_on_off=hardware['invert_on_off'], alarms=alarms)
  rouser_thread = Thread(target=rouser.main_loop)

  scheduler = Scheduler('raspyalarm_schedule.json', rouser=rouser, interfaces=interfaces)
  scheduler_thread = Thread(target=scheduler.main_loop)

  rouser_thread.start()
  scheduler_thread.start()

  signal.signal(signal.SIGINT, shutdown)
  signal.signal(signal.SIGTERM, shutdown)

  if args.get('--shell'):
    IPython.embed()
    shutdown()


if __name__ == '__main__':
  run()
