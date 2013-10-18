from collections import defaultdict

from stormdrain.bounds import Bounds
from stormdrain.pubsub import get_exchange
from mplevents import MPLaxesManager



class LinkedPanels(object):
    """ Helper class to manage updates of linked axes.
    
        Given a set of axes instances and associated names
        ax_specs = {ax1:(xname, yname), ax2:(xname2, yname2), ...}
        this class figures out which axes are linked, and ensures that their
        limits are kept in sync with each other. 
        
        This object also maintains a bounds object that strictly refers to the
        coordinates named in the ax_specs
        
        This solves the problem where time might be on one vertical axis and
        on another horizontal axis.
        
        This class is figure-agnostic, so it can handle a set of axes linked across figures.
    """

    # margin_defaults = {
    #         'xy':(0.1, 0.1, 0.7, 0.4),
    #         'xz':(0.1, 0.5, 0.7, 0.15),
    #         'zy':(0.8, 0.1, 0.15, 0.4),
    #         'tz':(0.1, 0.8, 0.85, 0.15),
    #         # 't': (0.1, 0.85, 0.8, 0.1),
    #         }        
    #     
    def __init__(self, ax_specs):
        # self.figure = figure
        # self.panels = {}
        self._D = 2 # dimension of the axes
        self._setup_events()
        
        self.axes_managers = {}
        self.bounds = Bounds()
        self.ax_specs = ax_specs
        
        # These axes are to be kept equal in aspect
        self.equal_ax = set()
        
        self.ax_coords = defaultdict(set)
        for ax, names in self.ax_specs.iteritems():
            self.add_axes(ax, names)
                
    def add_axes(self, ax, names):
        self.ax_specs[ax] = names
        assert len(names) == self._D
        for d in range(self._D):
            self.ax_coords[names[d]].add(ax)
            self.axes_managers[names] = MPLaxesManager(ax)
        
    def _setup_events(self):
        self.interaction_xchg = get_exchange('MPL_interaction_complete')
        self.interaction_xchg.attach(self)
        self.bounds_updated_xchg = get_exchange('SD_bounds_updated') 
        self.reflow_start_xchg = get_exchange('SD_reflow_start')
        self.reflow_done_xchg = get_exchange('SD_reflow_done')
            
    def reset_axes_events(self):
        for mgr in self.axes_managers.values():
            mgr.events.reset()
            
    def bounds_updated(self):
        self.bounds_updated_xchg.send(self.bounds)
        self.reflow_start_xchg.send('LinkedPanels triggered data reflow')
        self.reflow_done_xchg.send('LinkedPanels reflow done')

    def send(self, ax_mgr):
        """ MPL_interaction_complete messages are sent here """
        bounds = self.bounds
        # x_var, y_var = ax_mgr.coordinate_names['x'], ax_mgr.coordinate_names['y']
        axes = ax_mgr.axes
        if axes not in self.ax_specs:
            # the axes that were interacted with were not on this plot
            return

        x_var, y_var = self.ax_specs[axes]
        
        # Figure out if the axis limits have changed, and set any new bounds
        new_limits = axes.axis(emit=False)    # emit = False prevents infinite recursion    
        old_x, old_y = getattr(bounds, x_var), getattr(bounds, y_var)
        new_x, new_y = new_limits[0:2], new_limits[2:4]
        
        # figure out the necessary modifications to keep the axes square
        if axes in self.equal_ax:
            bbox_aspect = axes.bbox.height/axes.bbox.width
            new_dx, new_dy = new_x[1] - new_x[0], new_y[1] - new_y[0]
            # goal is dy/dx = bbox_aspect
            if new_dy/new_dx > bbox_aspect:
                # expand new_dx to get the right aspect
                goal_dx = new_dy/bbox_aspect
                half_delta_dx = 0.5*(goal_dx-new_dx)
                new_x = new_x[0] - half_delta_dx, new_x[1] + half_delta_dx
            else:
                # expand new_dy to get the right aspect
                goal_dy = bbox_aspect*new_dx
                half_delta_dy = 0.5*(goal_dy-new_dy)
                new_y = new_y[0] - half_delta_dy, new_y[1] + half_delta_dy
        
        # Update all axis limits for all axes whose coordinates match those 
        # of the changed axes
        axes_to_update = set()
        axes_to_update.update(self.ax_coords[x_var])
        axes_to_update.update(self.ax_coords[y_var])
        
        
        if (new_x != old_x) | (new_y != old_y):
            setattr(bounds, x_var, new_x)
            setattr(bounds, y_var, new_y)
            for ax in axes_to_update:
                these_coords = self.ax_specs[ax]
                ax.set_xlim(getattr(bounds, these_coords[0]))
                ax.set_ylim(getattr(bounds, these_coords[1]))
            
            self.bounds_updated()
