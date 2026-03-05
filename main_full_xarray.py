# cinquième proposition -> full xarray
#######################
#######################
# Import of the packages needed

import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
import statistics_xr as stat_xr
import visualization_xr as visu_xr
import data_formatting as dt_form
from os import makedirs

path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

# Determine if the file is a CSV or a NetCDF

suffix = path.suffix.lower()

if suffix == ".csv": # CSV case
    
    print("It is a CSV")
    ds = dt_form.csv_to_xarray(path)
    
elif suffix in (".nc", ".nc4", ".netcdf"): # netCDF case
    
    print("It is a NetCDF")
    ds = xr.open_dataset(path)

elif suffix not in (".csv", ".nc", ".nc4", ".netcdf"):
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")


#Création des dictionnaires
dict_visualization={"bar chart":1,"scatter plot":2,"line chart":3, "radar chart":4, "histogram chart":5}
menu_visu_xr = {
    1: visu_xr.bar_chart,
    2: visu_xr.scatter_chart,
    3: visu_xr.line_chart,
    4: visu_xr.radar_chart,
    5: visu_xr.histogram_chart
}

dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5}
menu_stats_xr = {
    1: stat_xr.mean_value,
    #2: stat_xr.maximum_value,     #Fonction à écrire après
    #3: stat_xr.minimum_value,
    #4: stat_xr.percentile,
    #5: stat_xr.nombre_ocurrences_au_dessus_seuil
}

while True:
    print("\nMenu statistiques disponibles :")
    for name, num in dict_stats.items():
        print(f"[{num}] {name}")
    
    stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))
    if stat_choice == 0:
        break  # sortir de la boucle

    if stat_choice not in menu_stats_xr:
        print("Choix invalide, réessayez.")
        continue

    # Appel de la fonction choisie
    ds = menu_stats_xr[stat_choice](ds)

print(dict_visualization)
visualization = int(input("Enter the number of the visualization you want: "))

makedirs("output", exist_ok=True)

fig = menu_visu_xr[visualization](ds)
plt.show()
plt.savefig(f"output/{menu_visu_xr[visualization].__name__}.png", bbox_inches="tight")
plt.close(fig)

print(f"{menu_visu_xr[visualization].__name__}.png saved in output/")

