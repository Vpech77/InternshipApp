from static.py.point_generalisation import *
import psycopg2
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import Point
from configparser import ConfigParser

def load_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return config

def select_countryName():
    config  = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT pays.name AS countryName FROM world AS pays ORDER BY pays.name")
                res = cur.fetchall()
                return res
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
def select_puntos(name='France', category='known_mapdata'):
    config  = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT ST_AsGeoJson(villes.geom) as geometry, CAST((villes.pfas_sum) AS FLOAT)\
                            FROM {category} as villes JOIN world as pays ON ST_Within(villes.geom, pays.geom) \
                            WHERE pays.name ilike '{name}'")
                res = cur.fetchall()
                return res
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
def select_puntos_region(name='France', category='known_mapdata'):
    config  = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT ST_AsGeoJson(villes.geom) as geometry, CAST((villes.pfas_sum) AS FLOAT)\
                            FROM known_mapdata as villes,(SELECT region.geom FROM region, world \
                            WHERE ST_Intersects(region.geom, ST_MakeEnvelope(-0.47766304902998513, 44.8402913966969, 3.899131431403049, 47.97363600091214, 4326))\
                            AND (ST_Within(region.geom, world.geom) and world.name ilike 'France'))\
                            AS temp WHERE ST_Within(villes.geom, temp.geom)")
                res = cur.fetchall()
                return res
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
def sql_to_gdf(res):
    columns = ["geometry", "value"]
    geom = [json.loads(val[0]) for val in res]
    pt = [Point(dico['coordinates'][0], dico['coordinates'][1]) for dico in geom]
    df = pd.DataFrame(res, columns=columns)
    gdf = gpd.GeoDataFrame(df["value"], geometry=pt, crs="EPSG:4326")
    return gdf

def gdf_to_json(gdf):
    return json.loads(gdf.to_json())

def select_all_puntos(name='France'):
    category = ["known_mapdata", "presumptive_mapdata", "user_mapdata"]
    return {k:gdf_to_json(sql_to_gdf(select_puntos_region(name, k))) for k in category}

def get_crs(country):
    crs = 4326
    if country == "France":
        crs = 2154
    if country == "Spain":
        crs = 5634
    if country == "Portugal" or country == "Azores Islands":
        crs = 2188
    if country == "Iceland":
        crs = 9947
    if country == "Ireland" or country == "U.K. of Great Britain and Northern Ireland":
        crs = 2158
    return crs

def apply_algo(country, category, algoParams, algoName="LabelGrid"):
    puntos = select_puntos(country, category)
    gdf = sql_to_gdf(puntos)
    result = gdf

    if algoName == "LabelGrid":
        width = float(algoParams.get('width', 0.5))
        mode = algoParams.get('mode', 'aggregation')
        grid, result = point_label_grid(gdf, width, width, "hexagonal", mode)
    
    if algoName == "K-means":
        shrink_ratio = float(algoParams.get('shrink_ratio', 0.25))
        result = point_kmeans(gdf, shrink_ratio)
        pass
    
    if algoName == "Initial Point":
        pass
    
    if algoName == "Quadtree":
        typ = algoParams.get('type', 'selection')
        depth = int(algoParams.get('depth', 2))
        crs = get_crs(country)

        if typ == 'selection' and category == "known_mapdata":
            result = point_quadtree_selection(gdf, crs, depth)
        
        if typ == 'simplification':
            result = point_quadtree_simplification(gdf, crs, depth)
            
        if typ == 'aggregation':
            result = point_quadtree_aggregation(gdf, crs, depth)
            
    if algoName == "Delaunay":
        minlength = float(algoParams.get('minlength', 2.0))
        result = point_delaunay(gdf, minlength)

    if algoName == "Swing":
        arm = float(algoParams.get('arm', 8))
        result = point_swing(gdf, arm)

    # return gdf_to_json(result), gdf_to_json(grid)
    return gdf_to_json(result)