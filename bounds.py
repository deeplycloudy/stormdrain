import numpy as np

from stormdrain.pipeline import Segment, coroutine
        

class BoundsFilter(Segment):
    """ Filter showing use of the axes bounds to filter data from an array.

        Can't use one of these per panel instance, and then re-call the
        coroutine as necessary to set up individual segments, because the targets
        are different and we want the target in the class so we can hook/unhook 
        later. Would be interesting to chart out where things should live if
        we want to hook/unhook vs. save on memory or efficiency.

        The mechanics of how one breaks the pipeline and reconnects with a 
        modified filter are yet to be worked out - 

        There is another version of this class, to be written, that filters across
        all coordinates based on the bounds for all the axes.
        
        Could filter on 
            1. all limits in bounds (restrict_to == None, the default)
            2. intersection of a list of variable names and names in bounds
                (restrict_to = ('name1', 'name2', ...))
        Then check to see if the valid name and values from bounds should be transformed somehow
            transform_mapping = {'name2':('alternate_name', transform_func)}
            where transform_func accepts and returns a 2-tuple of min and max limit values from
            the name in bounds to the name in transform_mapping. alternate_name is a name in the
            array "a" that is passed in, and the function should transform from bounds to limits
            on "a"

    """
    
    def __init__(self, *args, **kwargs):
        bounds = kwargs.pop('bounds', None)
        restrict_to = kwargs.pop('restrict_to', None)
        transform_mapping = kwargs.pop('transform_mapping', {})
        super(BoundsFilter, self).__init__(*args, **kwargs)
        self.bounds = bounds
        self.restrict_to = restrict_to
        self.transform_mapping = transform_mapping
        
    @coroutine
    def filter(self):
        """ We set up the bounds and target here to save on lookup overhead.
            It also allows the pipeline to be broken and reinitialized if the
            target needs to change.

            Initialize with a matplotlib axes instance that is the target plot.
        """
        bounds = self.bounds
        target = self.target
        # coords_xy = self.ax_bundle.ax_specs[self.ax_bundle.panels['xy']]
        # coords_tz = self.ax_bundle.ax_specs[self.ax_bundle.panels['tz']]
        # x_name, y_name = coords_xy['x'], coords_xy['y']
        # t_name, z_name = coords_tz['x'], coords_tz['y']
        
        while True:
            a = (yield)
            lim = bounds.limits()
            good = np.ones(a.shape, dtype=bool)
            # print "Filter with limits {0}".format(lim)
            
            for k, (v_min, v_max) in lim:
                if self.restrict_to is not None:
                    if not(k in self.restrict_to):
                        continue
                if k in self.transform_mapping:
                    new_k, transform_func = self.transform_mapping[k]
                    v_min, v_max = transform_func((v_min, v_max))
                    k = new_k
                if k not in a.dtype.names:
                    # ensure that this array even has data of bounds_type=k
                    # implicitly ignores this bound, instead of returning empty
                    continue
                good &= (a[k] >= v_min) & (a[k] <= v_max)
            
            
            target.send(a[good])


class Bounds(object):
    """ Bounds is a class to hold a set of ranges (start,end) for different
        variables.  Bounds can be optionally initialized with another Bounds
        instance as a parent.  If bounds for a particular variable cannot be found
        within itself, the Bounds will try its parent.
    """

    def __init__(self, parent = None, **kwargs):
        self._parent = parent
        self._vars = []
        for bound, limits in kwargs.items():
            setattr(self, bound, limits)

    def __getattr__(self, attr):
        #If we're in this function, a straight lookup of the attribute within
        #the instance's dictionary has failed.  Therefore, we look to the
        #parent, if one exists, otherwise
        if self._parent:
            return getattr(self._parent, attr)
        else:
            return (None, None)

    def __setattr__(self, attr, val):
        if attr not in ['_parent','_vars']:
            # Check to see if we already have a value for this attribute. If so, just change the value.
            # Only look at vars, not parent, since want to be able to override parent
            if attr not in self._vars:
                self._vars.append(attr)
        self.__dict__[attr] = val

    def __getitem__(self, var):
        return getattr(self, var)
    
    def __iter__(self):
        #Return an iterator over all bounded variables, including those in
        #parent
        if self._parent:
            return iter(self._vars +
                [v for v in self._parent if v not in self._vars])
        else:
            return iter(self._vars)
    
    def limits(self):
        vars = [v for v in self]
        return zip(vars, (getattr(self, v) for v in vars))

