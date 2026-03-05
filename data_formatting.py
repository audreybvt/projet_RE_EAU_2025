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

        # récupération des métadonnées si elles existent
        scenario = ds.attrs.get("experiment_id", "unknown")
        gcm = ds.attrs.get("driving_model_id", "unknown")
        rcm = ds.attrs.get("model_id", "unknown")
        bc = ds.attrs.get("bc_method_id", "unknown")
        hy_model = ds.attrs.get("hy_model_id", "unknown")
        
        
        if "unknown" in (gcm, rcm, bc, hy_model, scenario) :
            return print("The format of the file is not appropriate")
        
        
        # ajout des dimensions
        ds = ds.expand_dims({
            "scenario": [scenario],
            "gcm": [gcm],
            "rcm": [rcm],
            "hy_model": [hy_model],
        })

        datasets.append(ds)

    # combinaison intelligente
    combined = xr.combine_by_coords(datasets)

    return combined

def csv_to_xarray(filepath):
    """
    Conversion générique CSV -> xarray.Dataset
    """

    # Lecture automatique
    df = pd.read_csv(filepath)

    # Détection automatique des dates
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col])
            if df[col].notna().all():
                date_col = col
                break
        except:
            continue
    else:
        date_col = None

    # Identifier types de colonnes
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    object_cols = df.select_dtypes(include="object").columns.tolist()

    # Si colonne date trouvée → index temporel
    if date_col:
        df = df.set_index(date_col)

    # Cas long (au moins une colonne catégorielle)
    if object_cols:
        df = df.set_index(object_cols, append=True)

    # Conversion
    ds = df.to_xarray()

    return ds