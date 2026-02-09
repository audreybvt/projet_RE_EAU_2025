# Fonctions de calculs d'indicateurs hydrologiques


def IPS(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---
    try:
        col_idx = int(input("\nIndex de la colonne pour calculer l'IPS : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne")
    
    if col_idx < 0 or col_idx >= len(df.columns):
        raise IndexError("Index de colonne invalide")
    
    col_name = df.columns[col_idx]

    # --- Nom automatique de la nouvelle colonne ---
    new_col_name = f"IPS_{col_name}"

    # --- Calcul de la moyenne et ajout de la colonne ---
    try:
        IPS_val = df[col_name].astype(float).mean() # CALCUL IPS A AJOUTER
    except Exception as e:
        raise ValueError(f"Impossible de calculer l'indicateur IPS de la colonne {col_name} : {e}")
    
    df[new_col_name] = IPS_val  # répété sur toutes les lignes

    print(f"\n Colonne '{new_col_name}' ajoutée avec le calcul de l'IPS de la colonne '{col_name}'")

    return df
