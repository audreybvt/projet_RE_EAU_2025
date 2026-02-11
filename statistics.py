# ---------------- mean ---------------- a été modifié pour correspondre à nouvelle structure
#gérer le cas où il y a des nan pour mettre le moyenne là où, il y a des valeurs
import pandas as pd
import numpy as np

def ask_date(message):
    #fonction pour ne pas avoir à tout relancer en cas d'erreur de saisie
    while True:
        user_input = input(message).strip()
        
        if user_input == "":
            return None  # L'utilisateur veut toute la période
        
        try:
            return pd.to_datetime(user_input, dayfirst=True)
        except Exception:
            print("Format invalide ❌  Utilisez YYYY-MM-DD ou DD/MM/YYYY")

def mean_value(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---
    try:
        col_idx = int(input("\nIndex de la colonne pour calculer la moyenne : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne")
    
    if col_idx < 0 or col_idx >= len(df.columns):
        raise IndexError("Index de colonne invalide")
    
    col_name = df.columns[col_idx]

    # --- Affichage de la plage disponible ---
    date_col = df.columns[0]

    # Filtrer uniquement les lignes où la colonne choisie n'est pas NaN
    df_valid = df[df[col_name].notna()]

    if df_valid.empty:
        raise ValueError(f"Aucune donnée valide dans la colonne '{col_name}'")

    min_date = df_valid[date_col].min()
    max_date = df_valid[date_col].max()

    print("\nPériode disponible pour la colonne sélectionnée :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    #min_date = df[date_col].min()
    #max_date = df[date_col].max()

    #print("\nPériode disponible dans le fichier :")
    #print(f" Du {min_date.date()} au {max_date.date()}")

    # --- Choix de la période ---
    print("\nDéfinition de la période (laisser vide pour utiliser toute la période)")

    start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date("Date de fin   (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]

    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée disponible sur la période sélectionnée")

    # Calcul de la moyenne
    try:
        mean_val = df_period[col_name].astype(float).mean()
    except Exception as e:
        raise ValueError(f"Impossible de calculer la moyenne de {col_name} : {e}")

    # --- Nom explicite de la colonne ---
    period_str = ""
    if start_date or end_date:
        period_str = f"_{start_date.date() if start_date else 'start'}_" \
                     f"{end_date.date() if end_date else 'end'}"

    new_col_name = f"mean_{col_name}{period_str}"

    df[new_col_name] = np.where(df[col_name].isna(), np.nan, mean_val) #on crée la nouvelle colonne qui respecte les nan de la colonne
    #d'origine

    print(
        f"\nColonne '{new_col_name}' ajoutée\n"
        f"Moyenne de '{col_name}' sur {len(df_period)} lignes = {mean_val:.2f}"
    )

    return df






def moyenne_multimodele(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix des colonnes ---
    colonnes_input = input(
        "Index des colonnes entre lesquelles effectuer une moyenne, séparés par une virgule (ex: 1,2,3) : "
    )

    try:
        colonnes = sorted(set(int(i.strip()) for i in colonnes_input.split(",")))
    except ValueError:
        raise ValueError("Les index doivent être des nombres entiers")

    for i in colonnes:
        if i < 0 or i >= len(df.columns):
            raise IndexError(f"Index invalide : {i}")

    index_colonnes = [df.columns[i] for i in colonnes]

    print(f"\n Colonnes sélectionnées : {index_colonnes}")

    # --- Nom automatique de la nouvelle colonne ---
    idx_str = "_".join(str(i) for i in colonnes)
    new_col_name = f"moyenne_multimodele_{idx_str}"

    # --- Calcul de la moyenne ligne par ligne ---
    try:
        mean_vals = df[index_colonnes].astype(float).mean(axis=1)
    except Exception as e:
        raise ValueError(f"Impossible de calculer la moyenne : {e}")

    # --- Ajout au dataframe ---
    df[new_col_name] = mean_vals

    print(f"\n Colonne {new_col_name} ajoutée (moyenne ligne par ligne des colonnes sélectionnées)")

    return df



def maximum_value(X):
    return X.max()

def minimum_value(X):
    return X.min()

def percentile(X, q): # When the q_th percentile is needed, 0 < q < 1
    return X.quantile(q)

def nombre_ocurrences_au_dessus_seuil(X,seuil): # Attention à la définition de X
    compteur=0
    for x in X:
        if x>=seuil :
            compteur+=1
    return compteur
    
def rolling_mean_value(df):
    import pandas as pd

    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---
    try:
        col_idx = int(input("\nIndex de la colonne pour la moyenne glissante : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne")
    
    if col_idx < 0 or col_idx >= len(df.columns):
        raise IndexError("Index de colonne invalide")
    
    col_name = df.columns[col_idx]

    # --- Colonne date (on suppose qu'elle est en 1ère position) ---
    date_col = df.columns[0]

    min_date = df[date_col].min()
    max_date = df[date_col].max()

    print("\nPériode disponible dans le fichier :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    # --- Choix de la période ---
    print("\nDéfinition de la période (laisser vide pour utiliser toute la période)")

    start_date = input("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date = input("Date de fin   (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df.copy()

    if start_date:
        start_date = pd.to_datetime(start_date, dayfirst=True)
        df_period = df_period[df_period[date_col] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date, dayfirst=True)
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée disponible sur la période sélectionnée")

    # --- Taille de la fenêtre ---
    try:
        window = int(input("\nTaille de la fenêtre pour la moyenne glissante (nombre de lignes) : "))
    except ValueError:
        raise ValueError("Veuillez entrer un entier pour la taille de la fenêtre")

    if window <= 0:
        raise ValueError("La fenêtre doit être strictement positive")

    # --- Calcul moyenne glissante ---
    try:
        rolling_series = (
            df_period[col_name]
            .astype(float)
            .rolling(window=window)
            .mean()
        )
    except Exception as e:
        raise ValueError(f"Impossible de calculer la moyenne glissante de {col_name} : {e}")

    # --- Nom explicite de la colonne ---
    period_str = ""
    if start_date or end_date:
        period_str = f"_{start_date.date() if start_date else 'start'}_" \
                     f"{end_date.date() if end_date else 'end'}"

    new_col_name = f"rolling_mean_{col_name}_w{window}{period_str}"

    # On crée la colonne vide dans le df original
    df[new_col_name] = None

    # On remplit uniquement les lignes correspondant à la période
    df.loc[df_period.index, new_col_name] = rolling_series

    print(
        f"\nColonne '{new_col_name}' ajoutée\n"
        f"Moyenne glissante (fenêtre={window}) calculée sur {len(df_period)} lignes"
    )

    return df