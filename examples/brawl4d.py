import numpy as np

from stormdrain.bounds import BoundsFilter
from stormdrain.data import NamedArrayDataset

from stormdrain.support.matplotlib.linked import LinkedPanels
from stormdrain.support.matplotlib.mplevents import MPLaxesManager
from stormdrain.support.matplotlib.artistupdaters import scatter_dataset_on_panels, FigureUpdater


# Names of recognized exchanges and a simple description of what they do.
# brawl4d_exchanges = {
#     'B4D_panel_bounds_updated':"messaged when the bounds in a 4D panel plot changes",
#     'B4D_panel_redraw':"messaged when a panel redraw is necessary",
#     }

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
        self.figure = kwargs.pop('figure', None)
        if self.figure is not None:
            fig = self.figure
            self.panels = {}
            self.panels['xy'] = fig.add_axes(Panels4D.margin_defaults['xy'])
            self.panels['xz'] = fig.add_axes(Panels4D.margin_defaults['xz'], sharex=self.panels['xy'])
            self.panels['zy'] = fig.add_axes(Panels4D.margin_defaults['zy'], sharey=self.panels['xy'])
            self.panels['tz'] = fig.add_axes(Panels4D.margin_defaults['tz'], sharey=self.panels['xz'])
            
            ax_specs = { self.panels['xy']: ('lon', 'lat'), 
                         self.panels['xz']: ('lon', 'alt'),
                         self.panels['zy']: ('alt', 'lat'),
                         self.panels['tz']: ('time', 'alt'), }
            kwargs['ax_specs'] = ax_specs
            
        super(Panels4D, self).__init__(*args, **kwargs)
            
        # for mgr in self.axes_managers.values():
        #     mgr.interaction_callback = self.update_bounds_after_interaction


    # def coord_names_4d(self):
    #     """ Return the names of the x, y, z and time coordinates"""
    #     panels = self.panels
    #     xy_spec = self.ax_specs[ panels['xy'] ]
    #     tz_spec = self.ax_specs[ panels['tz'] ]
    #     x_coord, ycoord, z_coord, t_coord = xy_spec['x'], xy_spec['y'], tz_spec['y'], tz_spec['x']
    #     return x_coord, ycoord, z_coord, t_coord
    # def panel_name_for_axis(self, ax):
    #     for panel_name, axis in self.panels.iteritems():
    #         if axis is ax:
    #             return panel_name
                
                
if __name__ == '__main__':
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
    scatter_outlet_broadcaster = scatter_dataset_on_panels(d, panels=panels, color_field='time')
    scatter_updater = scatter_outlet_broadcaster.broadcast()
    bound_filter = BoundsFilter(target=scatter_updater, bounds=panels.bounds)
    filterer = bound_filter.filter()
    d.target = filterer
    
    
    # Set an initial view.
    panels.panels['xy'].axis((-110, -90, 30, 40))
    panels.panels['tz'].axis((0, 10, 0, 5e3))
    # Shouldn't need these, since the previous two cover all coordinates
    # panels.panels['zy'].axis((0, 5e3, 30, 40,))
    # panels.panels['xz'].axis((-110, -90, 0, 5e3))

    
    plt.show()