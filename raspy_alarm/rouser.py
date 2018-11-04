import time
import datetime
import gpiozero


class Rouser(object):
  OUTPUTS = {}
  INPUTS = {}

  def __init__(self, name, output_pins, input_pins, alarms=None, invert_on_off=False, **additional_params):
    self.name = name

    # Initialize the output interface if needed
    self.output_pins = output_pins

    if output_pins[0] not in self.OUTPUTS:
      output = gpiozero.Buzzer(output_pins[0])
      if invert_on_off:
        output.on, output.off = output.off, output.on  # e.g. a particular shaker vibrates when it's "off"
      output.off()

      self.OUTPUTS[output_pins[0]] = output

    self.output = self.OUTPUTS[output_pins[0]]

    # Initialize the input interfaces if needed
    self.input_pins = input_pins
    self.toggle_pins = additional_params.get('toggle_pins', [])

    for pin in input_pins:
      if pin not in self.INPUTS:
        button = gpiozero.Button(pin)

        if pin in self.toggle_pins:
          button.when_pressed = lambda b: (self.alarm['onset_time'] is None) and (self.output.on() if (self.output.is_active ^ (not invert_on_off)) else self.output.off())

        else:
          button.when_pressed = lambda b: self.INPUTS[b.pin.number]['events'].append([time.time()])
          button.when_released = lambda b: self.INPUTS[b.pin.number]['events'][-1].append(time.time())

        self.INPUTS[pin] = {'button': button, 'events': []}

    self.alarms = alarms or {}
    self.alarm = {}
    self._reset_alarm()

    self.default_beep_on_length = additional_params.get('default_beep_on_length', 0.5)
    self.default_beep_off_length = additional_params.get('default_beep_off_length', 0.5)
    self.default_snooze_duration = additional_params.get('default_snooze_duration', 600)
    self.max_active_duration = additional_params.get('max_active_duration', 600)
    self.default_snooze_state = additional_params.get('default_snooze_state', 'off')

    self.running = True

  def _reset_alarm(self):
    self.old_alarm = self.alarm.copy()
    self.alarm = {
      'name': None,  # string
      'conditions_to_start_alarm': None,  # callables that take the current time and a list of button presses as arguments
      'conditions_to_stop_alarm': None,
      'conditions_to_snooze_alarm': None,
      'beep_off_length': None,
      'beep_on_length': None,
      'onset_time': None,
      'snooze_time': None,
      'snooze_duration': None,
      'snooze_state': None,
      'timezone': None,
    }

  def _evaluate_conditions(self, conditions):
    current_time = time.time()

    for or_cond in conditions:
      for and_cond in or_cond:
        try:
          if not and_cond(current_time, self.input_pins, self.INPUTS):
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
    print("Rouser \"{}\" main loop running...".format(self.name))

    while self.running:
      # print("Ping - rouser")
      time.sleep(1)

      for name, params in self.alarms.items():
        if params.get('start_conditions', None):
          if self._evaluate_conditions(params['start_conditions']):
            self.start_alarm(name)

      if self.alarm['snooze_time']:
        if self.alarm['snooze_time'] + self.alarm['snooze_duration'] < time.time():
          self.resume_alarm()

      if self.alarm['onset_time'] and self.alarm['conditions_to_snooze_alarm']:
        if self._evaluate_conditions(self.alarm['conditions_to_snooze_alarm']):
          self.snooze_alarm()

      if self.alarm['conditions_to_stop_alarm']:
        if self._evaluate_conditions(self.alarm['conditions_to_stop_alarm']):
          self.stop_alarm()

      if self.alarm['onset_time'] and self.alarm['onset_time'] + self.max_active_duration < time.time():
        self.stop_alarm()

  def start_alarm(self, name, start_conditions=None, stop_conditions=None, snooze_conditions=None, beep_off_length=None, beep_on_length=None, snooze_duration=None, snooze_state=None, timezone=None):
    if name is not None and name == self.alarm['name']:
      return

    self.alarm = {
      'name': name,
      'conditions_to_start_alarm': start_conditions,
      'conditions_to_stop_alarm': stop_conditions,
      'conditions_to_snooze_alarm': snooze_conditions,
      'beep_off_length': beep_off_length,
      'beep_on_length': beep_on_length,
      'snooze_duration': snooze_duration,
      'snooze_state': snooze_state,
      'onset_time': None,
      'snooze_time': None,
      'timezone': timezone,
    }

    if name in self.alarms:
      named_alarm = self.alarms[name]
      # overrides = {key: }
      self.alarm['conditions_to_start_alarm'] = self.alarm['conditions_to_start_alarm'] or named_alarm.get('start_conditions', None)
      self.alarm['conditions_to_stop_alarm'] = self.alarm['conditions_to_stop_alarm'] or named_alarm.get('stop_conditions', None)
      self.alarm['conditions_to_snooze_alarm'] = self.alarm['conditions_to_snooze_alarm'] or named_alarm.get('snooze_conditions', None)
      self.alarm['beep_off_length'] = self.alarm['beep_off_length'] or named_alarm.get('off_time', None)
      self.alarm['beep_on_length'] = self.alarm['beep_on_length'] or named_alarm.get('on_time', None)
      self.alarm['snooze_duration'] = self.alarm['snooze_duration'] or named_alarm.get('snooze_time', None)
      self.alarm['snooze_state'] = self.alarm['snooze_state'] or named_alarm.get('snooze_state', None)

    self.alarm['beep_off_length'] = self.alarm['beep_off_length'] or self.default_beep_off_length
    self.alarm['beep_on_length'] = self.alarm['beep_on_length'] or self.default_beep_on_length
    self.alarm['snooze_duration'] = self.alarm['snooze_duration'] or self.default_snooze_duration
    self.alarm['snooze_state'] = self.alarm['snooze_state'] or self.default_snooze_state

    print("Starting alarm {} at {}...".format(self.alarm['name'], datetime.datetime.now(tz=self.alarm['timezone'])))
    if name is None:
      print("Alarm settings:", self.alarm)

    self.resume_alarm()

  def resume_alarm(self):
    self.alarm['onset_time'] = time.time()
    self.alarm['snooze_time'] = None

    if self.alarm['beep_on_length']:
      self.output.beep(self.alarm['beep_off_length'], self.alarm['beep_on_length'])
    else:
      self.output.on()

  def snooze_alarm(self):
    if self.alarm['snooze_state'] == 'off':
      self.output.off()
    else:
      self.output.on()

    self.alarm['snooze_time'] = time.time()
    self.alarm['onset_time'] = None

  def stop_alarm(self):
    self.output.off()
    if any(self.alarm.values()):
      print("Stopping alarm {} at {}...".format(self.alarm['name'], datetime.datetime.now(tz=self.alarm['timezone'])))
      self._reset_alarm()

  def shutdown(self):
    print("Shutting down \"{}\" rouser.".format(self.name))
    self.stop_alarm()
    self.running = False
