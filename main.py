
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
import os

# path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark):"))

while True:
    try:
        path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation mark): "))
        
        if not path.exists():
            print("Le fichier n'existe pas. Réessayez.")
            continue
            
        if not path.is_file():
            print("Ce n'est pas un fichier valide.")
            continue

        break
        
    except Exception as e:
        print(f"Erreur : {e}")

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

dict_stats={"mean":1,"max":2,"min":3, "percentile":4, "moyenne multimodele":5, "moyenne glissante":6, "Groupement par mois":7}
menu_stats = {
    1: mean_value,
    2: maximum_value,
    3: minimum_value,
    4: percentile,
    5: moyenne_multimodele,
    6: rolling_mean_value,
    7: Qmonth_interannual
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
    1: IPS,
    2: Qmean,
    3: Q90_95,
    4: Q10_05,
    5: VCN10,
    6: VCX3,
    7: over_threshold
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
# skip_n = int(input("Combien de lignes de métadonnées (en-têtes sans compter le nom des colonnes) y a-t-il? "))

while True:
    try:
        skip_n = int(input("Combien de lignes de métadonnées (en-têtes sans compter le nom des colonnes) y a-t-il? "))
        
        if skip_n < 0:
            print("Veuillez entrer un nombre positif.")
            continue
            
        break
        
    except ValueError:
        print("Veuillez entrer un nombre entier valide.")

df = pd.read_csv(path, sep=";", skiprows=skip_n)
# Nettoyage = supprimer les colonnes ou lignes entièrement vides (pas de dates, pas de noms ...)
df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)



try:
    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]], dayfirst=True) # On suppose que la première colonne est celle des dates
except Exception:
    print("Attention : la première colonne n'a pas pu être convertie en datetime.")

#df[df.columns[0]]=pd.to_datetime(df[df.columns[0]], dayfirst=True) # On suppose que la première colonne est celle des dates
for col in df.select_dtypes(include="object"):
    df[col]=df[col].str.replace(",",".",regex=False).astype(float)
    

print(df.info()) # Afficher à l'utilisateur les noms des colonnes que comporte son fichier

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
        df = menu_indicateurs[indicator_choice](df)
        

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
        df = menu_stats[stat_choice](df)

    # Demande de la visualisation
    print("\nVisualisations disponibles :")
    for name, num in dict_visualization.items():
        print(f"[{num}] {name}")
    #visualization = int(input("Enter the index of the visualization you want: "))
    while True:
        try:
            visualization = int(input("Enter the index of the visualization you want: "))
        
            if visualization not in menu:
                print("Choix invalide.")
                continue
            
            break
        
        except ValueError:
            print("Veuillez entrer un nombre entier valide.")

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

