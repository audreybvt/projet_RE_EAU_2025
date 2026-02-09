# ---------------- mean ---------------- a été modifié pour correspondre à nouvelle structure
#gérer le cas où il y a des nan pour mettre le moyenne là où, il y a des valeurs

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

    # --- Nom automatique de la nouvelle colonne ---
    new_col_name = f"mean_{col_name}"

    # --- Calcul de la moyenne et ajout de la colonne ---
    try:
        mean_val = df[col_name].astype(float).mean()
    except Exception as e:
        raise ValueError(f"Impossible de calculer la moyenne de la colonne {col_name} : {e}")
    
    df[new_col_name] = mean_val  # répété sur toutes les lignes

    print(f"\n Colonne '{new_col_name}' ajoutée avec la moyenne de '{col_name}' = {mean_val:.2f}")

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
    
