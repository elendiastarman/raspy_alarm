from dateutil import rrule, tz

import datetime
import hashlib
import time
import json
import os


FREQUENCIES = {'yearly': rrule.YEARLY, 'monthly': rrule.MONTHLY, 'weekly': rrule.WEEKLY, 'daily': rrule.DAILY, 'hourly': rrule.HOURLY, 'minutely': rrule.MINUTELY, 'secondly': rrule.SECONDLY}
MONTH_NAMES = ['jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'jun', 'june', 'jul', 'july', 'sept', 'september', 'oct', 'october', 'nov', 'november', 'dec', 'december']
MONTHS = {name: index // 2 for index, name in enumerate(MONTH_NAMES)}
WEEKDAY_NAMES = ['m', 'mo', 'mon', 'monday', 't', 'tu', 'tue', 'tuesday', 'w', 'we', 'wed', 'wednesday', 'r', 'th', 'thu', 'thursday', 'f', 'fr', 'fri', 'friday', 's', 'sa', 'sat', 'saturday', 'u', 'su', 'sun', 'sunday']
WEEKDAYS = {name: index // 4 for index, name in enumerate(WEEKDAY_NAMES)}
WEEKDAYNO = (rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU)  # This supports e.g. rrule.MO(2) for the second Monday of a month


class Scheduler(object):
  def __init__(self, schedule_filepath, alarms=None, rouser=None, interfaces=None):
    self.schedule_filepath = schedule_filepath
    self.rouser = rouser

    self.timezone = None
    self.schedule_hash = None
    self.cached_rrsets = []
    self.cached_exclusions = []
    self.cached_inclusions = []

    self.interfaces = []
    for interface in interfaces or []:
      self.add_interface(interface)

    self.running = True

  @property
  def now(self):
    return datetime.datetime.now(tz=self.timezone).replace(microsecond=0)

  @property
  def EPOCH(self):
    return datetime.datetime(2018, 1, 1, 0, 0, 0, tzinfo=self.timezone)

  def _make_rrule(self, data):
    if 'freq' in data:
      if isinstance(data['freq'], str):
        data['freq'] = FREQUENCIES[data['freq'].lower()]
    else:
      data['freq'] = rrule.DAILY

    if 'bymonth' in data:
      if isinstance(data['bymonth'], (str, int)):
        data['bymonth'] = [data['bymonth']]

      for index, item in enumerate(data['bymonth']):
        if isinstance(item, str):
          data['bymonth'][index] = MONTHS[item.lower()]

    if 'byweekday' in data:
      if isinstance(data['byweekday'], (str, int)):
        data['byweekday'] = [data['byweekday']]

      for index, item in enumerate(data['byweekday']):
        if isinstance(item, str):
          data['byweekday'][index] = WEEKDAYS[item.lower()]

        elif isinstance(item, list) and len(item) == 2:
          if isinstance(item[0], str):
            item[0] = WEEKDAYS[item[0].lower()]

          data['byweekday'][index] = WEEKDAYNO[item[0]](item[1])

    data.setdefault('bysecond', 0)

    if 'dtstart' in data:
      data['dtstart'] = self.now.replace(**data['dtstart'])
    else:
      data['dtstart'] = self.EPOCH

    return rrule.rrule(**data)

  def _check_schedule(self):
    contents = None
    filepath = os.path.join(os.getcwd(), self.schedule_filepath)

    try:
      with open(filepath, 'r') as file:
        contents = file.read()
    except FileNotFoundError as e:
      pass

    if not contents:
      return

    schedule_hash = hashlib.sha1(bytes(contents, encoding='utf-8')).hexdigest()
    if schedule_hash == self.schedule_hash:
      return

    self.schedule_hash = schedule_hash

    self.timezone = None
    self.cached_rrsets = []
    self.cached_exclusions = []
    self.cached_inclusions = []

    try:
      parsed = json.loads(contents)
    except Exception as e:
      print("Error loading schedule JSON: {}".format(str(e)))
      return

    self.timezone = tz.gettz(parsed.get('timezone', None))

    now = self.now

    for rrset_config in parsed.get('rrule_sets', []):
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

    exceptions = parsed.get('exceptions', {})

    for indate_config in exceptions.get('include', []):
      self.cached_inclusions.append(dict(
        datetime=now.replace(**indate_config['datetime']),
        params=indate_config['parameters'],
      ))

    for exdate_config in exceptions.get('exclude', []):
      date = now.replace(**exdate_config)
      self.cached_exclusions.append(date)

  def calculate_datetimes(self, threshold=None):
    if threshold is None:
      threshold = self.now

    datetimes = list(self.cached_inclusions)

    for alarm_rule in self.cached_rrsets:
      rrule_set = alarm_rule['rrule_set']
      temp_dt = rrule_set.after(threshold)

      while temp_dt in self.cached_exclusions:
        temp_dt = rrule_set.after(temp_dt)

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

      now = self.now
      threshold = now - datetime.timedelta(seconds=1)
      datetimes = sorted(self.calculate_datetimes(threshold), key=lambda _: _['datetime'])

      if datetimes:
        dt = datetimes[0]['datetime']
        params = datetimes[0]['params']
        name = params.get('name', None)

        delta = datetime.timedelta(seconds=5)
        if dt - delta < now < dt + delta and (name is None or name != self.rouser.alarm['name']):
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
