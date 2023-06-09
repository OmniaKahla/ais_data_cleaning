""" 
author: "Omnia Kahla"
date: 2021-09-02
version: 1.0
input: AIS data
output: Spoofing detection
command: python SpoofingDetection.py
this code is provided without any warranty or responsibilty
the author is not responsible for any damage caused by using this code
"""
import math
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn import preprocessing
from shapely.geometry import Point
from shapely import wkt
import os

def load_data (file_path):
    """
    this function loads the data from a csv file
    it takes as input the file path
    it returns the dataframe
    :param file_path: file path
    :return: dataframe
    """
    df = pd.read_csv(file_path)
    return df

def get_cluster_insights(df_original, n_neighbors,mmsi):
    """
    this function detects the clusters and returns whether the trajectory has location spoofing or identity spoofing or both or none
    it takes as input the dataframe, the number of neighbors and the mmsi
    it returns the insights
    :param df_original: dataframe
    :param n_neighbors: number of neighbors
    :param mmsi: mmsi
    :return: has problem ,has location spoofing,has identity spoofing, # of clusters
    """
    df=df_original[["x","y"]]
    if len(df)==0:
        return False, False, False,-1
    nbrs = NearestNeighbors(n_neighbors=n_neighbors).fit(df)
    try:
        neigh_dist, neigh_ind = nbrs.kneighbors(df)
    except ValueError:
        return False, False, False,-1
    sort_neigh_dist = np.sort(neigh_dist, axis=0)
    eps=find_eps(sort_neigh_dist, n_neighbors-1)
    #print("eps",eps)
    if eps==0.0:# anchored vessel for the whole day or base station
        return False, False, False, -1
    min_samples= 5 # an arbitrary value based on my experiments
    clusters = DBSCAN(eps=eps, min_samples=min_samples).fit(df)
    unique_clusters=set(clusters.labels_)
    clusters_labels=list(clusters.labels_)
    se = pd.Series(clusters_labels)
    df_original['cluster_label'] = se.values
    grouped = df_original.groupby('cluster_label') # To avoid the warning message remove the list
    df_groups=pd.DataFrame(columns=["cluster","length"])
    df_groups.set_index('cluster')
    for name, group in grouped:
        df_temporary=group
        df_temporary.sort_values(by=['# Timestamp'])
        #print(name)
        df_groups.loc[str(name)]={"cluster": name, "length": len(group)}
        #print(df_groups.loc[str(name)]["length"])
        #ind+=1
        # if name==-1:
        #     df_temporary.to_csv(path_or_buf=f"{date}/clusters/{mmsi}_outlier.csv", sep=',', header=True, index=False, index_label=None, mode='w', encoding=None)    
        # else: 
        df_temporary.to_csv(path_or_buf=f"{date}/clusters/{mmsi}_trajectoryID_{name}.csv", sep=',', header=True, index=False, index_label=None, mode='w', encoding=None)
    hasLocationSpoofing=False
    hasIdentitySpoofing=False
    has_problem=False
    df_temp=pd.DataFrame(columns=["cluster_label","# Timestamp", "x", "y"])
    count_ofJumps=0
    calculatedSpeed=0
    num_of_points_speed_exceeds_1000=0
    count_of_outliers=0
    df_outliers = df_original.iloc[:0,:].copy()
    if len(unique_clusters)<=1: # only single trajectory
        return False, False, False, len(unique_clusters)
    current_Label=clusters_labels[0]
    outlier_cluster_name=-2 
    outlier_clusters=set()# creating a set of all outliers clusters
    for i in range (1, len(clusters_labels)):#adds the 2 consective points that are in different clusters
        if current_Label != clusters_labels[i]:
            current_Label=clusters_labels[i]
            rec_in_cluster=df_original.iloc[i]
            second_point = {'cluster_label': clusters_labels[i],'# Timestamp':rec_in_cluster["# Timestamp"], 'x': rec_in_cluster["x"],'y':rec_in_cluster["y"]} 
            rec_in_cluster=df_original.iloc[i-1]
            first_point = {'cluster_label': clusters_labels[i-1],'# Timestamp':rec_in_cluster["# Timestamp"], 'x': rec_in_cluster["x"],'y':rec_in_cluster["y"]} 
            calculatedSpeed=calculate_speed_between_points(first_point,second_point)
            if calculatedSpeed >1000:
                #print(calculatedSpeed)
                #outlier_point_index= compare_points(first_point,second_point,i)
                num_of_points_speed_exceeds_1000+=1
                #if outlier_point_index==-1: # both points are not detected as outliers from DBSCAN, so the point which its cluster density is the smallest is an outlier
                outlier_point_index, outlier_cluster_name=compare_cluster_density_return_outlier_index(first_point["cluster_label"], second_point["cluster_label"], i, df_groups)
                outlier_clusters.add(str(outlier_cluster_name))
                count_of_outliers+=1
                df_outliers.loc[count_of_outliers]=df_original.iloc[outlier_point_index]
                
                # df_temp.loc[count_ofJumps]= first_point
                # df_temp.loc[count_ofJumps+1] = second_point
                # count_ofJumps+=2
    df_temp["# Timestamp"] = pd.to_datetime(df_temp["# Timestamp"])
    #print(outlier_clusters)
    #print(len(df_outliers))
    if len(df_outliers)!=0:
        df_outliers.drop_duplicates(subset=['# Timestamp', 'Latitude', 'Longitude'], keep='last', inplace=True)
        df_outliers.to_csv(path_or_buf=f"{date}/clusters/{mmsi}_outlier.csv", sep=',', header=True, index=False, index_label=None, mode='w', encoding=None)    
    desityOfHops=count_ofJumps/len(df)
    density_of_points_speed_exceeds_1000 = num_of_points_speed_exceeds_1000/len(df)
    if  desityOfHops>0.1 and density_of_points_speed_exceeds_1000>0.1 :
        has_problem=True
        for name, group in grouped:
            df_temporary=group
            df_temporary.sort_values(by=['# Timestamp'])
            hasLocationSpoofing= calculated_speed_between_points_in_cluster(df_temporary)
        if hasLocationSpoofing==False:
            hasIdentitySpoofing=True
    elif density_of_points_speed_exceeds_1000 < 0.1 and density_of_points_speed_exceeds_1000>0:
        has_problem=True
        hasLocationSpoofing=True
    return has_problem,hasLocationSpoofing,hasIdentitySpoofing, len(unique_clusters)

# def compare_points(first_point,second_point, index):
#     if first_point["cluster_label"] == -1:
#         print("first point" , first_point)
#         return index-1
#     elif second_point["cluster_label"] ==-1:
#         print("second point", second_point)
#         return index
#     return -1

def compare_cluster_density_return_outlier_index(cluster1, cluster2, index, df_groups):
   # print(df_groups.loc[str(cluster1)]["length"], df_groups.loc[str(cluster2)]["length"])
    if df_groups.loc[str(cluster1)]["length"] > df_groups.loc[str(cluster2)]["length"] :
       # print (cluster2 ," cluster 2 has ", df_groups.loc[str(cluster2)]["length"] ,"# of points and is the smallest")
        return index, cluster2
    else:
       # print (cluster1, " cluster 1 has ", df_groups.loc[str(cluster1)]["length"] ,"# of points and is the smallest")
        return index-1, cluster1

def calculate_speed_between_points(point1, point2):
    """
    this function calculates the speed between 2 points
    it takes as input the 2 points
    it returns the speed
    :param point1: point1
    :param point2: point2
    :return: speed
    """
    calculatedSpeed=0
    calculated_Distance = math.sqrt(math.pow(
            (point1["x"]-point2["x"]), 2) + math.pow((point1["y"]-point2["y"]), 2))
    
    time_diff = abs(pd.to_datetime(point2["# Timestamp"])-pd.to_datetime(point1["# Timestamp"]))
    if time_diff.total_seconds() == 0:  # division over zero exception
        calculatedSpeed=0
    else:
        calculatedSpeed = calculated_Distance / time_diff.total_seconds()
    return calculatedSpeed

def calculated_speed_between_points_in_cluster(df_temp):
    """
    this function calculates speed between points in a Cluster
    it takes as input the dataframe that contains the points where the cluster changes
    it returns whether it has location spoofing or identity spoofing 
    :param df_temp: dataframe
    :return: hasLocationSpoofing,hasIdentitySpoofing
    """
    hasLocationSpoofing=False
    #hasIdentitySpoofing=False
    for i in range(1,len(df_temp)):
        calculatedSpeed=calculate_speed_between_points(df_temp.iloc[i-1],df_temp.iloc[i])
        if calculatedSpeed>1000:
            hasLocationSpoofing=True
            break
        #     continue
        # else:
        #     hasIdentitySpoofing=True
        #     continue
    return hasLocationSpoofing#,hasIdentitySpoofing

def find_eps(sort_neigh_dist, leng):
    """
    this function finds the eps
    it takes as input the sorted neighbor distances and the length
    it returns the eps
    :param sort_neigh_dist: sorted neighbor distances
    :param leng: length
    :return: eps
    """
    k_dist = sort_neigh_dist[:, leng]
    i= 0
    while i<len(k_dist)-1:
        diff=k_dist[i+1]-k_dist[i]
        if (diff > 700):
           break
        i+=1  
    return k_dist[i]


if __name__=="__main__": 
    date = "2022-09-02" #"2023-04-11"
    mmsi_file = f"%s/MMSIList.csv" % date
    df_mmsi = load_data(mmsi_file)
    df_mmsi.columns=["MMSI"]
    df_mmsi.drop(df_mmsi[(df_mmsi.MMSI == 0)].index, inplace = True)
    mmsi_set = set(df_mmsi["MMSI"].tolist())
    outdf=pd.DataFrame(columns=["MMSI","hasProblem","hasLocationSpoofing","hasIdentitySpoofing", "CountOfClusters"])
    count=0
    if not os.path.exists(date+"/clusters"):
        os.mkdir(date+"/clusters")
    count_has_problem=0
    count_has_identity_spoofing=0
    count_has_location_spoofing=0
    for mmsi in mmsi_set:
        #mmsi = "211547270" # "219015373" # 622
        #mmsi=219028670
        #mmsi=219021388
        print("mmsi is =", mmsi)
        file_path = f"{date}/CleanedFiles/{mmsi}.csv"
        df_temp = load_data(file_path)
        hasProblem,hasLocationSpoofing,hasIdentitySpoofing, numberOfClusters=get_cluster_insights(df_temp, 5,mmsi)
        if hasIdentitySpoofing or hasLocationSpoofing:
            print(f"hasProblem = {hasProblem}, hasLocationSpoofing={hasLocationSpoofing},hasIdentitySpoofing={hasIdentitySpoofing} ")
        new_row = {'MMSI':mmsi, 'hasProblem': hasProblem,'hasLocationSpoofing':hasLocationSpoofing,
        'hasIdentitySpoofing':hasIdentitySpoofing, 'CountOfClusters': numberOfClusters}  
        outdf.loc[count] = new_row
        if hasProblem:
            count_has_problem+=1
        if hasIdentitySpoofing:
            count_has_identity_spoofing+=1
        if hasLocationSpoofing:
            count_has_location_spoofing+=1
        count+=1
        #break
    print(f"count_has_problem = {count_has_problem}, count_has_identity_spoofing={count_has_identity_spoofing},count_has_location_spoofing={count_has_location_spoofing} ")
    outdf.to_csv(path_or_buf=f"{date}/ClassificationResults_{date}.csv", sep=',', header=True, index=False, index_label=None, mode='w', encoding=None)