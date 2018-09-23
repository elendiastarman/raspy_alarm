import time
import gpiozero


class Rouser(object):
  def __init__(self, shaker_pin, button_pins, invert_on_off=False, beep_on_length=0.5, beep_off_length=0.5, alarms=None):
    self.shaker = gpiozero.Buzzer(shaker_pin)
    if invert_on_off:
      self.shaker.on, self.shaker.off = self.shaker.off, self.shaker.on  # maybe the shaker vibrates when it's "off"
    self.shaker.off()

    self.default_beep_on_length = beep_on_length
    self.default_beep_off_length = beep_off_length

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
    self.alarm_name = None  # string
    self.conditions_to_stop_alarm = None  # function run with self.buttons as argument

    self.running = True

  def main_loop(self):
    print("Rouser main loop running...")

    while self.running:
      # print("Ping - rouser")
      time.sleep(1)

      if self.conditions_to_stop_alarm:
        for or_cond in self.conditions_to_stop_alarm:
          for and_cond in or_cond:
            result = False
            try:
              result = and_cond(time.time(), self.buttons)
            except Exception as e:
              print("Error evaluating condition:", str(e))

            if not result:
              break

          else:
            break

        else:
          continue

        self.stop_alarm()

  def start_alarm(self, name, conditions=None):
    print("Starting alarm {}...".format(name))
    self.alarm_name = name
    beep_off_length = self.default_beep_off_length
    beep_on_length = self.default_beep_on_length

    if self.alarm_name in self.alarms:
      conditions = conditions or self.alarms[self.alarm_name].get('conditions', None)
      beep_off_length = self.alarms[self.alarm_name].get('off_time', self.default_beep_off_length)
      beep_on_length = self.alarms[self.alarm_name].get('on_time', self.default_beep_on_length)

    self.conditions_to_stop_alarm = conditions
    self.shaker.beep(beep_off_length, beep_on_length)

  def stop_alarm(self):
    print("Stopping alarm {}...".format(self.alarm_name))
    self.alarm_name = None
    self.conditions_to_stop_alarm = None
    self.shaker.off()

  def shutdown(self):
    print("Shutting down rouser.")
    self.stop_alarm()
    self.running = False
