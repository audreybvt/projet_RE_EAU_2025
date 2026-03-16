import pandas as pd
import xarray as xr
from pathlib import Path

def load_multiple_datasets(paths):
    """
    Charge plusieurs fichiers NetCDF et ajoute les dimensions
    model et scenario avant de les combiner.
    """

    datasets = []

    for path in paths:

        ds = xr.open_dataset(path, decode_cf=False)

        #Converting time values to YYYY-MM-DD
        ds['time'] = xr.coding.times.decode_cf_datetime(
            ds['time'], 
            ds['time'].attrs['units'], 
            calendar=ds['time'].attrs.get('calendar', 'standard')
        )
        ds['time'].attrs['units'] = 'YYYY-MM-DD'
        ds['time'].attrs.pop('calendar', None)

        #Create attributes for model and scenario
        # récupération des métadonnées si elles existent
        scenario = ds.attrs.get("experiment_id", "unknown")
        gcm = ds.attrs.get("driving_model_id", "unknown")
        rcm = ds.attrs.get("model_id", "unknown")
        bc = ds.attrs.get("bc_method_id", "unknown")
        hy_model = ds.attrs.get("hy_model_id", "unknown")
        
        
        if "unknown" in (gcm, rcm, bc, hy_model, scenario) :
            return print("The format of the file is not appropriate")
        
        # Créer une seule dimension "model_chain"
        model_chain = f"{gcm}-{rcm}-{bc}-{hy_model}"

        # Étendre le dataset avec les deux nouvelles dimensions
        ds = ds.expand_dims({
            "scenario": [scenario],
            "model_chain": [model_chain]
        })

        datasets.append(ds)

    # combinaison
    combined = xr.combine_by_coords(datasets, combine_attrs='drop')

    return combined

import pandas as pd

def clean_dataframe(df):
    """
    Nettoie un DataFrame avant visualisation :
    - Détecte automatiquement la colonne de dates et la convertit en datetime.
    - Convertit les colonnes object contenant des nombres (avec ',' ou '.') en float.
    - Les textes non convertibles restent inchangés (ou deviennent NaN si numeric coercion).
    
    Retourne :
        df_clean : DataFrame nettoyé
        date_col : nom de la colonne contenant la date (None si non trouvée)
    """
    df_clean = df.copy()
    date_col = None

    # --- Détection automatique de la colonne date ---
    for col in df_clean.columns:
        try:
            df_clean[col] = pd.to_datetime(df_clean[col], dayfirst=True, errors="raise")
            if df_clean[col].notna().all():
                date_col = col
                break
        except Exception:
            print("Attention : aucune colonne n'a pas pu être convertie en datetime.")
            continue

    # --- Conversion des colonnes object en float si possible ---
    for col in df_clean.select_dtypes(include="object"):
        # Remplacement de ',' par '.' pour les nombres décimaux
        df_clean[col] = pd.to_numeric(df_clean[col].str.replace(",", ".", regex=False), errors="coerce")

    return df_clean, date_col

def csv_to_xarray(filepath):
    """
    Conversion générique CSV -> xarray.Dataset
    """

    # prévisualisation
    print("\nAperçu des 5 premières lignes du fichier brut :")
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        for i in range(5):
            line = f.readline()
            clean_line = line.replace(";;", ";").strip(";")
            print(f"Ligne {i} | {clean_line[:100]}...")
    print("____________________")

    # On demande à l'utilisateur combien de lignes de métadonnées il souhaite ignorer
    while True:
        try:
            skip_n = int(input("Combien de lignes de métadonnées (en-têtes sans compter le nom des colonnes) y a-t-il? "))
            
            if skip_n < 0:
                print("Veuillez entrer un nombre positif.")
                continue
                
            break
            
        except ValueError:
            print("Veuillez entrer un nombre entier valide.")

    df = pd.read_csv(filepath, sep=";", skiprows=skip_n)
    # Nettoyage = supprimer les colonnes ou lignes entièrement vides (pas de dates, pas de noms ...)
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

    df, date_col = clean_dataframe(df)

    # Identifier types de colonnes
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    object_cols = df.select_dtypes(include="object").columns.tolist()

    # Si colonne date trouvée → index temporel
    if date_col:
        df = df.set_index(date_col)
        df.index.name = "time" # correction 

    # Cas long (au moins une colonne catégorielle)
    if object_cols:
        df = df.set_index(object_cols, append=True)

    # Conversion
    ds = df.to_xarray()

    return ds
