""" Why brawl4d? It's inherited from an old IDL-based 3D viewer that was designed to plot
    Balloons, Radar, and Aircraft with Lightning = BRAWL.

"""

import numpy as np

from stormdrain.bounds import BoundsFilter
from stormdrain.data import NamedArrayDataset
from stormdrain.pipeline import Branchpoint

from stormdrain.support.matplotlib.linked import LinkedPanels
from stormdrain.support.matplotlib.mplevents import MPLaxesManager
from stormdrain.support.matplotlib.artistupdaters import scatter_dataset_on_panels, FigureUpdater
from stormdrain.support.coords.filters import CoordinateSystemController

class Panels4D(LinkedPanels):
    # 1.618
    # 89,55,34,21,13,8,5,3,2,1,1,0

    dx = .89*0.55
    dz = .89*0.21
    mg = .89*0.05
    dy = dx
    dt = dx+dz 
    w = mg+dt+mg
    h = mg+dy+dz+mg+dz+mg
    aspect = h/w # = 1.30

    # Left, bottom, width, height
    margin_defaults = {
        'xy':(mg*aspect, mg, dx*aspect, dy),
        'xz':(mg*aspect, mg+dy, dx*aspect, dz),
        'zy':((mg+dx)*aspect, mg, dz*aspect, dy),
        'tz':(mg*aspect, mg+dy+dz+mg, dt*aspect, dz),
        }

    def __init__(self, *args, **kwargs):
        self.names_4D = kwargs.pop('names_4D', ('lon', 'lat', 'alt', 'time'))
        self.figure = kwargs.pop('figure', None)
        if self.figure is not None:
            fig = self.figure
            self.panels = {}
            self.panels['xy'] = fig.add_axes(Panels4D.margin_defaults['xy'])
            self.panels['xz'] = fig.add_axes(Panels4D.margin_defaults['xz'], sharex=self.panels['xy'])
            self.panels['zy'] = fig.add_axes(Panels4D.margin_defaults['zy'], sharey=self.panels['xy'])
            self.panels['tz'] = fig.add_axes(Panels4D.margin_defaults['tz'], sharey=self.panels['xz'])
            
            ax_specs = { self.panels['xy']: (self.names_4D[0], self.names_4D[1]), 
                         self.panels['xz']: (self.names_4D[0], self.names_4D[2]),
                         self.panels['zy']: (self.names_4D[2], self.names_4D[1]),
                         self.panels['tz']: (self.names_4D[3], self.names_4D[2]), }
            kwargs['ax_specs'] = ax_specs
            
        super(Panels4D, self).__init__(*args, **kwargs)
    
    
                
if __name__ == '__main__':
    import matplotlib
    fontspec = {'family':'Helvetica', 'weight':'bold', 'size':10}
    matplotlib.rc('font', **fontspec)
    
    import matplotlib.pyplot as plt
    
    
    panel_fig = plt.figure()
    panels = Panels4D(figure=panel_fig)
    fig_updater = FigureUpdater(panel_fig)
    
    data = np.asarray( [ ('The Most Toxic \nTown in America', 36.983, -94.833,  250. , 1.34 ),
                        ('Dublin, TX',                       32.087, -98.343,  446. , 5.25 ),
                        ('Floating Mesa',                    35.277, -102.049, 1064., 1.90 ),
                        ('Lubbock',                          33.582, -101.881, 984. , 5.37 ),
                        ('Stonehenge Replica',               31.892, -102.326, 886. , 7.01 ),
                        ('Very Large Array',                 34.079, -107.618, 2126., 4.23 ),
                       ],  
                       dtype = [ ('name', '|S32'), ('lat', '>f4'), ('lon', '>f4'), 
                                 ('alt', '>f4'), ('time', '>f4') ]  )
    # Create a dataset that stores numpy named array data, and automatically receives updates 
    # when the bounds of a plot changes.
    d = NamedArrayDataset(data)
    
    # Create a scatterplot representation of the dataset, and add the necessary transforms
    # to get the data to the plot. In this case, it's a simple filter on the plot bounds, and 
    # distribution to all the scatter artists. Might also add map projection here if the plot
    # were not directly showing lat, lon, alt.
    scatter_outlet_broadcaster = scatter_dataset_on_panels(panels=panels, color_field='time')
    scatter_updater = scatter_outlet_broadcaster.broadcast()
    branch = Branchpoint([scatter_updater,])
    brancher = branch.broadcast()
    bound_filter = BoundsFilter(target=brancher, bounds=panels.bounds)
    filterer = bound_filter.filter()
    d.target = filterer
    
    # Set an initial view.
    panels.panels['xy'].axis((-110, -90, 30, 40))
    panels.panels['tz'].axis((0, 10, 0, 5e3))
    # Shouldn't need these, since the previous two cover all coordinates
    # panels.panels['zy'].axis((0, 5e3, 30, 40,))
    # panels.panels['xz'].axis((-110, -90, 0, 5e3))



    # Now let's set up a second figure that has projected data. The unprojected axes act
    # as the master data controller, and control what data get re-flowed to the other plot.
                        
    panel2_fig = plt.figure()
    panels2 = Panels4D(figure=panel2_fig, names_4D=('x', 'y', 'z', 'time'))
    fig_updater2 = FigureUpdater(panel2_fig)
    
    scatter_outlet_broadcaster2 = scatter_dataset_on_panels(panels=panels2, color_field='time')
    scatter_updater2 = scatter_outlet_broadcaster2.broadcast()
    
    cs = CoordinateSystemController(33.5, -101.5, 0.0)
    cs_transformer = cs.project_points(target=scatter_updater2, x_coord='x', y_coord='y', z_coord='z', 
                        lat_coord='lat', lon_coord='lon', alt_coord='alt', distance_scale_factor=1.0e-3)

    # tap into the data that result from subsetting on the first axes.
    branch.targets.add(cs_transformer)
    panels2.panels['xy'].axis((-1000, 1000, -1000, 1000))
    panels2.panels['tz'].axis((0, 10, 0, 5))
    
    plt.show()