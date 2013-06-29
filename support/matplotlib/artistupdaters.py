import numpy as np

from stormdrain.pipeline import coroutine
from stormdrain.pubsub import get_exchange
from stormdrain.pipeline import Branchpoint

class FigureUpdater(object):
    def __init__(self, figure):
        self.figure=figure
        # Tell the figure to update (draw) when the bounds change.
        bounds_updated_xchg = get_exchange('SD_bounds_updated')
        bounds_updated_xchg.attach(self)
        
    def send(self, bounds):
        self.figure.canvas.draw()

def scatter_dataset_on_panels(d, panels, color_field=None):
    bounds_updated_xchg = get_exchange('SD_bounds_updated')
    all_outlets = []
    empty = [0,]
    for ax in panels.ax_specs:
        # create a new scatter artist
        art = ax.scatter(empty, empty, c=empty)
        
        # Need to update the color mapping using the specified color field. It needs to know that the
        # bounds have been updated in order to adjust the color limits.
        up = MappableRangeUpdater(art, color_field=color_field)
        bounds_updated_xchg.attach(up)
                
        # Need to update the actual scatter coordinate data on each scatter artist
        outlet = ScatterArtistOutlet(art, coord_names=panels.ax_specs[ax], color_field=color_field)

        all_outlets.append(outlet.update())

    brancher = Branchpoint(all_outlets)
    return brancher

class ScatterArtistOutlet(object):
    """ 
    Allow for the scatters to be colored by a solid color, by the number of points in the point index, or some field in the data array, subject to bounds.
    The first of the following that is not None, in order, is used: by_points, color_field, solid_color kwargs. 
    
    When colored by a field in the data array, the bounds for that field in the ax_bundle bounds are used first, and if those
    don't exist, the range of the data is used. This method prioritizes syncing colors if at all possible.
    
    If the method is constant color or points, we can't just color according to the limits in bounds.
    
    Instead, we need special handling in the artist. For points, we first need to aggregate the data. In the coroutine model, this means we need to aggregate at the origin.
    In a generator model, we need can aggregate just before sending the data to the artist.
    
    So, in our coroutine-based model, we must simply maintain a pool of data, all of which is aggregated after
    any new dataset is loaded, and shoved down the pipe upon a redraw request.
    
    
    coord_names is a 2-tuple of names in the array that is sent here that counts as a 
    color_field is the name of the field in a to be used to color the points.
    
    
    """
    def __init__(self, artist, coord_names=('x', 'y'),  color_field=None):
        self.artist = artist
        self.coords = coord_names
        self.color_field = color_field
        
    @coroutine
    def update(self):
        # print "now processing {0}".format(self.artist)
        while True:
            a = (yield)

            # print "artist got data ", a
            ax = self.artist.axes
            coords = self.coords
            # print "artist got coords ", coords
            x, y = a[coords[0]], a[coords[1]]
            new_scatter_data = np.asarray(zip(x,y))
            self.artist.set_offsets(new_scatter_data)
            
            if self.color_field is not None:
                colors = a[self.color_field]
                self.artist.set_array(colors)
                # try:
                #     c_min, c_max = self.ax_bundle.bounds[self.color_field]
                # except AttributeError:
                #     c_min, c_max = colors.min(), colors.max()
                # self.artist.set_clim(c_min, c_max)
                

            # ax.figure.canvas.draw()
    
class MappableRangeUpdater(object):
    def __init__(self, artist, color_field):
        self.color_field = color_field
        self.artist = artist
    
    def send(self, bounds):
        lim = bounds[self.color_field]
        self.artist.set_clim(lim[0], lim[1])
    

class LineArtistOutlet(object):
    def __init__(self, ax_bundle, artist):
        self.artist = artist
        self.ax_bundle = ax_bundle

    @coroutine
    def update(self):
        # print "now processing {0}".format(self.artist)
        while True:
            a = (yield)
            # print "artist got data ", a
            ax = self.artist.axes
            coords = self.ax_bundle.ax_specs[ax]
            # print "artist got coords ", coords
            x, y = a[coords['x']], a[coords['y']]
            self.artist.set_data(x, y)
            ax.figure.canvas.draw()
