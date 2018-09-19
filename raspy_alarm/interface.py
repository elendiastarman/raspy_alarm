class Interface(object):
  def check(self):
    raise NotImplemented()


class EmailInterface(Interface):
  pass
