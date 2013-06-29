from stormdrain.pubsub import get_exchange

# Names of recognized exchanges and a simple description of what they do.
mpl_exchanges = {
    'MPL_interaction_complete':"Plot limits have changed by user interaction and/or programmatic limit set. Message sent is MPLaxesManager instance",
    }


class Accumulator(object):
    """ Provides for event callbacks for matplotlib drag/release events and 
        axis limit changes by accumulating a series of event occurrences.
        Produces a single call to func after a user interacts with the plot.

        Also stores the axes that got the event, and passes them to func.

        Sample usage:

        from pylab import figure, show

        def simple(axes):
            print "update ", axes
        a = Accumulator(simple)

        f=figure()
        ax=f.add_subplot(111)
        plt=ax.plot(range(10))
        f.canvas.mpl_connect('draw_event', a.draw_event)
        f.canvas.mpl_connect('button_release_event', a.mouse_up_event)
        f.canvas.mpl_connect('button_press_event', a.mouse_down_event)
        ax.callbacks.connect('xlim_changed', a.axis_limit_changed)
        ax.callbacks.connect('ylim_changed', a.axis_limit_changed)
        show()

        """

    def __init__(self, func):
        self.func=func
        self.reset()
        self.mouse_up = True

    def reset(self):
        """ Reset flags after the update function is called.
            Mouse is tracked separately.
            """
        # print 'reset'
        self.limits_changed = 0
        self.got_draw = False
        self.axes = None

    def axis_limit_changed(self, ax):
        # print 'ax limits'
        self.limits_changed += 1
        self.axes = ax
        self.check_status()

    def draw_event(self, event):
        # print 'draw event'
        if self.limits_changed > 0:
            # only care about draw events if one of the axis limits has changed
            self.got_draw=True
        self.check_status()

    def mouse_up_event(self, event):
        # print 'mouse up'
        self.mouse_up = True
        self.check_status()

    def mouse_down_event(self, event):
        # print 'mouse down'
        self.mouse_up = False

    def both_limits_changed(self):
        """ Both x and y limits changed and the mouse is up (not dragging)
            This condition takes care of the limits being reset outside of a
            dragging context, such as the view-reset (home) button on the
            Matplotlib standard toolbar. 
            """
        # print "both_lim_chg"
        return (self.limits_changed >= 2) & self.mouse_up

    def interaction_complete(self):
        """ x, y, or both limits changed, and the mouse is up (not dragging).
            Also checks if matplotlib has done its final redraw of the screen, 
            which comes after the call to *both* set_xlim and set_ylim 
            have been triggered. The check for the draw event is the crucial 
            step in not producing two calls to self.func.
            
            New problem: with zoom, after a reset, get a draw event. on next axes change, the draw
            event  combines with an axis change to trigger interaction_complete. Then get another
            reset and ax limit change, and draw, and this passes again.
            Fixed this by adding a check on self.limits_changed > 0  in draw_event.
        """
        # print "interaction_complete"
        return (self.limits_changed>0) & self.got_draw & self.mouse_up

    def check_status(self):        
        if self.both_limits_changed() | self.interaction_complete():
            # print 'both limits:', self.both_limits_changed(), ', interaction:', self.interaction_complete()
            self.func(self.axes)
            self.reset()


class MPLaxesManager(object):

    def __init__(self, axes): #coordinate_names
        self.axes   = axes
        # self.coordinate_names = coordinate_names
        self.events = Accumulator(self.on_axes_changed)        
        
        self.callback_ids = {}
        self.callback_ids['draw_event'] = self.axes.figure.canvas.mpl_connect('draw_event', self.events.draw_event)
        self.callback_ids['button_press_event'] = self.axes.figure.canvas.mpl_connect('button_press_event', self.events.mouse_down_event)
        self.callback_ids['button_release_event'] = self.axes.figure.canvas.mpl_connect('button_release_event', self.events.mouse_up_event)
        self.callback_ids['xlim_changed'] = self.axes.callbacks.connect('xlim_changed', self.events.axis_limit_changed)
        self.callback_ids['ylim_changed'] = self.axes.callbacks.connect('ylim_changed', self.events.axis_limit_changed)


    def on_axes_changed(self, axes):
        """ Examine axes to see if axis limits really changed, and if so trigger a message. """

        # Expect that the axes where the event was generated are this instance's axes
        if axes != self.axes:
            return
            
        get_exchange('MPL_interaction_complete').send(self)

        