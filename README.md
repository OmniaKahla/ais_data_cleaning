# ais_data_cleaning
this repo contains scripts for data cleaning of the AIS data
I used conda version 22.9.0
To have the same conda environment, you can use the "spec-file_geo-env.txt". 
You can download the data from the Danish Maritim website in the below link. 
https://dma.dk/safety-at-sea/navigational-information/ais-data  --> Then click on the "Get Historical AIS Data" on the buttom of the page
Or use the following link directly http://web.ais.dk/aisdata/

To run the code:
1- Extract the downloaded AIS data file at the same path of the code folder.
2- Run the preprocessing.py by using the command "python preprocessing.py". The file depends on the "PreprocessingUtilities.py" that contains all helper functions.
  a- This would create a folder with the date of the file
  b- create MMSIList.csv that contains a list of valid MMSI. 
  c- create a "CleanedFiles" folder.
  d- The "CleanedFiles" folder contains a file for each vessel named with the MMSI.
  e- The data in each MMSI file are sorted, no duplicates-based on time, latitude, and longitude-, no invalid Latiude/longitude for instance no 91 for latitude or 181 for longitude, and added x,y coordinates that would be used in the next step. 
3- run the SpoofingDetection.py by using the command "python SpoofingDetection.py". The file would generate "ClassificationResults_date.csv" that contains the results of the spoofing detection. 
