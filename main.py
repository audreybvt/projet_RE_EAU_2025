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

suffix = path.suffix.lower()

if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("It is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")
    

# CSV case
df = pd.read_csv(path, sep = ";")
print(df.info())

number_of_variables = float(input("How many variables do you want to compare?” Enter the number:")) 

date = input("What is the name of the column with the dates? Copy and paste its name:") 

df[date] = pd.to_datetime(df[date], dayfirst=True) 

if number_of_variables == 1: 
    column1= input("What is the name of the column of interest? Copy and paste its name here (without quotation marks):") 
    df[column1] = ( 

        df[column1] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    statistic1 = float(input("Which statistic do you want to compute and display? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    visualization1 = float(input("Which kind of visualization do you want? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 

if number_of_variables == 2: 
    column2.1= input("What is the name of the first column of interest? Copy and paste its name here (without quotation marks):") 
    df[column2.1] = ( 

        df[column2.1] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    column2.2= input("What is the name of the third column of interest? Copy and paste its name here (without quotation marks):") 
    df[column2.2] = ( 

        df[column2.2] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    statistic2.1= float(input("Which statistic do you want to compute and display for the first column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    statistic2.2= float(input("Which statistic do you want to compute and display for the second column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    visualization2 = float(input("Which kind of visualization do you want? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 

if number_of_variables == 3: 
    column3.1= float(input("Which statistic do you want to compute and display for the first column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    df[column3.1] = ( 

        df[column3.1] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    column3.2= float(input("Which statistic do you want to compute and display for the second column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    df[column3.2] = ( 

        df[column3.2] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    column3.3= float(input("Which statistic do you want to compute and display for the third column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    df[column3.3] = ( 

        df[column3.3] 

        .str.replace(",",".", regex=False) 

        .astype(float) 

    ) 
    statistic3.1 = float(input("Which statistic do you want to compute and display for the first column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    statistic3.2 = float(input("Which statistic do you want to compute and display for the second column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    statistic3.3 = float(input("Which statistic do you want to compute and display for the third column? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 
    visualization3 = float(input("Which kind of visualization do you want? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ...")) 

 

 

 

 

'''
visualisation = float(input("Which kind of visualization do you want? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ..."))
# Which kind of visualization do you want?
# en fonction de la réponse demander les colonnes d'intéret :
# - date, - une ou deux variables autres, plusieurs variables en fonction du temps ?

### ATTENTIN PBM D'INDENTATION

# cas 1 date 1 variable
if visualisation == 1 or visualisation == 2 :
    date = input("What is your date column name? mettre les spec de typo")
    column1 = input("What is your column of interest ?")
    df[date] = pd.to_datetime(df[date], dayfirst=True)
    df[column1] = (
        df[column1]
        .str.replace(",",".", regex=False)
        .astype(float)
    )

#cas juste une variable
elif visualisation == 3 :
    column1 = input("What is your column of interest ?")
    statistic = float(input("Which statistic do you want to compute and display? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ..." ))
    df[column1] = (
        df[column1]
        .str.replace(",",".", regex=False)
        .astype(float)
    )

# cas 1 date 2 variables
elif visualisation == 4 or visualisation == 5 : :
    date = input("What is your date column name? mettre les spec de typo")
    column1 = input("What is your column 1 of interest ?")
    column2 = input("What is your column 2 of interest ?")
    df[date] = pd.to_datetime(df[date], dayfirst=True)
    df[column1] = (
        df[column1]
        .str.replace(",",".", regex=False)
        .astype(float)
    )
    df[column2] = (
        df[column2]
        .str.replace(",",".", regex=False)
        .astype(float)
    )

# cas 2 variables
elif visualisation == 6 :
    column1 = input("What is your column 1 of interest ?")
    column2 = input("What is your column 2 of interest ?")
    statistic_column1 = float(input("Which statistic do you want to compute on your column 1 and display? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ..." ))
    statistic_column2 = float(input("Which statistic do you want to compute on your column 2 and display? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ..." ))
    df[column1] = (
        df[column1]
        .str.replace(",",".", regex=False)
        .astype(float)
    )
    df[column2] = (
        df[column2]
        .str.replace(",",".", regex=False)
        .astype(float)
    )

########

#on convertit les colonnes dans le bon type si ce sont des objets
#il faudra voir comment on gère les types de colonnes
#mettre un test du type ?

# Gérer le problème demande d'une courbe temporelle/demande d'une moyenne 
statistic = float(input("Which statistic do you want to compute and display? Here are the possible choices, type the number corresponding to your choice: 1 2 3 ..." ))

'''
