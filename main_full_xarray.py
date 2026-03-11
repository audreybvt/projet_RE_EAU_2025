# cinquième proposition -> full xarray
#######################
#######################
# Import of the packages needed

import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import statistics_xr as stat_xr
import visualization_xr as visu_xr
import data_formatting as dt_form
import indicators as indic
from pathlib import Path
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
dict_visu={"bar chart":1,"scatter plot":2,"line chart":3, "radar chart":4, "histogram chart":5}
menu_visu = {
    1: visu_xr.bar_chart,
    2: visu_xr.scatter_chart,
    3: visu_xr.line_chart,
    4: visu_xr.radar_chart,
    5: visu_xr.histogram_chart
}

dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5}
menu_stats = {
    1: stat_xr.mean_value_time,
    #2: stat_xr.maximum_value,     #Fonction à écrire après
    #3: stat_xr.minimum_value,
    #4: stat_xr.percentile,
    #5: stat_xr.nombre_ocurrences_au_dessus_seuil
}

# Indicator selection dictionaries
dict_indicateurs = {
    "IPS": 1,
    "Qmean": 2,
    "Q90/95": 3,
    "Q10/05": 4,
    "VCN10": 5,
    "VCX3": 6,
    "over_threshold":7
}

menu_indicateurs = {
    1: indic.IPS,
    2: indic.Qmean,
    3: indic.Q90_95,
    4: indic.Q10_05,
    5: indic.VCN10,
    6: indic.VCX3,
    7: indic.over_threshold
}

while True: 
# Demande des indicateurs
    while True:
        print("\nIndicateurs disponibles :")
        for name, num in dict_indicateurs.items():
            print(f"[{num}] {name}")
        
        # indicator_choice = int(input("Entrez le numéro de l'indicateur à calculer (0 pour terminer) : "))
        while True:
            try:
                indicator_choice = int(input("Entrez le numéro de l'indicateur à calculer (0 pour terminer) : "))
        
                if indicator_choice == 0:
                    break
            
                if indicator_choice not in menu_indicateurs:
                    print("Choix invalide, réessayez.")
                    continue
            
                break
        
            except ValueError:
                print("Veuillez entrer un nombre entier valide.")
        if indicator_choice == 0:
            break  # sortir de la boucle

        #if indicator_choice not in menu_indicateurs:
            #print("Choix invalide, réessayez.")
            #continue

        # Appel de la fonction choisie
        ds = menu_indicateurs[indicator_choice](ds)
        

    # Demande des statistiques
    while True:
        print("\nCalculs statistiques disponibles :")
        for name, num in dict_stats.items():
            print(f"[{num}] {name}")
        
        #stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))

        while True:
            try:
                stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))
        
                if stat_choice == 0:
                    break
            
                if stat_choice not in menu_stats:
                    print("Choix invalide, réessayez.")
                    continue
            
                break
        
            except ValueError:
                print("Veuillez entrer un nombre entier valide.")
        if stat_choice == 0:
            break  # sortir de la boucle

        #if stat_choice not in menu_stats:
            #print("Choix invalide, réessayez.")
            #continue

        # Appel de la fonction choisie
        ds = menu_stats[stat_choice](ds)

    # Demande de la visualisation
    print("\nVisualisations disponibles :")
    for name, num in dict_visu.items():
        print(f"[{num}] {name}")
    #visualization = int(input("Enter the index of the visualization you want: "))
    while True:
        try:
            visualization = int(input("Enter the index of the visualization you want: "))
        
            if visualization not in menu_visu:
                print("Choix invalide.")
                continue
            
            break
        
        except ValueError:
            print("Veuillez entrer un nombre entier valide.")

    makedirs("output", exist_ok=True)

    fig = menu_visu[visualization](ds)
    plt.savefig(f"output/{menu_visu[visualization].__name__}.png", bbox_inches="tight")
    print("Affichage de la figure, fermez la fenêtre pour continuer le script.")
    plt.show()
    plt.close(fig)

    print(f"{menu_visu[visualization].__name__}.png saved in output/")

    #choix de continuer
    continuer = input("\nVoulez-vous effectuer une autre analyse/visualisation sur ce fichier ? (o/n) : ").lower()
    if continuer != 'o':
        print("Fin du programme. Au revoir !")
        break