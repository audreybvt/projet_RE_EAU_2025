#######################
#######################
# Import of the packages needed

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from treatmentCSV import*


# Ask for the path to the file we want to analyze
path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

# Determine if the file is a CSV or a NetCDF
'''
suffix = path.suffix.lower()

if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("it is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF")
    '''

# CSV case
df = pd.read_csv(path, sep = ";")
print(df.info())
# Which kind of visualization do you want?
# en fonction de la réponse demander les colonnes d'intéret :
# - date, - une ou deux variables autres, plusieurs variables en fonction du temps ?

# cas 1 date 1 variable
date = input("What is your date column name? mettre les spec de typo")
column1 = input("What is your column of interest ?")

#cas juste une variabel
column1 = input("What is your column of interest ?")

# cas 1 date 2 variables
date = input("What is your date column name? mettre les spec de typo")
column1 = input("What is your column 1 of interest ?")
column2 = input("What is your column 2 of interest ?")

# cas 2 variables
column1 = input("What is your column 1 of interest ?")
column2 = input("What is your column 2 of interest ?")