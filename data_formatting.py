import pandas as pd
import xarray as xr

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