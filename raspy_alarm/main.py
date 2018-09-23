from threading import Thread
import IPython

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


def run():
  interfaces = []
  for key, email_info in emails.items():
    interface = EmailInterface(**email_info)
    interface.startup()
    interfaces.append(interface)

  rouser = Rouser(hardware['input_pins'][0], hardware['output_pins'], invert_on_off=hardware['invert_on_off'], alarms=alarms)
  rouser_thread = Thread(target=rouser.main_loop)

  scheduler = Scheduler('raspyalarm_schedule.json', rouser=rouser, interfaces=interfaces)
  scheduler_thread = Thread(target=scheduler.main_loop)

  rouser_thread.start()
  scheduler_thread.start()

  IPython.embed()

  rouser.shutdown()
  scheduler.shutdown()


if __name__ == '__main__':
  run()
