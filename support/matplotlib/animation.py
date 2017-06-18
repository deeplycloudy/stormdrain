from __future__ import absolute_import
import time

import numpy as np
from matplotlib.animation import TimedAnimation

from stormdrain.pipeline import coroutine, CachedTriggerableSegment

class FixedDurationAnimation(TimedAnimation):
    """ If this gets too slow, might look at pre-rendered matplotlib ArtistAnimation for inspiration """
    def __init__(self, fig, duration, coordinator, **kwargs):
        """ Draw a TimedAnimation on figure *fig* over the given *duration* (in seconds) 
            at *interval* (in ms).
        
            The draw operation is delegated to *coordinator*, a class which should implement
                init_draw(self, animator)
                draw_frame(self, animator, fraction_of_total_animation)
                cleanup(self, animator)
            to clear the figure and draw the frames, respectively.
            Cleanup is called when the animation has finished.
        """
        
        self._duration = float(duration)
        self._coordinator = coordinator
        
        super(FixedDurationAnimation, self).__init__(fig, **kwargs)
        
    def _step(self, *args):
        # add an opportunity to cleanup if the animation has stopped.
        # the repeat functionality of TimedAnimation is ensured by calling 
        # the superclass first.
        still_going = super(FixedDurationAnimation, self)._step(*args)
        if not still_going:
            self._coordinator.cleanup(self)
        return still_going
        
        
    def new_frame_seq(self):
        # the code below works, but takes unpredictably too long
        # if the frames take longer to draw than self._interval.
        # fps = 1000. / self._interval
        # n_frames = self._duration * fps
        # fractions = list(np.arange(0.0, 1.0, 1.0/n_frames)) 
        # fractions += [1.0] #ensure we always get to 100% complete
        # return iter(fractions)
        
        def frame_iter():
            duration = self._duration
            start = time.time()
            time_fraction = 0.0
            while time_fraction < 1.0:
                time_fraction = (time.time() - start) / duration
                time_fraction = min(time_fraction, 1.0) # never exceed 1.0
                yield time_fraction
            
        return frame_iter()

    def _draw_frame(self, framedata):
        fraction = framedata
        self._coordinator.draw_frame(self, fraction)

    def _init_draw(self):
        self._coordinator.init_draw(self)
    


class PipelineAnimation(object):
    def __init__(self, duration, outlets, variable='time', limits=(0,1), branchpoint_data_source=None):
        """ Limits are usually the bounds of the current view in *variable* 
        
            Outlets are a set of coroutines that receive subsetted arrays to be drawn.
            
            The data array to be animated should come from branchpoint_data_source, 
            an instance of pipeline.Branchpoint
        """
        self.tstart = time.time()
        self.duration = duration
        self.outlets = outlets
        self.branchpoint_data_source = branchpoint_data_source
        
        self.filterer=self._filter_to_fraction(variable, limits)
        
        self.cache_trigger = CachedTriggerableSegment(target=self.filterer)
        self.cache_segment = self.cache_trigger.cache_segment()
        if branchpoint_data_source is not None:
            branchpoint_data_source.targets.add(self.cache_segment)
            
    def cleanup(self, animator):
        self.branchpoint_data_source.targets.remove(self.cache_segment)
                
    @coroutine
    def _filter_to_fraction(self, variable, limits):
        start = limits[0]
        limit_span = limits[1] - limits[0]
        while True:
            a = (yield)
            elapsed = self._time_fraction*limit_span
            current = (a[variable] >= start) & (a[variable] <= (start + elapsed))
            subset = a[current]
            for updater in self.outlets:
                updater.send(subset)
        
    def draw_frame(self, animator, time_fraction):
        self._time_fraction = time_fraction
        self.cache_trigger.resend_last()
    
    def init_draw(self, animator):
        self._time_fraction = 0.0
        self.cache_trigger.resend_last()
        
