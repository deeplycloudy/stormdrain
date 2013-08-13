from stormdrain.pubsub import get_exchange

class BaseDate(object):
    def __init__(self, date):
        self.date=date


class NamedArrayDataset(object):
    def __init__(self, data, target=None):
        self.target = target
        self.data = data
        self.bounds_updated_xchg = get_exchange('SD_bounds_updated')
        
        # Need to find a way to detach when "done" with dataset. __del__ doesn't work
        # because of some gc issues. context manager doesn't exactly work, since the
        # dataset objects are not one-shot tasks; they live for the whole lifecycle.
        # Anyway, ignoring for now.
        self.bounds_updated_xchg.attach(self)
        
        
    def send(self, msg):
        """ SD_bounds_updated messages are sent here """
        # print 'Data object got message {0}'.format(msg)
        if self.target is not None:
            # print 'Sending from Data.'
            self.target.send(self.data)
