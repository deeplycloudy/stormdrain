Stormdrain
==========
A pipeline for evented multidimensional data processing

Work with this data and streaming model, and you can accept events from any other framework to trigger modifications to your data.

Your data sit at the inlet of a pipeline, while the outlet of the pipeline could be something that knows how to update a plot. Along the way, build in transforms and filters that are linked to plot adjustments.



Matplotlib linked axes support
==============================
There are some helper classes in support.matplotlib to help manage linked axes that can't otherwise be shared by the sharex=ax support.

These are hooked into the stormdrain.bounds event support.

After a support.matplotlib.linked.LinkedPanels instance is created as <pre>panels</pre>, it's possible to create an additional figure, and sync its the limits of new axes with <pre>panels</pre> like so:

<pre>
from stormdrain.support.matplotlib.formatters import SecDayFormatter
from stormdrain.support.matplotlib.artistupdaters import FigureUpdater

tE_fig = plt.figure()
tE_ax  = tE_fig.add_subplot(111)

# Put the new axes under the control of the LinkedPanels instance, which is figure-agnostic

print panels.names_4D
panels.add_axes(tE_ax, ('time', 'Efield'))
tE_fig_updater = FigureUpdater(tE_fig)
tE_ax.xaxis.set_major_formatter(SecDayFormatter(panels.basedate, tE_ax.xaxis))

# load some data as a named array
data = np.ones(10, dtype=[('t','f4'), ('E','f4')])
tE_ax.plot(data['t'], data['E'])
</pre>

The code above naturally extends panels from brawl4d.py in the folder of examples.