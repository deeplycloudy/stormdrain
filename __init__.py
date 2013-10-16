"""

stormdrain events

SD_bounds_updated
Bounds have changed. Typically this happens in response to axes limits
changing on a plot, or filtering criteria on a dataset changing.

SD_reflow_start and SD_reflow_done 
These events, which often should follow a SD_bounds_updated event, is used to
trigger a reflow of datasets down their pipelines. After all workers using
this event complete, SD_reflow_done is sent to indicate that subsequent
actions using the data can complete. For instance, a plot could do a final
draw, since all artists should have received their updated data at this stage.

"""

SD_exchanges = {
    'SD_bounds_updated':"Bounds instance has been updated",
    'SD_reflow_start':"Global data reflow, often follows bounds change",
    'SD_reflow_done':"Signals that data reflow is complete; should follows SD_reflow_start",
    }