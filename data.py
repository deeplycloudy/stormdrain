from functools import wraps

import numpy as np
from numpy.lib.recfunctions import append_fields

from stormdrain.pubsub import get_exchange
from stormdrain.pipeline import coroutine

class BaseDate(object):
    def __init__(self, date):
        self.date=date

_default_index_name = 'point_id'

def indexed(index_name=_default_index_name):
    """ Decorator to add an index column to the data array in a NamedArrayDataset.
        Allows filtered arrays be linked to the original array after a lasso

        func returns an instance of NamedArrayDataset.
    """
    def wrapper(func):
        @wraps(func)
        def create_indexed(*args, **kwargs):
            d = func(*args, **kwargs)
            if d is not None:
                indices = np.arange(d.data.size)
                d.data = append_fields(d.data, index_name, indices, usemask=False)
            return d
        return create_indexed
    return wrapper

        
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
    
    @coroutine
    def update(self, index_name=_default_index_name, field_names=None):
        """ update the values in self.data using data received 
        
            This function assumes that the shapes of the data are compatible
            and have enough of the same dtype fields to complete the operation.
            If field_names is None, the dtypes must match exactly.
        """
        while True:
            a = (yield)
            indices = a[index_name]
            if field_names is not None:
                # update only one field
                for field_name in field_names:
                    self.data[field_name][indices] = a[field_name]
            else:
                # update everything
                self.data[indices] = a
                        
    def send(self, msg):
        """ SD_bounds_updated messages are sent here """
        # print 'Data object got message {0}'.format(msg)
        if self.target is not None:
            # print 'Sending from Data.'
            self.target.send(self.data)
