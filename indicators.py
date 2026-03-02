# Fonctions de calculs d'indicateurs hydrologiques
import pandas as pd
import numpy as np

# code IPS (Indice de Penman-Schneiter) _____________________________________________________
def IPS(df):
    print("Calcul de l'IPS: colonnes disponibles")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    try:
        # Sélection des colonnes
        idx_p = int(input("\nIndex de la colonne Précipitations (P) : "))
        idx_etr = int(input("Index de la colonne Évapotranspiration Réelle (ETR) : "))
        idx_dr = int(input("Index de la colonne Variation de Réserve (ΔR) : "))
        
        col_p = df.columns[idx_p]
        col_etr = df.columns[idx_etr]
        col_dr = df.columns[idx_dr]

    except (ValueError, IndexError):
        raise ValueError("Sélection de colonnes invalide. Veuillez entrer les index affichés.")

    # Nouvelle colonne
    new_col_name = "IPS"

    #Calcul de l'IPS
    # Formule : IPS = P - ETR - ΔR
    try:
        df[new_col_name] = (
            df[col_p].astype(float) - 
            df[col_etr].astype(float) - 
            df[col_dr].astype(float)
        )
    except Exception as e:
        raise ValueError(f"Erreur lors du calcul mathématique : {e}")

    # Affichage 
    recharge_moyenne = df[new_col_name].mean()
    print(f"Colonne '{new_col_name}' ajoutée.")
    print(f"Moyenne du bilan hydrique calculée : {recharge_moyenne:.2f}")

    return df

# calcul de Qmoy (débit moyen sur une période)

def Qmoy(df):
    print("Calcul du Débit Moyen (Qmoy): colonnes disponibles")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # Sélection des colonnes 
    try:
        idx_t = int(input("\nIndex de la colonne Date : "))
        col_t = df.columns[idx_t]
        idx_q = int(input("Index de la colonne Débit (Q) : "))
        col_q = df.columns[idx_q]
    except (ValueError, IndexError):
        raise ValueError("Entrée invalide (index ou nombre incorrect).")
    
    # Configuration de la période 
    try:   
        unite = input("Choisissez l'unité de temps (j: jours, m: mois, a: années) : ").lower().strip()
        freq_map = {'j': 'D', 'm': 'ME', 'a': 'YE'} # 'YE' pour Year End
        
        if unite not in freq_map:
            raise ValueError("L'unité doit être j, m ou a.")
            
        label_unite = {"j": "jours", "m": "mois", "a": "années"}[unite]
        nb = int(input(f"Entrez le pas de temps (ex: '3' pour avoir la moyenne tous les 3 {label_unite}) : "))
        
        frequence = f"{nb}{freq_map[unite]}"
    except ValueError as e:
        raise ValueError(f"Erreur de saisie : {e}")

    # Calcul et ajout au dataframe
    df[col_t] = pd.to_datetime(df[col_t])
    
    try:
        new_col_date = f"Date_Paquet_{nb}{unite}"
        new_col_q = f"Qmoy_{nb}{unite}"

        # Calcul par paquet (on utilise une copie pour le resample)
        df_resampled = df.set_index(col_t)[col_q].astype(float).resample(frequence).mean().reset_index()
        df_resampled.columns = [new_col_date, new_col_q]

        # Ajout des colonnes sur le df existant 
        df = pd.concat([df, df_resampled], axis=1)

        print(f" Colonnes '{new_col_date}' et '{new_col_q}' ajoutées.")
        print(df[[new_col_date, new_col_q]].dropna().head())

    except Exception as e:
        raise ValueError(f"Erreur lors du calcul : {e}")

    return df