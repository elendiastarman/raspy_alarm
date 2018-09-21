class Scheduler(object):
  def __init__(self, schedule_filepath, rouser=None, interfaces=None):
    self.schedule_filepath = schedule_filepath
    self.rouser = rouser

    self.interfaces = []
    if interfaces:
      self.interfaces = interfaces

  def main_loop(self):
    self.check_email()
    something = self.check_schedule()

    if something:
      self.rouser.start_alarm()

  def add_interface(self):
    pass
