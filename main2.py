# Deuxième proposition
#######################
#######################
# Import of the packages needed

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from treatmentCSV import*
from statistics import*

path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

# Determine if the file is a CSV or a NetCDF

suffix = path.suffix.lower()

dict_visualization_num_variables={1:[1,"date"],2:[2]}
dict_visualization={"temporel":1,"histogramme":2}

if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("It is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")
    

# CSV case
df = pd.read_csv(path, sep=";")

print(dict_visualization)
visualization = int(input("Enter the number of the visualization you want: "))

print(df.info())

print("Avec votre choix de visualisation, vous allez travailler sur", dict_visualization_num_variables[visualization], "colonnes.")
colonnes_a_etudier = [0] * dict_visualization_num_variables[visualization][0]
for i in range (dict_visualization_num_variables[visualization][0]):
    print("i=",i+1)
    colonnes_a_etudier[i]=int(input("Entrez le numero de la ie colonne à étudier : "))



if len(dict_visualization_num_variables[visualization]) > 1:
    index_date = int(input("Entrez l'index de votre colonne de date : "))
    
    df.iloc[:, index_date] = pd.to_datetime(
        df.iloc[:, index_date],
        dayfirst=True
    )
    
    colonnes_a_etudier = [index_date] + colonnes_a_etudier

print(colonnes_a_etudier)