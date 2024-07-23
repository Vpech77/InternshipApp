import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
from shapely.ops import triangulate, unary_union
from shapely.geometry import LineString, Polygon, Point, MultiPoint
from shapely import contains, length
from cartagen4py.utils.geometry.segment import *
import warnings
warnings.filterwarnings('ignore')

################################### LABEL GRID ################################

def create_hexagonalCell(coords_min, coords_max, width):
    xstep = width*3
    ystep = width*2
    cols = list(np.arange(coords_min[0], coords_max[0]+xstep, xstep))
    rows = list(np.arange(coords_min[1], coords_max[1]+ystep, ystep))
    polygons = [Polygon([(x, y), 
                         (x + width, y),
                         (x+width+width/2, y+width),
                         (x + width, y+2*width),
                         (x, y+2*width),
                         (x-width/2, y+width)]) 
                for x in cols[:-1] for y in rows[:-1]]
    return polygons

def createGrid(puntos, width, height, typ):
    xmin, ymin, xmax, ymax = puntos.total_bounds
    if typ == 'square':
        cols = list(np.arange(xmin, xmax + width, width))
        rows = list(np.arange(ymin, ymax + height, height))
        polygons = [Polygon([(x, y), 
                             (x + width, y), 
                             (x + width, y + height), 
                             (x, y + height)]) 
                    for x in cols[:-1] for y in rows[:-1]]
    if typ == 'diamond':
        cols = list(np.arange(xmin-width, xmax + width, width))
        rows = list(np.arange(ymin-height, ymax + height, height))
        polygons = [Polygon([(x, y), 
                             (x + width / 2, y + height / 2), 
                             (x, y + height), 
                             (x - width / 2, y + height / 2)]) 
                    for x in cols[:-1] for y in rows[:-1]]
    if typ == 'hexagonal':
        width = width
        odd_coords_min = (xmin-width, ymin-width)
        odd_coords_max = (xmax+width, ymax)
        odd_poly = create_hexagonalCell(odd_coords_min, odd_coords_max, width)
        not_odd_coords_min = (odd_coords_min[0]+3/2*width, odd_coords_min[1]-width)
        not_odd_coords_max = (odd_coords_max[0], odd_coords_max[1]+width)
        not_odd_poly = create_hexagonalCell(not_odd_coords_min, not_odd_coords_max, width)
        polygons = odd_poly + not_odd_poly
    return gpd.GeoDataFrame({'geometry':polygons})

################################### DELAUNAY ################################

def delaunay_concave_hull(points, min_length):
    """
    This algorithm computes a concave hull from a set of points. The algorithm first computes the Delaunay triangulation of the set of points,
    and then removes iteratively the boundary edges that are longer than a parameter.
    The algorithm was proposed by Duckham et al. (https://doi.org/10.1016/j.patcog.2008.03.023)

    Parameters
    ----------
    points : the list of points we want to cover with a concave hull
    min_length : Minimal length of a boundary edge of the triangulation to stop the algorithm.

    Examples
    --------
    >>> points = [Point(1,1),Point(6,6),Point(1,6),Point(6,5),Point(2,4),Point(2,1), Point(1,4)]
    >>> delaunay_concave_hull(points, 2.0)
    <POLYGON ((1 1, 1 4, 1 6, 6 6, 6 5, 2 4, 2 1, 1 1))>
    """
    multipoint = MultiPoint(points)
    triangles = triangulate(multipoint)
    hull = unary_union(triangles)

    removed = []
    shrinkable = True
    while(shrinkable):
        hull_ext = hull.exterior
        longest = -1
        max_length = min_length
        i = 0
        for triangle in triangles:
            if(i in removed):
                i += 1
                continue

            # first check: if the triangle is inside the hull, pass to next
            if(triangle.intersects(hull_ext)==False):
                i += 1
                continue

            # regularity check: if the three points of the triangle are on the boundary, removing this triangle would create an invalid geometry
            if(hull_ext.intersects(Point(triangle.exterior.coords[0])) and hull_ext.intersects(Point(triangle.exterior.coords[1])) 
               and hull_ext.intersects(Point(triangle.exterior.coords[2]))):
                i += 1
                continue
            
            # check that we do not create a multipolygon
            if(hull.difference(triangle).geom_type == 'MultiPolygon'):
                i += 1
                continue

            segments = get_segment_list(triangle)
            for segment in segments:
                segment_length = segment.length()
                if segment_length > max_length:
                    max_length = segment_length
                    longest = i
            i += 1
        
        if longest == -1:
            break
        
        hull = hull.difference(triangles[longest])
        removed.append(longest)
    
    return hull

################################### SWING ################################

def init_gdf(points):
    points = points.drop_duplicates(subset=['geometry'])
    points["available"] = True
    points["notVisited"] = True
    return points.iloc[points.geometry.x.argsort().values].copy()

def ymax_point(points):

    ind_max = points.geometry.y.nlargest(1).index[0]
    return points.loc[ind_max, 'geometry']

def line(pt1, pt2):
    return LineString([[pt1.x, pt1.y], [pt2.x, pt2.y]])

def angle_3_pts(point1, point2, point3):
    angle1 = angle_2_pts(point2, point1)
    angle2 = angle_2_pts(point2, point3)
    return (angle2 - angle1)%(2*np.pi)
def angle_2_pts(point1, point2):
    x = point2.x - point1.x
    y = point2.y - point1.y
    return np.arctan2(y, x)

def angle(pt, pt0, pt00, direction):

    angle_deg = angle_3_pts(pt00, pt0, pt)*180/np.pi
    if direction == 'clockwise':
        angle_deg = 360-angle_deg
    if angle_deg == 0:
        return np.nan
    return angle_deg

def angle_min(ptIn, pt0, points):

    ind_min = ptIn.angle.idxmin()
    tmp_pt = ptIn.loc[ind_min, 'geometry']
    mini = ptIn.angle.min()
    gdf_occ = gpd.GeoDataFrame(geometry=ptIn.loc[ptIn.angle == mini, "geometry"])

    if len(gdf_occ):
        gdf_occ['l'] = [length(line(pt, pt0)) for pt in gdf_occ.geometry]
        ind_min = gdf_occ.l.idxmin()
        tmp_pt = gdf_occ.loc[ind_min, 'geometry']

    original_index = points[points.geometry == tmp_pt].index[0]
    return tmp_pt, ind_min, original_index

def valid_point(tmp_pt, pt0, lines):

    lines = lines[:-1]
    li = line(tmp_pt, pt0)
    for e in lines:
        if e.intersects(li) and lines[0].coords[0] != tmp_pt.coords[0]:
            return False
    return True

def next_point(points, r, lines, direction, pt0, pt00=None):

    points_in = [row[0] for row in zip(points.geometry, points.available, points.notVisited) 
              if row[0].within(pt0.buffer(r)) and row[0] != pt0 and row[0] != pt00 and row[1] and row[2]]

    ptIn = gpd.GeoDataFrame(geometry=gpd.GeoSeries(points_in))
    tmp_pt = None
    
    if not(ptIn.empty):
        if not(pt00):
            ptIn["angle"] = [angle(pt, pt0, Point(pt0.x, pt0.y+r), direction) for pt in ptIn.geometry]
            tmp_pt, ind, ind_ori = angle_min(ptIn, pt0, points)
        else:
            ptIn["angle"] = [angle(pt, pt0, pt00, direction) for pt in ptIn.geometry]
            tmp_pt, ind, ind_ori = angle_min(ptIn, pt0, points)

            while(not(valid_point(tmp_pt, pt0, lines))):
                points.loc[ind_ori, "notVisited"] = False
                ptIn = ptIn.drop(ind)
                if not(ptIn.empty):
                    tmp_pt, ind, ind_ori = angle_min(ptIn, pt0, points)
                else:
                    return tmp_pt
        points.loc[ind_ori, "available"] = False
    return tmp_pt

def swingSimpleLoop(points, r, direction, poly=None):
    points = init_gdf(points)
    pt_dep0 = ymax_point(points)
    lines = []
    pt_next = next_point(points, r, lines, direction, pt_dep0)

    if not(pt_next):
        ind = points[points.geometry == pt_dep0].index[0]
        return points.drop(ind), poly
    
    lines.append(line(pt_dep0, pt_next))
    pt_dep = pt_dep0
    pt_prev = pt_next

    while(pt_next.coords[0] != pt_dep0.coords[0]):
        pt_next = next_point(points, r, lines, direction, pt_prev, pt_dep)
 
        if not(pt_next):
            ind = points[points.geometry == pt_dep0].index[0]
            return points.drop(ind), poly
        pt_dep = pt_prev
        pt_prev = pt_next
        lines.append(line(pt_dep, pt_prev))

    polygon = Polygon([list(l.coords[0]) for l in lines])
    points['inside'] = contains(polygon, points.geometry)
    new_points = points.loc[points["available"] ^ points["inside"], "geometry"]
    new_points = gpd.GeoDataFrame(geometry=new_points)
    return new_points, polygon

def swing(points, r, direction='anticlockwise'):
    new_points, poly = swingSimpleLoop(points, r, direction)
    polygons = []

    while(not(new_points.empty)):
        if isinstance(poly, Polygon):
            polygons.append(poly)
        new_points, poly = swingSimpleLoop(new_points, r, direction, poly)
    if isinstance(poly, Polygon):
        polygons.append(poly)
    return polygons