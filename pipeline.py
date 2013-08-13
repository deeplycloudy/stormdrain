""" 
Idea for standardized hookup and vis of pipelines.

Requires that every segment's class takes target as the first argument to init, 
and kwargs thereafter. 

This might just be better handled by convention in writing them from scratch - use nested
parentheses and good formatting instead of a programmatic solution. The getattr(methname) is
pretty ugly, honestly. Why not simply register a list of instances and target coroutines? DRY?

segments = [(Segment, 'segment_func', {}),
            (BoundsFilter, 'filter', {'bounds':bounds}),
            (BoundsFilter, 'filter', {'bounds':bounds}),
            (Broadcast, 'broadcast', {})
           ]

End of the segment (first one inited) one does not require a target, and should be either Broadcast or an outlet.

register(segments, prior_segment=None, subsequent_segment=None)

from itertools import reversed
def register(segments, subsequent_segment=None):
    segchain = []
    seg = subsequent_segment
    for cls, meth, kws in reversed(segments):
        seg_reference = cls(subsequent_segment, **kws)
        crt = getattr(seg_reference, meth)
        seg = crt()

        segchain.append((seg_reference, seg))
        
    return segchain
    
        
"""


import time
from collections import deque

import numpy as np

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

            
# if we want ax_bundle to be in every segment, can we get it in there in the coroutine as part of that block?
@coroutine
def segment(ax_bundle, target):
    """ >>> segment(ax_bundle, (segment(ax_bundle, target)))
    """
    while True:
        a = (yield)
        # print "segment passthrough to ", target
        target.send(a)


class Segment(object):
    """ Class-based version useful for tracking a changing state or adjusting targets
        at a later time. Some '.dot' access overhead this way, of course.

        >>> Segment( ax_bundle, Segment(ax_bundle, None).process() )

        Is it also easier to disconnect and replumb the pipeline later if we use classes for
        all segments? Hopefully we're dealing with big chunks of data all at once so the
        call overhead isn't too bad.
    """

    def __init__(self, target=None): 
        self.target = target 
        
    # @coroutine
    # def process(self):
    #     while True:
    #         a = (yield)
    #         print "segment passthrough to ", target
    #         self.target.send(a)

            
@coroutine
def broadcast(targets):
    while True:
        stuff = (yield)
        for target in targets:
            # print "broadcast to ", target
            target.send(stuff)
        del stuff


class ItemModifier(Segment):
    """ Performs modification of data in the pipe using item_name as an 
        indexing value.
    
        The coroutine modify expects to recieve (indexable, value)
        and peforms the operation indexable[item_name] = value before sending
        indexable along to the next stage.
        
        Note that this is compatible with numpy arrays that have named dtypes.
        Every array entry for that name is set to the same value, unless
        value itself is an array with the same length as the named array.
    """
    
    def __init__(self, *args, **kwargs):
        self.name_to_modify = kwargs.pop('item_name', None)
        super(ItemModifier, self).__init__(*args, **kwargs)
    
    @coroutine
    def modify(self):
        while True:
            a, value = (yield)
            if self.name_to_modify is not None:
                a[self.name_to_modify] = value
                self.target.send(a)
                

class CachedTriggerableSegment(object):
    """ Mediates use of a pipelines by caching and resending on demand the last-received data

        By turning the cache into a queue, and adding a last_how_many argument to resend, this routine
        retains and can resends a complete history of pipeline activity, up to the cache_len limit (defaults to 1)

        The caching behavior assumes that there is only one inlet and one outlet - it's a straight coupler.

    """
    def __init__(self, target=None, cache_len=1):
        """ target is an activated coroutine."""
        self.target = target
        self.cache = deque([], cache_len)
        # self.inlet = self.cache_segment()

    @coroutine
    def cache_segment(self):
        while True:
            stuff = (yield)
            self.cache.append(stuff)
            # self.resend()

    def resend_last(self, n=1):
        # convert to list so we can use slicing
        for v in list(self.cache)[-n:]:
            self.target.send(v)



class Branchpoint(object):
    """ Class-based version useful for tracking a changing state or adjusting targets
        at a later time. Some '.dot' access overhead this way, of course.

        >>> brancher = Branchpoint( [target1, target2, ...] )

        Allows for flexible branching by maintaining a set (in the formal sense) of targets.
        brancher.targets.append(newtarget)
        brancher.targets.remove(existingtarget)
    """

    def __init__(self, targets): 
        """ Accepts a sequence of targets """
        self.targets = set(targets) # this perhaps should be a set and not a list, so it remains unique

    @coroutine
    def broadcast(self):
        while True:
            stuff = (yield)
            for target in self.targets:
                # print "broadcast to ", target
                target.send(stuff)
            del stuff

