
"""
This script is used to clean the data before processing DBSCAN
author: Omnia Kahla
date: 2021-09-02
version: 1.0
input: AIS data
output: Cleaned data
command: python preprocessing.py
this code is provided without any warranty or responsibilty
the author is not responsible for any damage caused by using this code
"""
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os
import PreprocessingUtilities as pre

if __name__=="__main__":
    date= "2023-04-11" #"2022-12-24"#"2022-09-02"
    outputfolder="SplitFileByMMSISortedByTime/"+date+"/"
    data_file= f"../../AISData/aisdk-%s.csv"%date

    df=pre.change_timestamp_format(date, outputfolder, data_file)
    print("Load completed!")
    #print(df.columns)
    mmsi_set = pre.generate_mmsi_file(outputfolder, df)
    print("Done saving MMSI List to file")
    #mmsi = "211547270"
    if not os.path.exists(outputfolder+'CleanedFiles/'):
            os.mkdir(outputfolder+'CleanedFiles/')
    for mmsi in mmsi_set:
        print(mmsi)
        df_temp = pre.sort_by_timestamp(df, mmsi)
        print('data sorted based on time')   
        pre.remove_unvalid_Lat_Long_duplicates(df_temp)
        print("Removing duplicates and out of extent completed! ")
        print("start converting Lat/Long")
        # df_temp["geometry"]= df_temp.apply(lambda row: Point(row.Longitude, row.Latitude), axis=1)
        geodf = pre.extend_with_cartesian_coordinates(df_temp)
        geodf.to_csv(path_or_buf=outputfolder+'CleanedFiles/'+str(mmsi)+".csv", index = False, mode='w', header=True, sep=',', index_label=None, encoding=None)
        print("Done saving to file")
    