from email.message import EmailMessage

import smtplib
import socket


class Interface(object):
  def startup(self):
    raise NotImplemented()

  def check(self):
    raise NotImplemented()

  def shutdown(self):
    raise NotImplemented()


class EmailInterface(Interface):
  def __init__(self, **kwargs):
    self.info = kwargs
    self.server = None

  def startup(self):
    self.server = smtplib.SMTP(self.info['smtp_server'], int(self.info['smtp_port']))
    self.server.ehlo_or_helo_if_needed()
    self.server.login(self.info['address'], self.info['password'])

    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.connect(('8.8.8.8', 80))
    so.getsockname()

    self.server.sendmail()

  def shutdown(self):
    self.server.quit()
