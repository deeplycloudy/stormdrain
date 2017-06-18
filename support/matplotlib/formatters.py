from __future__ import absolute_import
import datetime

import numpy as np
from matplotlib.ticker import Formatter, EngFormatter

from matplotlib.dates import AutoDateFormatter


class SecDayFormatter(Formatter):
    
    def __init__(self, base_date, axis):
        self.reference_date = base_date
        self._axis = axis

    def __call__(self, x, pos=None):
        """ Formats seconds of the day to HHMM:SS.SSS
            Maximum resolution is 1 microsecond, due to limitiation in datetime
        """
        
        ref_date = self.reference_date
        tick_date = ref_date + datetime.timedelta(0, x)
        
        interval = self._axis.get_view_interval()
        delta_sec = interval[1] - interval[0]
        
        if (delta_sec < 30):
            fmt = '%S'
        else:
            fmt = '%H%M:%S'
        
        # for most plots, it seems like pos=1 is the first label, even though pos=0 is also requested.
        # some plots do in fact plot the label for both pos=0 and pos=1, so go with 1 for safety
        if pos == 1:
            fmt = '%H%M:%S'
        
        # This could be generated algorithmically - the pattern is obvious.
        frac_fmt = '%.6f'
        if delta_sec > 0.00005:
            frac_fmt = '%.5f'
        if delta_sec > 0.0005:
            frac_fmt = '%.4f'
        if delta_sec > 0.005:
            frac_fmt = '%.3f'
        if delta_sec > 0.05:
            frac_fmt = '%.2f'
        if delta_sec > 0.5:
            frac_fmt = '%.1f'
        if delta_sec > 5:
            frac_fmt = '%.0f'
            
        if pos is None:
            # Be verbose for the status readout
            fmt = '%H%M:%S'
            frac_fmt = '%.6f'
        
        # if pos is not None:
        #     print x, delta_sec, frac_fmt, frac_fmt % (tick_date.microsecond/1.0e6)
        
        time_str = tick_date.strftime(fmt)
        frac_str = frac_fmt % (tick_date.microsecond/1.0e6)
        return time_str + frac_str[1:]
            


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    
    basedate = datetime.datetime(2004,5,26)
    
    # times = range(86300, 86304)

    subplot_base = 311

    all_times = [np.arange(86399.993, 86400.005, .001),
                 np.arange(86395.0, 86403., .001),
                 np.arange(86299.993, 86600.005, 10)]
    
    
    for i, times in enumerate(all_times):
        ax = plt.subplot(subplot_base + i)
        ax.plot(times, np.arange(len(times)))
        ax.xaxis.set_major_formatter(SecDayFormatter(basedate, ax.xaxis))
        # ax.xaxis.set_major_formatter(SecondOfDayFormatter(basedate, ax.xaxis))
    plt.show()
    