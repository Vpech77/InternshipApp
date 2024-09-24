import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
from shapely.ops import triangulate, unary_union
from shapely.geometry import LineString, Polygon, Point, MultiPoint
from shapely import contains, length
from cartagen.utils.geometry.segment import *
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

################################### Quadtree ################################

class PointSetQuadTree():

    """A class implementing a point set quadtree."""

    def __init__(self, envelope, max_points=1, depth=0):
        """Initialize this node of the quadtree.

        envelope is a shapely Polygon object defining the region from which points are
        placed into this node; max_points is the maximum number of points the
        node can hold before it must divide (branch into four more nodes);
        depth keeps track of how deep into the quadtree this node lies.

        """
        self.envelope = envelope
        self.max_points = max_points
        self.points = []
        self.depth = depth
        # A flag to indicate whether this node has divided (branched) or not.
        self.divided = False
        self.grid = []
        
    
    def __str__(self):
        """Return a string representation of this node of the QuadTree, suitably formatted."""
        sp = ' ' * self.depth * 2
        s = str(self.boundary) + '\n'
        s += sp + ', '.join(str(point) for point in self.points)
        if not self.divided:
            return s
        return s + '\n' + '\n'.join([
                sp + 'nw: ' + str(self.nw), sp + 'ne: ' + str(self.ne),
                sp + 'se: ' + str(self.se), sp + 'sw: ' + str(self.sw)])
    
    def divide(self):
        """Divide (branch) this node by spawning four children nodes."""

        cx, cy = self.envelope.centroid.x, self.envelope.centroid.y
        length = abs(self.envelope.bounds[0]) - (self.envelope.bounds[2])
        # The boundaries of the four children nodes are "northwest",
        # "northeast", "southeast" and "southwest" quadrants within the
        # boundary of the current node.
        self.sw = PointSetQuadTree(Polygon([(cx - length/2, cy - length/2), (cx, cy - length/2), (cx, cy), (cx - length/2, cy), 
                                            (cx - length/2, cy - length/2)]),
                                    self.max_points, self.depth + 1)
        self.se = PointSetQuadTree(Polygon([(cx, cy - length/2), (cx + length/2, cy - length/2), (cx + length/2, cy), (cx, cy), 
                                            (cx, cy - length/2)]),
                                    self.max_points, self.depth + 1)
        self.nw = PointSetQuadTree(Polygon([(cx - length/2, cy), (cx, cy), (cx, cy + length/2), (cx - length/2, cy + length/2), 
                                            (cx - length/2, cy)]),
                                    self.max_points, self.depth + 1)
        self.ne = PointSetQuadTree(Polygon([(cx, cy), (cx + length/2, cy), (cx + length/2, cy + length/2), (cx, cy + length/2), 
                                            (cx, cy)]),
                                    self.max_points, self.depth + 1)
        self.divided = True
    
    def insert(self, point):
        """Try to insert a point from a GeoDataFrame into this QuadTree."""

        if not self.envelope.contains(point['geometry']):
            # The point does not lie inside boundary: bail.
            return False
        if len(self.points) < self.max_points:
            # There's room for our point without dividing the QuadTree.
            self.points.append(point)
            return True

        # No room: divide if necessary, then try the sub-quads.
        if not self.divided:
            self.divide()
            for prev_point in self.points:
              (self.ne.insert(prev_point) or
                self.nw.insert(prev_point) or
                self.se.insert(prev_point) or
                self.sw.insert(prev_point))  

        return (self.ne.insert(point) or
                self.nw.insert(point) or
                self.se.insert(point) or
                self.sw.insert(point))
    
    def __len__(self):
        """Return the number of points in the quadtree."""

        npoints = len(self.points)
        if self.divided:
            npoints += len(self.nw)+len(self.ne)+len(self.se)+len(self.sw)
        return npoints

    def draw(self, ax, grid, max_depth=None):
        """Draw a representation of the quadtree on Matplotlib Axes ax."""
        linewidth, color = 0.5, 'gray'

        if max_depth is not None:
            if self.depth <= max_depth:
                linewidth, color = 1, 'blue'
                
        x1, y1, x2, y2 = self.envelope.bounds
        ax.plot([x1,x2,x2,x1,x1],[y1,y1,y2,y2,y1], color=color, linewidth=linewidth)

        if self.divided:
            self.nw.draw(ax, grid, max_depth)
            self.ne.draw(ax, grid, max_depth)
            self.se.draw(ax, grid, max_depth)
            self.sw.draw(ax, grid, max_depth)
            
    def setGrid(self, grid, max_depth):

        if max_depth is not None:
            if self.depth <= max_depth:
                x1, y1, x2, y2 = self.envelope.bounds
                poly = Polygon([[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]])
                grid.append(poly)

        if self.divided:
            self.nw.setGrid(grid, max_depth)
            self.ne.setGrid(grid, max_depth)
            self.se.setGrid(grid, max_depth)
            self.sw.setGrid(grid, max_depth)

    def populate(self, geodataframe):
        """Populate the quadtree with the points contained in a GeoDataFrame, with a Point geometry"""

        for index, feature in geodataframe.iterrows():
            self.insert(feature)

    def get_all_points(self):
        all_points = []
        for point in self.points:
            all_points.append([point, self.depth])
        if self.divided:
            for point, depth in self.nw.get_all_points():
                all_points.append([point, depth])
            for point, depth in self.sw.get_all_points():
                all_points.append([point, depth])
            for point, depth in self.ne.get_all_points():
                all_points.append([point, depth])
            for point, depth in self.se.get_all_points():
                all_points.append([point, depth])
        return all_points

def reduce_points_quadtree(points, depth, mode='simplification', attribute=None):
    """
    Reduce a set of points using a quadtree.

    This algorithm was proposed by Bereuter & Weibel. :footcite:p:`bereuter:2012`
    The quadtree algorithm iteratively divide the point set into four chunks, creating clusters,
    until the depth parameter is reach or only one point remain per cluster.

    Parameters
    ----------
    points : GeoDataFrame of Point
        The point set to reduce.
    depth : int
        The maximum depth of the quadtree. This acts as a
        selector for the wanted degree of generalisation.
        The lower the value, the more generalised the point set will be.
    mode : str, optional
        There are three available modes:

        - *'selection'* means that for one cell, the algorithm retains
          the point with the largest value in the chosen attribute,
          weighted by the depth of the point. This option requires
          the attribute parameter to be provided.
        - *'simplification'* means that the point retained in the cell
          is the closest to the center of the cell.
        - *'aggregation'* means the points are all aggregated to
          the centroid of the points.
    
    Returns
    -------
    reduced : list of tuple
        The reduced points as tuples composed of three elements:

        #. The geometry of the reduced point
        #. The index of the point in the initial Geodataframe (-1 if the point was created)
        #. The amount of initial points replaced (which can be used to weight the size of the symbol of this point).
    
    quadtree : QuadTree
        The quadtree object.

    See Also
    --------
    reduce_points_kmeans :
        Reduce a set of points using K-Means clustering.

    References
    ----------
    .. footbibliography::
    """

    # First get the extent of the quadtree

    # Then create the quadtree and populate it with the points
    xmin, ymin, xmax, ymax = points.geometry.total_bounds
    length = max(xmax-xmin, ymax-ymin)
    domain = Polygon([(xmin, ymin), (xmin + length, ymin), (xmin + length, ymin + length), (xmin, ymin + length), (xmin,ymin)])
    qtree = PointSetQuadTree(domain, 1)
    qtree.populate(points)

    cells = []
    # get all the quadtree cells at the good depth
    cells_to_process = []
    cells_to_process.append(qtree.sw)
    cells_to_process.append(qtree.nw)
    cells_to_process.append(qtree.se)
    cells_to_process.append(qtree.ne)
    while len(cells_to_process) > 0:
        current_cell = cells_to_process.pop()
        if(current_cell.depth > depth):
            continue
        elif current_cell.depth < depth and current_cell.divided:
            cells_to_process.append(current_cell.sw)
            cells_to_process.append(current_cell.nw)
            cells_to_process.append(current_cell.se)
            cells_to_process.append(current_cell.ne)
        elif current_cell.depth < depth and not current_cell.divided:
            cells.append(current_cell)
            current_cell
        else:
            cells.append(current_cell)

    # loop on the cells
    output = []
    for cell in cells:
        # get all the points in this cell
        cell_points = cell.get_all_points()
        if len(cell_points) == 0:
            continue

        # then generalise the points based on the chosen mode
        match mode:
            case 'selection':
                if attribute is None:
                    raise Exception('Provide an attribute name in selection mode.')
                # retain the largest value in each cell for the chosen attribute of the point
                selected = None
                largest = 0
                for point, depth in cell_points:
                    value = point[attribute]
                    if value*depth > largest:
                        largest = value*depth
                        selected = point
                output.append((selected['geometry'], selected.index, len(cell_points)))

            case 'simplification':
                # the point retained in the cell is the closest to the center of the cell
                center = cell.envelope.centroid
                mindist = float("inf")
                nearest = None
                for point in cell_points:
                    dist = point[0]['geometry'].distance(center)
                    if dist < mindist:
                        mindist = dist
                        nearest = point
                output.append((nearest[0]['geometry'], nearest.index, len(cell_points)))

            case 'aggregation':
                # the points are all aggregated to the centroid of the points.
                geoms = []
                for point in cell_points:
                    geoms.append(point[0]['geometry'])
                multi = MultiPoint(geoms)
                centroid = multi.centroid
                output.append((centroid, -1, len(cell_points)))
    
    return output, qtree
