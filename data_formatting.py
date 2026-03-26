import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path

def handle_spatial_dimensions(ds, filename="dataset"):
    """
    Gère simplement les dimensions spatiales du dataset.
    Deux options: (1) Garder tout, (2) Sélectionner une seule entité (point/station).
    
    Parameters:
        ds: xarray.Dataset à traiter
        filename: nom du fichier pour affichage (optionnel)
    """
    # Identifier les dimensions spatiales potentielles
    spatial_dim = None

    # Chercher les dimensions de points (piézomètres, stations, etc.)
    point_dims = ['piezometre', 'station', 'stations', 'site', 'sites', 'location', 'locations']
    for dim in point_dims:
        if dim in ds.dims:
            spatial_dim = dim
            break

    # Si pas de dimension point, chercher les grilles
    if not spatial_dim:
        grid_dims = ['latitude', 'longitude', 'lat', 'lon', 'x', 'y']
        for dim in grid_dims:
            if dim in ds.dims:
                spatial_dim = dim
                break

    # Si aucune dimension spatiale détectée, retourner le dataset tel quel
    if not spatial_dim:
        return ds

    # Afficher l'info
    print(f"\n Fichier: {filename}")
    print(f"Dimension spatiale détectée: '{spatial_dim}' ({len(ds[spatial_dim])} valeurs)")

    # Menu simple
    print("\nOptions:")
    print("[1] Garder toutes les données")
    print("[2] Sélectionner une seule entité")

    while True:
        try:
            choice = int(input("Votre choix (1-2): ").strip())
            if choice in [1, 2]:
                break
            print("Choix invalide. Entrez 1 ou 2.")
        except ValueError:
            print("Veuillez entrer un nombre.")

    # Option 1: Garder tout
    if choice == 1:
        print("→ Conservation de toutes les données")
        return ds

    # Option 2: Sélectionner une entité
    else:
        print(f"\nEntités disponibles dans '{spatial_dim}':")
        coords = ds.coords[spatial_dim].values
        
        # Afficher les 10 premières
        for i, coord in enumerate(coords[:10]):
            print(f"[{i}] {coord}")
        if len(coords) > 10:
            print(f"... et {len(coords) - 10} autres")

        while True:
            try:
                idx = int(input(f"Index (0-{len(coords)-1}): ").strip())
                if 0 <= idx < len(coords):
                    selected = coords[idx]
                    print(f"→ Sélection: {selected}")
                    return ds.sel({spatial_dim: selected})
                else:
                    print("Index hors limites.")
            except ValueError:
                print("Veuillez entrer un nombre.")

def load_multiple_datasets(paths):
    """
    Charge plusieurs fichiers NetCDF et ajoute les dimensions
    model et scenario avant de les combiner.
    Utilise dask pour éviter les problèmes de mémoire.
    """

    datasets = []

    for path in paths:

        # Ouvrir sans décodage automatique (en spécifiant le moteur explicitement)
        try:
            ds = xr.open_dataset(path, decode_cf=False, engine='netcdf4')
        except Exception:
            # Fallback: essayer h5netcdf
            try:
                ds = xr.open_dataset(path, decode_cf=False, engine='h5netcdf')
            except Exception as e:
                print(f"Erreur lors de l'ouverture du fichier {path}: {e}")
                continue

        # Décodage manuel du temps seulement
        if 'time' in ds:
            ds = ds.assign_coords(time=xr.coding.times.decode_cf_datetime(
                ds['time'], ds['time'].attrs.get('units', 'days since 1900-01-01'),
                calendar=ds['time'].attrs.get('calendar', 'standard')
            ))

        # Gestion interactive des dimensions spatiales
        filename = Path(path).name  # Extraire le nom du fichier
        ds = handle_spatial_dimensions(ds, filename=filename)

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
            "model": [model_chain]
        })

        # Convertir en dask avec un chunking intelligent adapté aux dimensions disponibles
        chunk_dict = {}

        # Priorité au chunking temporel si disponible
        if 'time' in ds.dims:
            chunk_dict['time'] = min(1000, ds.sizes['time'])

        # Chunking des dimensions spatiales/ponctuelles
        spatial_dims = ['piezometre', 'latitude', 'longitude', 'lat', 'lon', 'x', 'y']
        for dim in spatial_dims:
            if dim in ds.dims and ds.sizes[dim] > 1:
                chunk_dict[dim] = min(100, ds.sizes[dim])
                break  # Un seul chunking spatial pour éviter la surcharge

        # Si aucune dimension connue, chunker la plus grande dimension non-scalaire
        if not chunk_dict:
            for dim, size in ds.sizes.items():
                if size > 1 and dim not in ['scenario', 'model']:  # Éviter les nouvelles dimensions
                    chunk_dict[dim] = min(1000, size)
                    break

        # Appliquer le chunking si des dimensions ont été trouvées
        if chunk_dict:
            ds = ds.chunk(chunk_dict)
        else:
            # Fallback: chunking automatique
            ds = ds.chunk('auto')

        datasets.append(ds)

    # combinaison avec dask
    combined = xr.combine_by_coords(datasets, combine_attrs='drop', join='outer', data_vars='all')
    print(f"\nCombinaison terminée. Dataset : {combined}")
    return combined

def clean_dataframe(df):

    df_clean = df.copy()
    date_col = None

    # 1) Priority to obvious names
    for candidate in [
        "Date", "date", "DATE",
        "time", "Time", "TIME",
        "Dates", "dates", "DATES",
        "Times", "times", "TIMES"
    ]:
        if candidate in df_clean.columns:
            df_clean[candidate] = pd.to_datetime(
                df_clean[candidate],
                errors="coerce"
            )
            date_col = candidate
            print(f" Date column detected by name: {candidate}")
            break

    # 2) Automatic detection otherwise
    if date_col is None:

        for col in df_clean.columns:

            if pd.api.types.is_numeric_dtype(df_clean[col]):
                continue

            if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                date_col = col
                print(f" Date column detected (already datetime): {col}")
                break

            converted = pd.to_datetime(
                df_clean[col],
                dayfirst=True,
                errors="coerce"
            )

            valid_ratio = converted.notna().mean()

            if valid_ratio > 0.8:
                df_clean[col] = converted
                date_col = col
                print(f" Date column detected: {col} ({valid_ratio:.0%} valid)")
                break

    # Final check
    if date_col is None:
        print(" No date column detected.")
    else:
        print(f" Using '{date_col}' as time index.")

    return df_clean, date_col

def csv_to_xarray(filepath):
    """
    Generic CSV -> xarray.Dataset converter
    Compatible with multidimensional NetCDF workflows
    """

    # Preview
    print("\nPreview of the first 5 lines:")
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        for i in range(5):
            line = f.readline()
            clean_line = line.replace(";;", ";").strip(";")
            print(f"Line {i} | {clean_line[:100]}...")
    print("________")

    # Ask metadata lines to skip
    while True:
        try:
            skip_n = int(input("How many metadata lines (before column names)? "))
            if skip_n < 0:
                print("Enter a positive number.")
                continue
            break
        except ValueError:
            print("Enter a valid integer.")

    df = pd.read_csv(filepath, sep=";", skiprows=skip_n)

    # Remove empty rows/columns
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

    # Clean + detect date
    df, date_col = clean_dataframe(df)

    # --- Time index ---
    if date_col:
        df = df.set_index(date_col)
        df.index.name = "time"
    else:
        raise ValueError("No date column detected")

    # --- Detect potential dimension columns ---
    possible_dims = [
        "model", "scenario",
        "station", "stations",
        "site", "sites",
        "piezometre",
        "location", "locations",
        "latitude", "longitude",
        "lat", "lon",
        "x", "y"
    ]

    dims_to_use = [col for col in possible_dims if col in df.columns]

    # Convert dimensions to string (categorical coords)
    for col in dims_to_use:
        df[col] = df[col].astype(str)

    # Add to MultiIndex
    if dims_to_use:
        df = df.set_index(dims_to_use, append=True)

    df = df.sort_index()

    # --- Ensure index uniqueness (required by xarray) ---
    if not df.index.is_unique:
        raise ValueError(
            "Index is not unique. Missing a dimension column "
            "to uniquely identify observations."
        )

    # --- Convert to xarray ---
    ds = df.to_xarray()

    ds["time"] = pd.to_datetime(ds["time"])

    print("Generated xarray Dataset:")
    print(ds)

    return ds
