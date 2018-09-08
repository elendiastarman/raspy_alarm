from threading import Thread
from .scheduler import Scheduler
from .rouser import Rouser


def run():
  rouser = Rouser(2, [21], invert_on_off=True)
  rouser_thread = Thread(target=rouser.main_loop)

  scheduler = Scheduler(rouser)
  scheduler_thread = Thread(target=scheduler.main_loop)

  rouser_thread.start()
  scheduler_thread.start()


if __name__ == '__main__':
  run()
