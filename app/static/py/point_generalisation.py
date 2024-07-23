# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 11:18:59 2024

@author: vpech
"""
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import cartagen4py as c4
from static.py.algos import *

################################### LABEL GRID ################################

def point_label_grid(puntos, width, length, typ='square', mode='selection'):
    puntos.reset_index(drop=True, inplace=True)
    puntos = puntos[['geometry', 'value']]
    grid = createGrid(puntos, width, length, typ)
    lst_in_value = [puntos.loc[cell.contains(puntos['geometry']), 'value'] 
                    for cell in grid['geometry']]
    lst_inter_value = [puntos.loc[cell.touches(puntos['geometry']), 'value'] 
                       for cell in grid['geometry']]
    lst_all_value = [lst_inter_value[i] 
                     if lst_in_value[i].empty 
                     else pd.concat([lst_in_value[i],lst_inter_value[i]]) 
                     for i in range(len(lst_in_value))]
    
    if mode == 'selection':
        ind = [e.nlargest(1).index[0] for e in lst_all_value if not e.empty]
        p = [puntos['geometry'].iloc[i] for i in ind]
        point_results = gpd.GeoDataFrame(geometry=gpd.GeoSeries(p))
        
    if mode == 'aggregation':
        aggreg = [(geom, (width*len(cell))) for geom, cell in zip(grid.centroid, lst_all_value) if not cell.empty]
        df = pd.DataFrame(aggreg, columns=["geometry", "radius"])
        df['radius'] = [(40*rad)/max(df['radius']) for rad in df['radius']]
        
        point_results = gpd.GeoDataFrame(df['radius'], geometry=df["geometry"])
    return grid, point_results

################################### K-MEANS ################################

def point_kmeans(gdf, shrink_ratio=0.1):
    lst_pt = [Point(pt.x, pt.y) for pt in gdf['geometry']]
    simplified = c4.kmeans_point_set_reduction(lst_pt, shrink_ratio, True)
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(simplified))
    
################################### QUADTREE SELECTION ################################

def point_quadtree_selection(gdf, epsg, depth=2):
    output, qtree = c4.quadtree_point_set_reduction(gdf.to_crs(epsg), depth, 'selection', attribute='value')
    p = [pt[0] for pt in output]
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(p), crs=epsg).to_crs(4326)

################################### QUADTREE SIMPLIFICATION ################################

def point_quadtree_simplification(gdf, epsg, depth=2):
    output, qtree = c4.quadtree_point_set_reduction(gdf.to_crs(epsg), depth, 'simplification')
    p = [pt[0] for pt in output]
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(p), crs=epsg).to_crs(4326)

################################### QUADTREE AGGREGATION ################################

def point_quadtree_aggregation(gdf, epsg, depth=2):
    output, qtree = c4.quadtree_point_set_reduction(gdf.to_crs(epsg), depth, 'aggregation')
    p = [pt[0] for pt in output]
    radius = [pt[2] for pt in output]
    pix = [(40*rad)/max(radius) for rad in radius]
    df = pd.DataFrame(pix, columns=['radius'])
    return gpd.GeoDataFrame(df['radius'], geometry=gpd.GeoSeries(p), crs=epsg).to_crs(4326)

################################### DELAUNAY ################################

def point_delaunay(gdf, minlength=2.0):
    points = [Point(pt.x, pt.y) for pt in gdf['geometry']]
    hull = delaunay_concave_hull(points, minlength)
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(hull))

################################### SWING ################################

def point_swing(gdf, arm=8):
    poly = swing(gdf, arm)
    if poly:
        print("polys")
    else:
        print("no poly")
    return gpd.GeoDataFrame(geometry=gpd.GeoSeries(poly))
        