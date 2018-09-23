from email.message import Message

import imaplib
import smtplib
import socket
import email
import json
import os
import re


class Interface(object):
  def startup(self):
    raise NotImplemented()

  def check(self):
    raise NotImplemented()

  def shutdown(self):
    raise NotImplemented()

  def _clean_address(self, email_address):
    parts = email_address.split('@')
    return parts[0] + '_' + parts[1].split('.')[0]


class EmailInterface(Interface):
  def __init__(self, **kwargs):
    self.scheduler = None

    self.info = kwargs
    self.smtp_server = None
    self.imap_server = None

    self.email_address = self.info['address']
    self.clean_address = self._clean_address(self.email_address)
    self.main_contacts = self.info['main_contacts']

  def _handle_email(self, email):
    print('Email from: {}'.format(email['From']))
    print('Email to: {}'.format(email['To']))
    print('Email subject: {}'.format(email['Subject']))

    from_addr = re.search('<(.*)>', email['From']).groups()[0]
    send_acknowledgement = False

    if self.scheduler:
      if email['Subject'].lower() == 'wake up now' and from_addr in self.info['wakeup_whitelist']:
        self.scheduler.rouser.start_alarm('wake up now', [[lambda t, b: False]])
        send_acknowledgement = True
      elif email['Subject'].lower() == 'cancel alarm' and from_addr in self.info['wakeup_whitelist']:
        self.scheduler.rouser.stop_alarm()
        send_acknowledgement = True

    if send_acknowledgement == True:
      self._send_email('Re: ' + email['Subject'], 'acknowledged', self.email_address, [from_addr])

  def _read_email(self):
    contents = None
    filepath = os.path.join(os.getcwd(), 'data', self.clean_address)

    try:
      with open(filepath, 'r') as file:
        file.seek(0)
        contents = file.read()
    except FileNotFoundError as e:
      pass

    if contents:
      data = json.loads(contents)
    else:
      data = {'latest_email': 0}

    self.imap_server.select('INBOX')
    response, email_ids = self.imap_server.search(None, 'ALL')
    if response != 'OK':
      print('COULD NOT READ {}'.format(self.email_address))
      return

    email_ids = sorted(map(int, email_ids[0].decode('utf-8').split()))
    # print('email_ids:', email_ids)

    for email_id in email_ids:
      if email_id < data['latest_email']:
        continue

      res, dat = self.imap_server.fetch(str(email_id), '(RFC822)')
      if res != 'OK':
        print('COULD NOT READ EMAIL {}'.format(email_id))
      else:
        message = email.message_from_string(dat[0][1].decode('utf-8'))
        self._handle_email(message)

    if email_ids:
      data['latest_email'] = email_ids[-1] + 1

    with open(filepath, 'w') as file:
      file.write(json.dumps(data))

  def _send_email(self, subject, content, from_addr=None, to_addrs=None):
    if from_addr is None:
      from_addr = self.email_address
    if to_addrs is None:
      to_addrs = self.main_contacts

    msg = Message()
    msg.set_payload(content)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)

    self.smtp_server.send_message(msg, from_addr=from_addr, to_addrs=to_addrs)

  def startup(self):
    print("Email interface started.")

    self.smtp_server = smtplib.SMTP_SSL(self.info['smtp_server'], int(self.info['smtp_port']))
    self.smtp_server.ehlo_or_helo_if_needed()
    self.smtp_server.login(self.info['address'], self.info['password'])

    self.imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
    self.imap_server.login(self.info['address'], self.info['password'])
    self.imap_server.select('INBOX')

    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.connect(('8.8.8.8', 80))
    ip_address = so.getsockname()

    self._send_email('Alarm started and ready', 'ip address: {}'.format(ip_address))

  def check(self):
    # print("Email interface checked.")
    self._read_email()

  def shutdown(self):
    print("  Shutting down email interface.")
    if self.smtp_server:
      self.smtp_server.quit()
    if self.imap_server:
      self.imap_server.logout()
