import matplotlib
matplotlib.use('WxAgg')

from matplotlib.lines import Line2D
from matplotlib.widgets import Widget
from matplotlib.nxutils import points_inside_poly

from stormdrain.pipeline import Segment, coroutine

class LassoFilter(Segment):
    """ Filter data points based on a polygon lasso. 
    
        The keyword argument coord_names is a list of names in the named array
        to be filtered by self.filter()
    """
    def __init__(self, *args, **kwargs):
        self.coord_names = kwargs.pop('coord_names', [])
        super(LassoFilter, self).__init__(*args, **kwargs)
        
        self.verts = None
    
    @coroutine
    def filter(self):
        """ Data flow into here """
        while True:
            a = (yield)
            # good = np.ones(a.shape, dtype=bool)
            
            coord0 = self.coord_names[0]
            coord1 = self.coord_names[1]
            in_poly_mask = points_inside_poly(zip(a[coord0], a[coord1]), self.verts) == 1                    
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
        
        *useblit* = *True* is the only thorougly tested option.
        
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
        self.line.set_data(zip(*self.verts))
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
                print 'Need at least three vertices to make a polygon'
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
        


class manager(object):
    def __init__(self):
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
        
        print verts
        mask = points_inside_poly(zip(self.x, self.y), verts) == 1
        print self.x[mask]
        print self.y[mask]
        self.charge[mask] = -1
        print self.charge
        self.lasso_line = lasso_line
        
        # not actually necessary ... scatter stores a ref to charge array
        # self.sc.set_array(self.charge)
        
        self.f.canvas.widgetlock.release(self.lasso)
    

if __name__ == '__main__':
    import numpy
    from matplotlib.nxutils import points_inside_poly
    from matplotlib.pyplot import figure, show
    m = manager()
    show()