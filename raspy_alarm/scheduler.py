import time


class Scheduler(object):
  def __init__(self, schedule_filepath, alarms=None, rouser=None, interfaces=None):
    self.schedule_filepath = schedule_filepath
    self.rouser = rouser

    self.interfaces = []
    for interface in interfaces or self.interfaces:
      self.add_interface(interface)

    self.running = True

  def main_loop(self):
    print("Scheduler main loop running...")

    while self.running:
      for interface in self.interfaces:
        # The interface is responsible for using methods on the scheduler to do stuff
        interface.check()

      # print("Ping - scheduler")
      time.sleep(1)

  def add_interface(self, interface):
    interface.scheduler = self
    self.interfaces.append(interface)

  def shutdown(self):
    print("Shutting down interfaces.")
    for interface in self.interfaces:
      interface.shutdown()

    print("Shutting down scheduler.")
    self.running = False
