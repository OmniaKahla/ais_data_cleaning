""""
this file contains utility functions used in the preprocessing phase
author: Omnia Kahla
date: 2021-09-02
this code is provided without any warranty or responsibilty
the author is not responsible for any damage caused by using this code
"""
import pandas as pd
import geopandas as gpd
import os
import re
from datetime import datetime

def sort_by_timestamp(df, mmsi):
    """
    this function sorts the dataframe by timestamp
    it takes as input the dataframe and the mmsi
    it returns the sorted dataframe
    :param df: dataframe
    :param mmsi: mmsi
    :return: sorted dataframe
    """
    df_temp = df.query("MMSI==%s"%mmsi)
    df_temp=df_temp.sort_values(by=['# Timestamp'])
    return df_temp

def generate_mmsi_file(dateFolder, df):
    """
    this function generates a file that contains the list of mmsi
    it takes as input the output folder and the dataframe
    it stores the output file in the output folder
    it removes the invalid mmsi such as 123456789, 111111111, 222222222, 333333333, 444444444, 555555555, 666666666, 777777777, 888888888, 999999999, 000000000
    in addition, it removes numbers that are not 9 digits, and decimal numbers
    it returns the list of mmsi
    :param dateFolder: the day of the data being downloaded and is used as the output folder for instance 2023-04-11
    :param df: dataframe
    :return: list of mmsi
    """
    mmsi_set = set(df["MMSI"].tolist())
    df_mmsi = pd.DataFrame(mmsi_set)
    df_mmsi.columns=["MMSI"]
    invalid_MMSI = [123456789,111111111,222222222,333333333,444444444,555555555,666666666,777777777,888888888,999999999,000000000,0]
    # filter out rows that contain specific numbers
    df_mmsi = df_mmsi[~df_mmsi.isin(invalid_MMSI)].dropna(how='all')
    # convert the values to int
    df_mmsi = df_mmsi.astype(int)
    df_mmsi = df_mmsi[df_mmsi.astype(str).apply(lambda x: x.str.len()).eq(9).all(1)]
    df_mmsi.to_csv(dateFolder+"/MMSIList.csv", index = False, mode='w', header=True, sep=',', index_label=None, encoding=None)
    return mmsi_set

def remove_unvalid_Lat_Long_duplicates(df_temp):
    """
    this function removes the rows with unvalid Lat/Long and the duplicates
    it takes as input the dataframe
    it changes inplace the input dataframe
    :param df_temp: dataframe
    """
    df_temp.drop(df_temp[(df_temp['Latitude'] > 90 ) | (df_temp['Latitude']<-90)].index, inplace = True)
    df_temp.drop(df_temp[(df_temp['Longitude'] > 180) | (df_temp['Longitude']<-180)].index, inplace = True)
    #df_temp.drop_duplicates(inplace = True)
    df_temp.drop_duplicates(subset=['# Timestamp', 'Latitude', 'Longitude'], keep='last', inplace=True)

def extend_with_cartesian_coordinates(df_temp):
    """
    this function converts the Lat/Long to x, y coordinates
    it takes as input the dataframe
    it returns the dataframe with the new columns
    :param df_temp: dataframe
    :return: dataframe with new columns
    """
    geodf = gpd.GeoDataFrame(df_temp, geometry=gpd.points_from_xy(df_temp.Longitude, df_temp.Latitude) )
    print("added geometry col")
        # geodf = gpd.GeoDataFrame(df_temp, crs=4326)
    geodf =geodf.set_crs(4326)
    print("defined the original coordinates for the geometry col")
    geodf = geodf.to_crs(25832) #25832 is recomended by the Danish Maritim System instead of 3857
    print("convert coordinates to x, y")
    geodf["x"] = geodf.geometry.apply(lambda row:row.x)
    geodf["y"] = geodf.geometry.apply(lambda row:row.y)
    print("added x, y columns to the geodf")
    print("Done converting Lat/Long, save now to a file")
    return geodf

def change_timestamp_format(dateFolder, data_file):
    """
    this function updates timestamp datetime format
    it takes as input the date of the file, the output folder and the input file
    it stores the output file in the output folder
    it returns df 
    :param date: date of the file
    :param outputfolder: output folder
    :param data_file: input file
    :return: df
    """
    print("change timestamp format")
    df = pd.read_csv(data_file)
    print("step 0")
    df["# Timestamp"] =  pd.to_datetime(df["# Timestamp"], format='%d/%m/%Y %H:%M:%S')
    print("step 1")
    if not os.path.exists(dateFolder):
        os.mkdir(dateFolder)
    df.to_csv(dateFolder+'/aisdk-%s_updated.csv'%dateFolder, sep=',',index=False,index_label=False, encoding='utf-8')
    return df
    
