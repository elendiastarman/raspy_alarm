from email.message import Message

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
    print("Email interface started.")
    return

    self.server = smtplib.SMTP(self.info['smtp_server'], int(self.info['smtp_port']))
    self.server.ehlo_or_helo_if_needed()
    self.server.login(self.info['address'], self.info['password'])

    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.connect(('8.8.8.8', 80))
    ip_address = so.getsockname()

    msg = Message()
    msg.setcontent('ip address: {}'.format(ip_address))
    msg['Subject'] = 'Alarm started and ready'
    msg['From'] = self.info['address']
    msg['To'] = self.info['main_contacts']

    self.server.send_message(msg, from_addr=self.info['address'], to_addrs=self.info['main_contacts'])

  def check(self):
    print("Email interface checked.")

  def shutdown(self):
    print("Shutting down email interface.")
    self.server.quit()
