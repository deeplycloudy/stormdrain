.. stormdrain documentation master file, created by
   sphinx-quickstart on Sun Nov 17 20:35:26 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
.. _brawl4d: https://github.com/deeplycloudy/brawl4d

Stormdrain: a pipeline for evented data processing
==================================================


Stormdrain implements an opinionated data flow model that sits between domain-specific dataset models and general-purpose visualization packages.

It arose from the need to interactively explore irregular, multidimensional data from the atmospheric sciences, with a parallel goal of being a pure Python library that doesn't try to do to much. It provides programmatic hooks for access to data subsets that are selected interactively. As such, it is naturally used within IPython notebooks, which support both interactivity and scriptability. 

Stormdrain does not require adoption of a specific plotting package or data model, but instead provides a data transport abstraction. Data sit at the inlet of a pipeline, while the outlet of the pipeline could be something that knows how to update a plot, or a log file. Pipeline segments along the way serve as transforms and filters. A publish-subscribe event infrastructure allows intermediate segments to respond to changes determined by user interaction, and reflow data in response to these changes.

Such agnosticism avoids the need to adopt a new base-object class for the entire analysis stack or the need to learn the grammar of a new plotting package in order to gain the benefits of interactivity. Experts with certain datatypes simply use their existing data classes as the substance that flows through the pipe!

Build a pipeline
================

Use a coroutine as a pipeline segment
-------------------------------------

Each pipeline segment is a coroutine, which is a function that is decorated with `pipeline.coroutine`. Data are *pushed* down the pipe, instead of *pulled* (as with ordinary iteration using generators). Each segment can be an ordinary function::

    @coroutine
    def scale(target, scale=1.0)
        """ Receive a numpy array, and multiply it by a scaling factor"""
        while True:
            a = (yield)
            target.send(a*scale)

The pattern `input = (yield)`, some processing, and `target.send(output)` within an infinite loop is the basic template for each pipeline segment.

It is best if each pipeline segment implements a small, defined task. This makes the analysis chain easier to debug and test, and easier to reuse!
            

A class dynamically modifies the flow in a segment
--------------------------------------------------
        
For many interactive applications, it's helpful to have a class with coroutines as methods of the class. Then the class can store persistent state that can be changed in response to user interaction, and any data that flows down the pipe will pick up the changes.

There are pre-defined classes for broadcasting data to multiple targets, cached, triggerable pipeline segments, and other things. See the classes in `stormdrain.pipeline`.

Each class can register for event notification
----------------------------------------------

Using a class also makes it possible to register for events. Each class only can respond to one event (since the pub-sub event model simply calls `.send` on the registered object).

Each class only can respond to one event (since the pub-sub event model simply calls `.send` on the registered object). If you think your class needs to respond to more than one event, simply write a new class 


All three ideas are demonstrated in the following class.::

    from stormdrain.pubsub import get_exchange
    class Histogrammer(object):
        def __init__(self, target, x_range=(0.0, 100.0), dx=1.0)
            self.x_range = hist_range
            self.dx = 1.0
            
            # Whoever emits this event passes a tuple of new limits
            # each registered object's .send method.
            xchg = get_exchange('my_limit_update_event')
            xchg.attach(self)
            
        @coroutine
        def histogram_for_array(self):
            """ Receive a numpy array, and send (histo, edges) from numpy.histogram"""
            while True:
                a = (yield)
                bins = np.arange(self.x_range[0], self.x_range[1], self.dx)
                histo, edges = np.histogram(a, bins=bins)
                self.target.send((histo, edges))
                
        def send(self, new_limits):
            self.x_range = new_limits
            self.dx = (new_limits[1] - new_limits[0])/10.0


Pipeline segments are hooked up in reverse order
------------------------------------------------

Let's create the following pipeline::

    `data -> [scale] -> [Histogrammer] -> [printer]`

We'll print output and manually send some data down the pipe a few times. Instead of printer, you could also have an outlet that knows how to update a plot.::

    import numpy as np
    
    @coroutine
    def print():
        # No target - just prints output and waits for more to print
        while True:
            a = (yield)
            print a

    printer = print()
    histogrammer = Histogrammer(target=printer)
    scaler = scale(target=histogrammer.histogram_for_array())
    
    data = np.random.random(size=100) * 100.0
    # flow the data with 
    scaler.send(data)
    
    limits = get_exchange('my_limit_update_event')
    limits.send((3.0, 50.0))
    scaler.send(data)    
    limits.send((53.0, 98.5))
    scaler.send(data)
    

You can get at the data in a pipe
---------------------------------


You can create a class that receives the most-recent output, and stores it an an instance variable. This is basically what the `stormdrain.pipeline.CachedTriggerableSegment` does, except it also serves as an intermediate segment that passes its data along.

Strategically-placed `stormdrain.pipeline.Branchpoint` classes along the pipeline also make it possible to attach arbitrarily many listeners at any later time, as long as they can access the `Branchpoint` instance.

An example would be helpful here.

    

A complete, interesting example
===============================

brawl4d.py in this project's examples directory shows how to use stormdrain with matplotlib to control subsetting of multidimensional data.

There is a pre-defined class for storing a numpy structured (named) array at the inlet of a pipe (`stormdrain.data.NamedArrayDataset`). That inlet segment is automatically notified when a data reflow is needed. Such reflows usually follow a notification that the displayed region of the dataset (stored in a `stormdrain.bounds.Bounds` object) has changed. The `LinkedPanels` class in the included `matplotlib` support shows emits the necessary bounds-changed and reflow events after user interaction on a plot.

There is a separate brawl4d_ project that implements an complete version of this idea for datasets used to blend lightning mapping and thunderstorm observations.




Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

