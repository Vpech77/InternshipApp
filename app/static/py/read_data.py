# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 13:34:24 2024

@author: vpech
"""
import matplotlib.pyplot as plt
import geopandas as gpd
import time


if __name__ == "__main__":
    start = time.perf_counter()
    
    # known = gpd.read_file('../be_data/known_be.shp')
    # user = gpd.read_file('../be_data/user_be.shp')
    # presumptive = gpd.read_file('../be_data/presumptive_be.shp')
    
    known = gpd.read_file('../map_data/Known_mapdata.shp')
    user = gpd.read_file('../map_data/User_mapdata.shp')
    presumptive = gpd.read_file('../map_data/Presumptive_mapdata.shp')
    
    # known.to_file("./known_all.geojson")
    # user.to_file("./user_all.geojson")
    # presumptive.to_file("./presumptive_all.geojson")
    
    end = time.perf_counter()
    duration = end - start
    print("Time: ", duration)

    # fig, ax1 = plt.subplots()
    # plt.suptitle('KNOWN')
    # known.plot(ax=ax1, color='firebrick')
    
    # fig, ax1 = plt.subplots()
    # plt.suptitle('USER')
    # user.plot(ax=ax1, color='purple')
    
    # fig, ax1 = plt.subplots()
    # plt.suptitle('PRESUMPTIVE')
    # presumptive.plot(ax=ax1, color='dodgerblue')
    

    