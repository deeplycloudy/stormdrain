
from __future__ import absolute_import
import numpy as np
from six.moves import zip

def filled_plus(*args):
    """ Return a filled plus marker (suitable for use with scatter, for example)

        filled plus
    
        call signatures::

          filled_plus(width)
          filled_plus(bar_width, bar_height)

        Arguments:
        
            *bar_width*: width of the vertical bar as a fraction of the total symbol size
        
            *bar_height*: height of the horizontal bar as a fraction of the total symbol size
    
    
           c-----   winding as indicated by a,b,c
            |   |
        a  b|   |
        -----   -----   -
        |           |   |--- y_height (fraction of 0, 1)
        -----   -----   -
            |   |
            |   |
            -----
    
            |---|
              |
              | x_width (fraction of 0,1)

    """
    
    if len(args) == 1:
        bar_width = bar_height = args[0]
    else:
        bar_width, bar_height = args
    
    
    half_x = bar_width / 2.0
    half_y = bar_height / 2.0
    l_bar = 0.5 - half_x
    r_bar = 0.5 + half_x
    t_bar = 0.5 + half_y
    b_bar = 0.5 - half_y
    plus_x = (0.0,   l_bar, l_bar, r_bar, r_bar, 1.0,   1.0,   r_bar, r_bar, l_bar, l_bar, 0.0)
    plus_y = (t_bar, t_bar, 1.0,   1.0,   t_bar, t_bar, b_bar, b_bar, 0.0,   0.0,   b_bar, b_bar)
    plus_xy = list(zip(plus_x, plus_y))
    filled_plus_marker = (plus_xy, 0)
    return filled_plus_marker
    
def filled_x(pos_bar_width, neg_bar_width, alpha_deg):
    """ Return a filled x marker (suitable for use with scatter, for example)

        filled plus
    
        call signatures::

          filled_plus(x_height, y_height)

        Arguments:
        
            *pos_bar_width*: width of the positive slope bar as a fraction of the total symbol size
        
            *neg_bar_width*: height of the negative slope bar as a fraction of the total symbol size
            
            *alpha*: angle between horizontal and the positive slope, in degrees

                W - winding is clockwise from W
         /\    /\   <- positive slope bar
        /  \  /  \    /
        \   \/   /   / alpha
         \      /   ---------
         /      \
        /   /\   \  <- negative slope bar
        \  /  \  /  <- endcap is actually normal to the bars
         \/    \/
    """
    
    alpha = np.radians(float(alpha_deg))
    slope = np.tan(alpha)
    
    # cap is normal to slope, so it's the other part of 90 degrees.
    cap_slope = np.tan(np.pi/2.0-alpha)
    
    # strategy is to make a thin x, and then add offsets to get width
    # endpoints of the thin x in non-normalized space.
    ur = ( 1.0,  slope)
    ul = (-1.0,  slope)
    bl = (-1.0, -slope)
    br = ( 1.0, -slope)
    
    # half-deltas to go from the center of each bar
    # need to scale these by total size of the shape
    scale = np.sqrt(ur[0]**2.0+ur[1]**2.0)
    d_pos =  (pos_bar_width/2.0) * cap_slope * scale
    d_neg = -(neg_bar_width/2.0) * cap_slope * scale
    
    x = None 
    y = None
    
    # finally, find the max x,y coordinate and scale to 0,1
    
    
if __name__ == '__main__':
    from matplotlib import pyplot as plt
    x = np.arange(10)
    y = np.arange(10)
    c = np.arange(10)
    s = 10*(np.arange(10)+1)**2
    
    m = filled_plus(0.2,0.5)
    m1 = filled_plus(0.4)
    
    plt.scatter(x+1, y+1, c=c, s=s, marker=m, edgecolor=(0.5,0.5,0.5))
    plt.scatter(-11+x, -11+y, c=c, s=s, marker=m1, edgecolor='none')
    plt.show()