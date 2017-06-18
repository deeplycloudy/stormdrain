from __future__ import absolute_import
from __future__ import print_function
from matplotlib.lines import Line2D
from matplotlib.widgets import Widget
from matplotlib import path

from stormdrain.pubsub import get_exchange
from stormdrain.pipeline import Segment, coroutine, CachedTriggerableSegment
from six.moves import zip



class LassoFilter(Segment):
    """ Filter data points based on a polygon lasso. 
    
        The keyword argument coord_names is a list of names in the named array
        to be filtered by self.filter()
    """
    def __init__(self, *args, **kwargs):
        self.coord_names = kwargs.pop('coord_names', [])
        self.verts = kwargs.pop('verts', None)
        super(LassoFilter, self).__init__(*args, **kwargs)
        
        
    def filter_mask(self, a):
        coord0 = self.coord_names[0]
        coord1 = self.coord_names[1]
        p = path.Path(self.verts)
        xys = list(zip(a[coord0], a[coord1]))
        in_poly_mask = p.contains_points(xys) == 1
        return in_poly_mask
    
    @coroutine
    def filter(self):
        """ Data flow into here """
        while True:
            a = (yield)
            # good = np.ones(a.shape, dtype=bool)
            in_poly_mask = self.filter_mask(a)           
            self.target.send(a[in_poly_mask])


class PolyLasso(Widget):
    """
    A lasso widget that allows the user to define a lasso region by
    clicking to form a polygon.
    """
    
    def __init__(self, figure, callback=None,
                 line_to_next=True,
                 useblit=True,
                 color='black'):
        """
        Create a new lasso.
        
        *ax* is the axis on which to draw
        
        *callback* is a function that will be called with arguments (*ax*, *line*, *verts*).
        *verts* is a list of (x,y) pairs that define the polygon, with the first and
        last entries equal.
        
        *line_to_next* controls whether or not a line is drawn to the current
        cursor position as the polygon is created
        
        *useblit* = *True* is the only thoroughly tested option.
        
        """
        self.axes = None
        self.figure = figure
        self.canvas = self.figure.canvas
        self.useblit = useblit
        self.line_to_next = line_to_next
        self.background = None
        self.color = color
        # if useblit:
        #     self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        
        
        self.verts = []
        self.line = None
        self.callback = callback
        self.cids = []
        self.cids.append(self.canvas.mpl_connect('button_release_event', self.onrelease))
        self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.onmove))

        # moved to after axes are chosen
        # self.cids.append(self.canvas.mpl_connect('draw_event', self.ondraw))
    
    def ondraw(self, event):
        """ draw_event callback, to take care of some blit artifacts """
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        if self.line:
            self.axes.draw_artist(self.line)
        self.canvas.blit(self.axes.bbox)
    
    def do_callback(self, event):
        """ idle_event callback after polygon is finalized. """
        # Clear out callbacks.
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        self.callback(self.axes, self.line, self.verts)
        self.cleanup()
    
    def cleanup(self):
        """ Remove the lasso line. """
        # Clear out callbacks
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        self.axes.lines.remove(self.line)
        self.canvas.draw()
    
    def finalize(self):
        """ Called when user makes the final right click """
        # all done with callbacks pertaining to adding verts to the polygon
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        self.cids = []
        
            # Matplotlib will not draw the closed polygon until we step completely
            # out of this routine. It is desirable to see the closed polygon on screen
            # in the event that *callback* takes a long time. So, delay callback until
            # we get an idle event, which will signal that the closed polygon has also
            # been drawn.
        self.cids.append(self.canvas.mpl_connect('idle_event', self.do_callback))
    
    def draw_update(self):
        """ Adjust the polygon line, and blit it to the screen """
        self.line.set_data(list(zip(*self.verts)))
        if self.useblit:
            self.canvas.restore_region(self.background)
            if self.axes is not None:
                self.axes.draw_artist(self.line)
                self.canvas.blit(self.axes.bbox)
        else:
            self.canvas.draw_idle()
    
    def onmove(self, event):
        """ Update the next vertex position """
        if self.line == None: return
        self.verts[-1] = ((event.xdata, event.ydata))
        if self.line_to_next:
            self.draw_update()
    
    def onrelease(self, event):
        """ User clicked the mouse. Add a vertex or finalize depending on mouse button. """
        if self.verts is None: return
        
        # detect the axes to draw in automatically on first click
        if (self.axes == None) & (event.inaxes is not None):
            self.axes = event.inaxes
            if self.useblit:
                self.background = self.canvas.copy_from_bbox(self.axes.bbox)
                self.cids.append(self.canvas.mpl_connect('draw_event', self.ondraw))
        else:
            if event.inaxes != self.axes: return
        
        if event.button == 3:
            # Right click - close the polygon
            # Set the dummy point to the first point
            self.verts[-1] = self.verts[0]
            self.draw_update()
            # Greater than three verts, since a triangle
            # has a duplicate point to close the poly.
            if len(self.verts)>3:
                self.do_callback(event)
                # self.finalize()
            else:
                print('Need at least three vertices to make a polygon')
                self.cleanup()
            return
        
        # The rest pertains to left click only
        if event.button != 1: return
        
        if (self.axes is not None):
            if (self.line == None):
                # Deal with the first click
                self.line=Line2D([event.xdata], [event.ydata],
                            linestyle='-', marker='s', color=self.color, lw=1, ms=4, animated=True)
                self.axes.add_line(self.line)
                self.verts.append((event.xdata, event.ydata))
        
            # finalize vertex at this click, set up a new one that changes as mouse moves
            self.verts[-1] = (event.xdata, event.ydata)
            self.verts.append((event.xdata, event.ydata))
        
            self.draw_update()
        

class LassoPayloadController(object):
    """ For convenience and descriptiveness, this object should be subclassed 
        and define a single Payload() property that names the actual property:

        class LassoSomePropertyController(LassoPayloadController):
            some_property = LassoPayloadController.Payload()
        prop_lasso_controller = LassoSomePropertyController( ... )
        
        View of this object could be a set of buttons that, e.g.
            change the payload state.
            
        Setting the payload to None prevents the payload from being sent.
            prop_lasso_controller.some_property = None 

    """
    @staticmethod
    def Payload():
        # Thanks Python Cookbook, 3rd. Ed!
        storage_name = '_payload' # matches attribute definition of None below.

        @property
        def prop(self):
            return getattr(self, storage_name)

        @prop.setter
        def prop(self, value):
            setattr(self, storage_name, value)
        return prop


    def __init__(self, *args, **kwargs):
        """ Register to receive lasso events. 

            cache_segment is typically set to receive the results of all data
            selection operations, as though it were a plot, so that the
            current plot state can be subset. The instantiator of this class
            should set the target of a data emitter to
            payload_lasso.cache_segment.cache_segment(), The target of the
            cache segment is a lasso_filter, followed by the addition of the
            payload, and finally, the target kwarg passed when this class is
            instantiated.

            On receiving a new lasso, trigger a resend of the cached data 
            to the dataset modifier.
        """
        self.target = kwargs.pop('target', None)
        self._payload = None
        self.lasso_filter = LassoFilter(target=self.add_payload_value(target=self.target))
        self.lasso_xchg = get_exchange('B4D_panel_lasso_drawn')
        self.lasso_xchg.attach(self)
        self.cache_segment = CachedTriggerableSegment(target=self.lasso_filter.filter())

    @coroutine
    def add_payload_value(self, target=None):
        while True:
            a = (yield)
            if (self._payload is not None) and (target is not None):
                target.send((a, self._payload))

    def send(self, msg):
        """ B4D_panel_lasso_drawn messages are sent here. 

            Set the state of the stormdrain.bounds.LassoFilter
            object to grab the right points.
        """
        panels, ax, lasso_line, verts = msg

        coord_names = panels.ax_specs[ax]
        self.lasso_filter.coord_names = coord_names
        self.lasso_filter.verts = verts
        if self._payload is None:
            # Don't send the payload - there's nothing to do.
            return
        else:
            self.cache_segment.resend_last()


class manager(object):    
    def __init__(self):
        import numpy
        from matplotlib.pyplot import figure, show
        
        self.x = numpy.arange(10.0)
        self.y = self.x**2.0
        self.charge = numpy.zeros_like(self.x)
        
        self.f = figure()
        ax = self.f.add_subplot(111)
        self.sc = ax.scatter(self.x, self.y, c=self.charge, vmin=-1, vmax=1, edgecolor='none')
        # self.sc.set_clim(-1, 1)
        
        self.lasso = PolyLasso(self.f, self.callback)
        self.f.canvas.widgetlock(self.lasso)
    
    def callback(self, ax, lasso_line, verts):
        
        print(verts)
        p = path.Path(verts)
        xys = list(zip(self.x, self.y))
        mask = p.contains_points(xys)

        print((self.x[mask]))
        print((self.y[mask]))
        self.charge[mask] = -1
        print((self.charge))
        self.lasso_line = lasso_line
        
        # not actually necessary ... scatter stores a ref to charge array
        # self.sc.set_array(self.charge)
        
        self.f.canvas.widgetlock.release(self.lasso)
    

if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Qt4Agg')
    from matplotlib.pyplot import figure, show
    m = manager()
    show()
