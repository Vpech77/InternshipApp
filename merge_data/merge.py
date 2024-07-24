# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 10:17:40 2024

@author: user
"""
import geopandas as gpd
import pandas as pd
import os

def merge_files(folder):
    fichiers = os.listdir(input_folder)
    
    lst_gdf = []
    
    for fichier in fichiers:
        input_path = os.path.join(input_folder, fichier)
        gdf = gpd.read_file(input_path)
        lst_gdf.append(gdf)
    
    merge = pd.concat(lst_gdf)
    merge.to_file("./zoom2.geojson")
    return merge

if __name__ == "__main__":

    input_folder = './data'
    res = merge_files(input_folder)
    res.plot()
    print("DONE !")