import time


class Scheduler(object):
  def __init__(self, schedule_filepath, alarms=None, rouser=None, interfaces=None):
    self.schedule_filepath = schedule_filepath
    self.rouser = rouser
    self.alarms = alarms

    self.interfaces = []
    if interfaces:
      self.interfaces = interfaces

    self.running = True

  def main_loop(self):
    print("Scheduler main loop running...")

    while self.running:
      for interface in self.interfaces:
        interface.check()
      # self.check_email()
      # something = self.check_schedule()

      # if something:
      #   self.rouser.start_alarm()
      # print("Ping - scheduler")
      time.sleep(1)

  def add_interface(self):
    pass

  def shutdown(self):
    print("Shutting down interfaces.")
    for interface in self.interfaces:
      interface.shutdown()

    print("Shutting down scheduler.")
    self.running = False
