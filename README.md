Stormdrain
==========
A pipeline for evented multidimensional data processing

Work with this data and streaming model, and you can accept events from any other framework to trigger modifications to your data.

Your data sit at the inlet of a pipeline, while the outlet of the pipeline could be something that knows how to update a plot. Along the way, build in transforms and filters that are linked to plot adjustments.



Matplotlib linked axes support
==============================
There are some helper classes in support.matplotlib to help manage linked axes that can't otherwise be shared by 

These are hooked into the stormdrain.bounds event support.