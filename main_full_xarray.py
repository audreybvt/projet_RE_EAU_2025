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

#Determine file format
supported_file_format = {
        1: "NetCDF",
        2: "CSV"
    }

while True:
    
    print("\nSupported file formats:")
    for num, name in supported_file_format.items():
        print(f"[{num}] {name}")
    
    print("\nNote: Multiple files are supported only for NetCDF files.")

    file_format = int(input("\nSelect the format of your file: "))

    if file_format not in supported_file_format:
        print("Invalid choice, please try again")
        continue
    else:
        break


#Opening CSV file
if supported_file_format[file_format] == "CSV":
    
    path = input("Please enter your path to your file :")
    path = Path(path.strip().replace("\\", "/"))

    ds = dt_form.csv_to_xarray(path)

#Opening NetCDF file(s)
elif supported_file_format[file_format] == "NetCDF": # NetCDF case
    
    paths = input("Enter path(s) separated by commas : ").split(",")

    paths = [Path(p.strip().replace("\\", "/")) for p in paths]

    ds = dt_form.load_multiple_datasets(paths)


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

