""" Publish/subscribe model for events. The exchange naming is cooperative,
    such that it's best to use an ad-hoc namespace for message names, e.g., 
    "SD_bounds_updated".
    
    Formally, this could be repalced a register / unregister procedure for new modules,
    with perhaps some sort of descriptor of what sort of events are actually sent.
    In the meantime, the defaultdict suffices to allow the basic idea of subscription
    and distribution to be demonstrated.

    Adapted from
    https://github.com/dabeaz/python-cookbook/blob/master/src/12/implementing_publish_subscribe_messaging/exchange2.py

"""


from contextlib import contextmanager
from collections import defaultdict

class Exchange:
    """ Manually attach and detach, or subscribe with a context manager."""
    def __init__(self):
        self._subscribers = set()

    def attach(self, task):
        # could enforce recognized exchange name here
        self._subscribers.add(task)

    def detach(self, task):
        self._subscribers.remove(task)

    @contextmanager
    def subscribe(self, *tasks):
        for task in tasks:
            self.attach(task)
        try:
            yield
        finally:
            for task in tasks:
                self.detach(task)

    def send(self, msg):
        for subscriber in self._subscribers:
            subscriber.send(msg)


# Dictionary of all created exchanges
_exchanges = defaultdict(Exchange)

# Return the Exchange instance associated with a given name
def get_exchange(name):
    return _exchanges[name]

# Example of using the subscribe() method
if __name__ == '__main__':
    # Example task (just for testing)
    class Task:
        def __init__(self, name):
            self.name = name
        def send(self, msg):
            print('{} got: {!r}'.format(self.name, msg))

    task_a = Task('A')
    task_b = Task('B')

    exc = get_exchange('spam')
    with exc.subscribe(task_a, task_b):
        exc.send('msg1')
        exc.send('msg2')

    exc.send('msg3')

