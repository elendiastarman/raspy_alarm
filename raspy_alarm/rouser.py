import time
import gpiozero


class Rouser(object):
  def __init__(self, shaker_pin, button_pins, invert_on_off=False, beep_on_length=0.5, beep_off_length=0.5):
    self.shaker = gpiozero.Buzzer(shaker_pin)
    if invert_on_off:
      self.shaker.on, self.shaker.off = self.shaker.off, self.shaker.on  # maybe the shaker vibrates when it's "off"
    self.shaker.off()

    self.beep_on_length = beep_on_length
    self.beep_off_length = beep_off_length

    self.buttons = {}
    for pin in button_pins:
      button = gpiozero.Button(pin)
      button.parent = self
      button.when_pressed = lambda b: b.parent.buttons[b.pin.number]['events'].append([time.time(), None])
      button.when_released = lambda b: b.parent.buttons[b.pin.number]['events'][-1].append(time.time())

      self.buttons[button.pin.number] = {
        'button': button,
        'events': [],
      }

    self.alarm_name = None  # string
    self.conditions_to_stop_alarm = None  # function run with self.buttons as argument

    self.shutdown = False

  def main_loop(self):
    while not self.shutdown:
      if self.conditions_to_stop_alarm and self.conditions_to_stop_alarm(self.buttons):
        self.stop_alarm()

      print("Ping - rouser")
      time.sleep(1)

  def start_alarm(self, name, conditions):
    self.alarm_name = name
    self.conditions_to_stop_alarm = conditions
    self.shaker.beep(self.beep_off_length, self.beep_on_length)

  def stop_alarm(self):
    self.alarm_name = None
    self.conditions_to_stop_alarm = None
    self.shaker.off()

  def shutdown(self):
    print("Shutting down rouser.")
    self.shutdown = True
