from numpy.lib.recfunctions import append_fields

from stormdrain.pipeline import coroutine
from stormdrain.support.coords.systems import MapProjection, GeographicSystem

class CoordinateSystemController(object):
    

    def __init__(self, ctr_lat, ctr_lon, ctr_alt=0.0):
        self.set_center(ctr_lat, ctr_lon, ctr_alt)
    
    def set_center(self, ctr_lat, ctr_lon, ctr_alt=0.0):
        self.ctr_lat = ctr_lat
        self.ctr_lon = ctr_lon
        self.ctr_alt = ctr_alt
        
        self._update_proj()
        
    def _update_proj(self, proj_name = 'aeqd', proj_datum = 'WGS84', proj_ellipse = 'WGS84'):
        ctr_lat = self.ctr_lat
        ctr_lon = self.ctr_lon
        ctr_alt = self.ctr_alt
        
        self.mapProj = MapProjection(projection=proj_name, ctrLat=ctr_lat, ctrLon=ctr_lon, lat_ts=ctr_lat, 
                                lon_0=ctr_lon, lat_0=ctr_lat, lat_1=ctr_lat, ellipse=proj_ellipse, datum=proj_datum)
        self.geoProj = GeographicSystem()
        
    @coroutine
    def project_points(self, target=None, x_coord='x', y_coord='y', z_coord='z', 
                        lat_coord='lat', lon_coord='lon', alt_coord='alt', distance_scale_factor=1.0):
        """ Pipeline segment. Receives array with lat,lon,alt coords as above,
            sends array with same shape but projected x,y,z coordinates appended.
            
            Use distance_scale_factor to conveniently convert from m to km.
        """
        while True:
            points = (yield)
            
            mapProj = self.mapProj
            geoProj = self.geoProj
            
            x,y,z = mapProj.fromECEF( 
                    *geoProj.toECEF(points[lon_coord], points[lat_coord], points[alt_coord])
                    )
                                         
            points = append_fields(points, (x_coord,y_coord,z_coord), 
                                           (x*distance_scale_factor,
                                            y*distance_scale_factor,
                                            z*distance_scale_factor)
                                            )
            
            target.send(points)
            del points

