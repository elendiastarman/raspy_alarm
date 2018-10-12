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
    self.cached_exceptions = None

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
    if schedule_hash == self.schedule_hash:
      return
    self.schedule_hash = schedule_hash

    self.cached_rrsets = []
    self.cached_exceptions = []

    parsed = json.loads(contents)
    now = datetime.datetime.now()

    for rrset_config in parsed.get('rrulesets', []):
      rset = rrule.rruleset()

      for rrule_config in rrset_config.get('rrules', []):
        rule = self._make_rrule(rrule_config)
        rset.rrule(rule)

      for exrule_config in rrset_config.get('exrules', []):
        rule = self._make_rrule(exrule_config)
        rset.exrule(rule)

      for rdate_config in rrset_config.get('rdates', []):
        date = now.replace(**rdate_config)
        rset.rdate(date)

      for exdate_config in rrset_config.get('exdates', []):
        date = now.replace(**exdate_config)
        rset.exdate(date)

      alarm_config = dict(
        rrule_set=rset,
        params=rrset_config['parameters'],
      )

      self.cached_rrsets.append(alarm_config)

    for exdate_config in parsed.get('exceptions', []):
      date = now.replace(**rdate_config)
      self.cached_exceptions.append(date)

  def _calculate_datetimes(self, threshold):
    datetimes = []

    for alarm_rule in self.cached_rrsets:
      rrule_set = alarm_rule['rrule_set']
      temp_dt = rrule_set(threshold)

      while temp_dt in self.cached_exceptions:
        temp_dt = rrule_set(temp_dt)

      datetimes.append(dict(
        datetime=temp_dt,
        params=alarm_rule['params'],
      ))

    return datetimes

  def main_loop(self):
    print("Scheduler main loop running...")

    while self.running:
      # print("Ping - scheduler")

      for interface in self.interfaces:
        # The interface is responsible for using methods on the scheduler to do stuff
        interface.check()

      self._check_schedule()

      now = datetime.datetime.now()
      threshold = now - datetime.timedelta(seconds=5)
      datetimes = sorted(self._calculate_datetimes(threshold), key=lambda _: _['datetime'])

      dt = datetimes[0]['datetime']
      params = datetimes[0]['params']
      name = params.get('name', None)

      if dt < now and (name is None or name != self.rouser.alarm['name']):
        self.rouser.start_alarm(**params)

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
