import time
import gpiozero

MAX_SHAKE_DURATION = 60 * 10  # 10 minutes in seconds


class Rouser(object):
  def __init__(self, shaker_pin, button_pins, alarms=None, invert_on_off=False, default_beep_on_length=0.5, default_beep_off_length=0.5, default_snooze_duration=600):
    self.shaker = gpiozero.Buzzer(shaker_pin)
    if invert_on_off:
      self.shaker.on, self.shaker.off = self.shaker.off, self.shaker.on  # maybe the shaker vibrates when it's "off"
    self.shaker.off()

    self.default_beep_on_length = default_beep_on_length
    self.default_beep_off_length = default_beep_off_length
    self.default_snooze_duration = default_snooze_duration

    self.buttons = {}
    for pin in button_pins:
      button = gpiozero.Button(pin)
      # button.parent = self
      button.when_pressed = lambda b: self.buttons[b.pin.number]['events'].append([time.time(), None])
      button.when_released = lambda b: self.buttons[b.pin.number]['events'][-1].append(time.time())

      self.buttons[button.pin.number] = {
        'button': button,
        'events': [],
      }

    self.alarms = alarms or {}
    self._reset_alarm()

    self.running = True

  def _reset_alarm(self):
    self.alarm = {
      'name': None,  # string
      'conditions_to_stop_alarm': None,  # callables that take the current time and a list of button presses as arguments
      'conditions_to_snooze_alarm': None,
      'beep_off_length': None,
      'beep_on_length': None,
      'shake_time': None,
      'snooze_time': None,
      'snooze_duration': None,
    }

  def _evaluate_conditions(self, conditions):
    current_time = time.time()

    for or_cond in conditions:
      for and_cond in or_cond:
        try:
          if not and_cond(current_time, self.buttons):
            break
        except Exception as e:
          print("Error evaluating condition:", str(e))
          break

      else:
        break

    else:
      return False

    return True

  def main_loop(self):
    print("Rouser main loop running...")

    while self.running:
      # print("Ping - rouser")
      time.sleep(1)

      if self.alarm['snooze_time']:
        if self.alarm['snooze_time'] + self.alarm['snooze_duration'] < time.time():
          self.resume_alarm()

      if self.alarm['shake_time'] and self['conditions_to_snooze_alarm']:
        if self._evaluate_conditions(self['conditions_to_snooze_alarm']):
          self.snooze_alarm()

      if self['conditions_to_stop_alarm']:
        if self._evaluate_conditions(self['conditions_to_stop_alarm']):
          self.stop_alarm()

      if self.alarm['shake_time'] + MAX_SHAKE_DURATION < time.time():
        self.stop_alarm()

  def start_alarm(self, name, stop_conditions=None, snooze_conditions=None, beep_off_length=None, beep_on_length=None, snooze_duration=None):
    print("Starting alarm {}...".format(name))
    self.alarm['name'] = name
    self.alarm['conditions_to_stop_alarm'] = stop_conditions
    self.alarm['conditions_to_snooze_alarm'] = snooze_conditions
    self.alarm['beep_off_length'] = beep_off_length or self.default_beep_off_length
    self.alarm['beep_on_length'] = beep_on_length or self.default_beep_on_length
    self.alarm['snooze_duration'] = snooze_duration or self.default_snooze_duration
    self.alarm['shake_time'] = None
    self.alarm['snooze_time'] = None

    if self.alarm['name'] in self.alarms:
      self.alarm['stop_conditions'] = self.alarm['stop_conditions'] or self.alarms[self.alarm['name']].get('stop_conditions', None)
      self.alarm['snooze_conditions'] = self.alarm['snooze_conditions'] or self.alarms[self.alarm['name']].get('snooze_conditions', None)
      self.alarm['beep_off_length'] = self.alarm['beep_off_length'] or self.alarms[self.alarm['name']].get('off_time', None)
      self.alarm['beep_on_length'] = self.alarm['beep_on_length'] or self.alarms[self.alarm['name']].get('on_time', None)
      self.alarm['snooze_duration'] = self.alarm['snooze_duration'] or self.alarms[self.alarm['name']].get('snooze_time', None)

    self.resume_alarm()

  def resume_alarm(self):
    self.alarm['shake_time'] = time.time()
    self.alarm['snooze_time'] = None
    self.shaker.beep(self.alarm['beep_off_length'], self.alarm['beep_on_length'])

  def snooze_alarm(self):
    self.shaker.off()
    self.alarm['snooze_time'] = time.time()
    self.alarm['shake_time'] = None

  def stop_alarm(self):
    print("Stopping alarm {}...".format(self.alarm['name']))
    self.shaker.off()
    self._reset_alarm()

  def shutdown(self):
    print("Shutting down rouser.")
    self.stop_alarm()
    self.running = False
