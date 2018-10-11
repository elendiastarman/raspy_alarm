import datetime
import hashlib
import rrule
import time
import json
import os


class Scheduler(object):
  def __init__(self, schedule_filepath, alarms=None, rouser=None, interfaces=None):
    self.schedule_filepath = schedule_filepath
    self.rouser = rouser

    self.schedule_hash = None
    self.cached_rrsets = None

    self.interfaces = []
    for interface in interfaces or self.interfaces:
      self.add_interface(interface)

    self.running = True

  def _make_rrule(self, data):
    if 'freq' in data:
      if isinstance(data['freq'], str):
        data['freq'] = rrule.FREQNAMES.index(data['freq'].upper())
    else:
      data['freq'] = rrule.DAILY

    now = datetime.datetime.now()
    if 'dtstart' in data:
      data['dtstart'] = now.replace(**data['dtstart'])
    else:
      data['dtstart'] = now

    return rrule.rrule(**data)

  def _check_schedule(self):
    contents = None
    filepath = os.path.join(os.getcwd(), 'data', self.schedule_filepath)

    try:
      with open(filepath, 'r') as file:
        contents = file.read()
    except FileNotFoundError as e:
      pass

    if not contents:
      return []

    schedule_hash = hashlib.sha1(bytes(contents, encoding='utf-8')).hexdigest()
    if schedule_hash != self.schedule_hash:
      self.schedule_hash
    else:
      return self.cached_rrsets  # ?

    parsed = json.loads(contents)

    for rrset_config in parsed.get('rrulesets', []):
      rset = rrule.rruleset()

      for rrule_config in rrset_config.get('rrules', []):
        rule = self._make_rrule(rrule_config)
        rset.rrule(rule)

      for exrule_config in rrset_config.get('exrules', []):
        rule = self._make_rrule(exrule_config)
        rset.exrule(rule)

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
