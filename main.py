
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
from indicators import*

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

dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "nombre d'occurences au dessus d'un seuil":5, "moyenne multimodele":6, "moyenne glissante":7}
menu_stats = {
    1: mean_value,
    2: maximum_value,
    3: minimum_value,
    4: percentile,
    5: nombre_ocurrences_au_dessus_seuil,
    6: moyenne_multimodele,
    7: rolling_mean_value
}

dict_indicateurs={"IPS":1, 
                  "Qmoy":2,
                  "Q90 & Q95":3}
menu_indicateurs = {
    1: IPS,
    2: Qmoy,
    3: Q90_95
}



#les print vont partir probablement et remplacer par un traitement pour mettre tout sous forme de df a priori
if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("It is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF: type not supported yet by this code.")
    

# CSV case
# prévisualisation
print("\nAperçu des 5 premières lignes du fichier brut :")
with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
    for i in range(5):
        line = f.readline()
        clean_line = line.replace(";;", ";").strip(";")
        print(f"Ligne {i} | {clean_line[:100]}...")
print("____________________")

# On demande à l'utilisateur combien de lignes de métadonnées il souhaite ignorer
skip_n = int(input("Combien de lignes de métadonnées (en-têtes sans compter le nom des colonnes) y a t'il? "))
df = pd.read_csv(path, sep=";", skiprows=skip_n)
# Nettoyage = supprimer les colonnes ou lignes entièrement vides (pas de dates, pas de noms ...)
df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)


df[df.columns[0]]=pd.to_datetime(df[df.columns[0]], dayfirst=True) # On suppose que la première colonne est celle des dates
for col in df.select_dtypes(include="object"):
    df[col]=df[col].str.replace(",",".",regex=False).astype(float)
    

print(df.info()) # Afficher à l'utilisateur les noms des colonnes que comporte son fichier

while True: 
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
    print("\nVisualisations disponibles :")
    for name, num in dict_visualization.items():
        print(f"[{num}] {name}")
    visualization = int(input("Enter the index of the visualization you want: "))

    os.makedirs("output", exist_ok=True)

    fig = menu[visualization](df) 
    plt.savefig(f"output/{menu[visualization].__name__}.png", bbox_inches="tight")
    print("Affichage de la figure, fermez la fenêtre pour continuer le script.")
    plt.show()
    plt.close(fig)

    print(f"{menu[visualization].__name__}.png saved in output/")

    #choix de continuer
    continuer = input("\nVoulez-vous effectuer une autre analyse/visualisation sur ce fichier ? (o/n) : ").lower()
    if continuer != 'o':
        print("Fin du programme. Au revoir !")
        break

