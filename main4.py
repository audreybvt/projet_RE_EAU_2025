# quatrième proposition -> intégration cas netcdf
#######################
#######################
# Import of the packages needed

import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
#from treatmentCSV import*
from statistics import*
import statistics_netCDF as stat_CDF
from visualization import*
import visualization_netCDF as visu_CDF

path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

# Determine if the file is a CSV or a NetCDF

suffix = path.suffix.lower()


#les print vont partir probablement et remplacer par un traitement pour mettre tout sous forme de df a priori

if suffix == ".csv": # CSV case
    
    print("It is a CSV")

    #Création des dictionnaires
    dict_visualization={"bar chart":1,"scatter plot":2,"line char":3, "radar chart":4, "histogram chart":5}
    menu_visu_CSV = {
        1: bar_chart,
        2: scatter_chart,
        3: line_chart,
        4: radar_chart,
        5: histogram_chart
    }

    dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5}
    menu_stats_CSV = {
        1: mean_value,
        2: maximum_value,
        3: minimum_value,
        4: percentile,
        5: nombre_ocurrences_au_dessus_seuil
    }
    
    df = pd.read_csv(path, sep=";")

    df[df.columns[0]]=pd.to_datetime(df[df.columns[0]], dayfirst=True)
    for col in df.select_dtypes(include="object"):
        df[col]=df[col].str.replace(",",".",regex=False).astype(float)


    #print(dict_stats)
    #stat_choice = int(input("Enter the number of the statistical operation you want: "))
    #df = menu_stats[stat_choice](df)  # retourne le dataframe modifié

    while True:
        print("\nMenu statistiques disponibles :")
        for name, num in dict_stats.items():
            print(f"[{num}] {name}")
        
        stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))
        if stat_choice == 0:
            break  # sortir de la boucle

        if stat_choice not in menu_stats_CSV:
            print("Choix invalide, réessayez.")
            continue

        # Appel de la fonction choisie
        df = menu_stats_CSV[stat_choice](df)

    print(dict_visualization)
    visualization = int(input("Enter the number of the visualization you want: "))

    os.makedirs("output", exist_ok=True)

    fig = menu_visu_CSV[visualization](df) 
    plt.savefig(f"output/{menu_visu_CSV[visualization].__name__}.png", bbox_inches="tight")
    plt.close(fig)

    print(f"{menu_visu_CSV[visualization].__name__}.png saved in output/")



elif suffix in (".nc", ".nc4", ".netcdf"): # netCDF case
    
    print("It is a NetCDF")

    #Création des dictionnaires
    dict_visualization={"bar chart":1,"scatter plot":2,"line char":3, "radar chart":4, "histogram chart":5}
    menu_visu_CDF = {
        1: visu_CDF.bar_chart,
        2: visu_CDF.scatter_chart,
        3: visu_CDF.line_chart,
        4: visu_CDF.radar_chart,
        5: visu_CDF.histogram_chart
    }

    dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5}
    menu_stats_CDF = {
        1: stat_CDF.mean_value,
        #2: stat_CDF.maximum_value,     #Fonction a écrir après
        #3: stat_CDF.minimum_value,
        #4: stat_CDF.percentile,
        #5: stat_CDF.nombre_ocurrences_au_dessus_seuil
    }

    ds = xr.open_dataset(path)

    #print(dict_stats)
    #stat_choice = int(input("Enter the number of the statistical operation you want: "))
    #df = menu_stats[stat_choice](df)  # retourne le dataframe modifié

    while True:
        print("\nMenu statistiques disponibles :")
        for name, num in dict_stats.items():
            print(f"[{num}] {name}")
        
        stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))
        if stat_choice == 0:
            break  # sortir de la boucle

        if stat_choice not in menu_stats_CDF:
            print("Choix invalide, réessayez.")
            continue

        # Appel de la fonction choisie
        ds = menu_stats_CDF[stat_choice](ds)

    print(dict_visualization)
    visualization = int(input("Enter the number of the visualization you want: "))

    os.makedirs("output", exist_ok=True)

    fig = menu_visu_CDF[visualization](ds)
    plt.savefig(f"output/{menu_visu_CDF[visualization].__name__}.png", bbox_inches="tight")
    plt.close(fig)

    print(f"{menu_visu_CDF[visualization].__name__}.png saved in output/")

else:
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")