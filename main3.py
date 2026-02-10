
# troisième proposition
#######################
#######################
# Import of the packages needed

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from treatmentCSV import*
from statistics import*
from visualization import*

path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

# Determine if the file is a CSV or a NetCDF

suffix = path.suffix.lower()

#Création des dictionnaires
dict_visualization={"bar chart":1,"scatter plot":2,"line char":3, "radar chart":4, "histogram chart":5}
menu = {
    1: bar_chart,
    2: scatter_chart,
    3: line_chart,
    4: radar_chart,
    5: histogram_chart
}

dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5, "moyenne multimodele":6}
menu_stats = {
    1: mean_value,
    2: maximum_value,
    3: minimum_value,
    4: percentile,
    5: nombre_ocurrences_au_dessus_seuil,
    6: moyenne_multimodele
}

dict_indicateurs={"IPS":1}
menu_indicateurs = {
    1: IPS
}



#les print vont partir probablement et remplacer par un traitement pour mettre tout sous forme de df a priori
if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("It is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")
    

# CSV case
df = pd.read_csv(path, sep=";")

df[df.columns[0]]=pd.to_datetime(df[df.columns[0]], dayfirst=True) # On suppose que la première colonne est celle des dates
for col in df.select_dtypes(include="object"):
    df[col]=df[col].str.replace(",",".",regex=False).astype(float)
    

print(df.info()) # Afficher à l'utilisateur les noms des colonnes que comporte son fichier


# Demande des indicateurs
while True:
    print("\nIndicateurs disponibles :")
    for name, num in dict_indicateurs.items():
        print(f"[{num}] {name}")
    
    indicator_choice = int(input("Entrez le numéro de l'indicateur à calculer (0 pour terminer) : "))
    if indicator_choice == 0:
        break  # sortir de la boucle

    if indicator_choice not in menu_indicateurs:
        print("Choix invalide, réessayez.")
        continue

    # Appel de la fonction choisie
    df = menu_indicateurs[indicator_choice](df)
    

# Demande des statistiques
while True:
    print("\nCalculs statistiques disponibles :")
    for name, num in dict_stats.items():
        print(f"[{num}] {name}")
    
    stat_choice = int(input("Entrez le numéro de la stat à appliquer (0 pour terminer) : "))
    if stat_choice == 0:
        break  # sortir de la boucle

    if stat_choice not in menu_stats:
        print("Choix invalide, réessayez.")
        continue

    # Appel de la fonction choisie
    df = menu_stats[stat_choice](df)

# Demande de la visualisation
print(dict_visualization)
visualization = int(input("Enter the number of the visualization you want: "))

os.makedirs("output", exist_ok=True)

fig = menu[visualization](df) 
plt.savefig(f"output/{menu[visualization].__name__}.png", bbox_inches="tight")
plt.close(fig)

print(f"{menu[visualization].__name__}.png saved in output/")
