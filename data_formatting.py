import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path

def handle_spatial_dimensions(ds):
    """
    Gère interactivement les dimensions spatiales du dataset.
    Permet de garder toutes les données, sélectionner un point ou une zone.
    """
    # Identifier les dimensions spatiales potentielles
    spatial_dims = {}
    coord_names = {}

    # Dimensions de grille (latitude/longitude) - vérifier indépendamment
    if 'latitude' in ds.dims or 'longitude' in ds.dims:
        spatial_dims['grid'] = ['latitude', 'longitude']
        coord_names['grid'] = ['latitude', 'longitude']

    # Dimensions alternatives de grille
    elif 'lat' in ds.dims or 'lon' in ds.dims:
        spatial_dims['grid'] = ['lat', 'lon']
        coord_names['grid'] = ['lat', 'lon']

    # Dimensions de coordonnées projetées
    elif 'x' in ds.dims or 'y' in ds.dims:
        spatial_dims['grid'] = ['x', 'y']
        coord_names['grid'] = ['x', 'y']

    # Dimensions de points (piézomètres, stations) - vérifier indépendamment
    point_dims = ['piezometre', 'station', 'stations', 'site', 'sites', 'location', 'locations']
    for dim in point_dims:
        if dim in ds.dims:
            spatial_dims['points'] = [dim]
            coord_names['points'] = [dim]
            break

    # Si aucune dimension spatiale détectée, retourner le dataset tel quel
    if not spatial_dims:
        return ds

    # Afficher les dimensions spatiales disponibles
    print(f"\nDataset spatial détecté avec les dimensions: {list(ds.dims.keys())}")
    print(f"Types spatiaux détectés: {list(spatial_dims.keys())}")

    # Menu de choix adapté aux types disponibles
    print("\nOptions pour les dimensions spatiales:")
    option_num = 1
    options_map = {}

    if 'grid' in spatial_dims:
        print(f"[{option_num}] Garder toutes les données de grille")
        options_map[option_num] = ('grid', 'keep')
        option_num += 1
        print(f"[{option_num}] Sélectionner un point sur la grille")
        options_map[option_num] = ('grid', 'point')
        option_num += 1
        print(f"[{option_num}] Sélectionner une zone sur la grille")
        options_map[option_num] = ('grid', 'region')
        option_num += 1

    if 'points' in spatial_dims:
        print(f"[{option_num}] Garder toutes les stations/points")
        options_map[option_num] = ('points', 'keep')
        option_num += 1
        print(f"[{option_num}] Sélectionner une station/point spécifique")
        options_map[option_num] = ('points', 'select')
        option_num += 1

    print(f"[{option_num}] Conserver toutes les données spatiales")
    options_map[option_num] = ('all', 'keep')

    # Saisir le choix de l'utilisateur
    while True:
        try:
            choice = int(input(f"Votre choix (1-{option_num}): ").strip())
            if choice in options_map:
                break
            print(f"Choix invalide. Entrez un nombre entre 1 et {option_num}.")
        except ValueError:
            print("Veuillez entrer un nombre.")

    # Traiter le choix
    spatial_type, action = options_map[choice]

    if spatial_type == 'all':
        print("→ Conservation de toutes les données spatiales")
        return ds
    elif spatial_type == 'grid':
        if action == 'keep':
            print("→ Conservation de toutes les données de grille")
            return ds
        elif action == 'point':
            return select_spatial_point(ds, {'grid': spatial_dims['grid']}, {'grid': coord_names['grid']})
        elif action == 'region':
            return select_spatial_region(ds, spatial_dims['grid'], coord_names['grid'])
    elif spatial_type == 'points':
        if action == 'keep':
            print("→ Conservation de toutes les stations/points")
            return ds
        elif action == 'select':
            return select_spatial_point(ds, {'points': spatial_dims['points']}, {'points': coord_names['points']})

def select_spatial_point(ds, spatial_dims, coord_names):
    """Sélectionne un point/station spécifique"""
    print("\nSélection d'un point/station:")

    # Pour les données de points (piézomètres, stations)
    if 'points' in spatial_dims:
        dim_name = spatial_dims['points'][0]
        coord_name = coord_names['points'][0]
        
        # Chercher les coordonnées spatiales associées aux points
        spatial_coord_vars = {}
        coord_pairs = [('latitude', 'longitude'), ('lat', 'lon'), ('Lat', 'Lon'), ('x', 'y')]
        
        for lat_var, lon_var in coord_pairs:
            if lat_var in ds.data_vars and lon_var in ds.data_vars:
                if ds[lat_var].dims == (dim_name,) and ds[lon_var].dims == (dim_name,):
                    spatial_coord_vars = {'lat': lat_var, 'lon': lon_var}
                    break
        
        # Menu de sélection
        print(f"Points disponibles ({len(ds.coords[coord_name].values)}):")
        print("[1] Sélectionner par index")
        if spatial_coord_vars:
            print("[2] Sélectionner le point le plus proche (par coordonnées)")
            print("[3] Afficher les points proches")
        
        while True:
            try:
                method = int(input("Méthode (1-3): ").strip()) if spatial_coord_vars else 1
                if (method in [1, 2, 3]) if spatial_coord_vars else (method == 1):
                    break
                print("Choix invalide.")
            except ValueError:
                print("Veuillez entrer un nombre.")
        
        # Méthode 1: Par index
        if method == 1:
            for i, point in enumerate(ds.coords[coord_name].values[:10]):
                print(f"[{i}] {point}")
            if len(ds.coords[coord_name].values) > 10:
                print(f"... et {len(ds.coords[coord_name].values) - 10} autres")

            while True:
                try:
                    idx = int(input(f"Index (0-{len(ds.coords[coord_name].values)-1}): ").strip())
                    if 0 <= idx < len(ds.coords[coord_name].values):
                        selected_point = ds.coords[coord_name].values[idx]
                        print(f"→ Sélection: {selected_point}")
                        return ds.sel({dim_name: selected_point})
                    else:
                        print("Index hors limites.")
                except ValueError:
                    print("Veuillez entrer un nombre.")
        
        # Méthode 2: Point le plus proche
        elif method == 2 and spatial_coord_vars:
            lat_var = spatial_coord_vars['lat']
            lon_var = spatial_coord_vars['lon']
            
            try:
                lat_val = float(input("Latitude: ").strip())
                lon_val = float(input("Longitude: ").strip())
                
                lats = ds[lat_var].values
                lons = ds[lon_var].values
                distances = ((lats - lat_val)**2 + (lons - lon_val)**2)**0.5
                idx = int(np.argmin(distances))
                
                selected_point = ds.coords[coord_name].values[idx]
                selected_lat = lats[idx]
                selected_lon = lons[idx]
                print(f"→ Point sélectionné: {selected_point} (lat={selected_lat:.4f}, lon={selected_lon:.4f})")
                return ds.sel({dim_name: selected_point})
                
            except (ValueError, IndexError):
                print("Entrée invalide.")
                return ds
        
        # Méthode 3: Top 5 points proches
        elif method == 3 and spatial_coord_vars:
            lat_var = spatial_coord_vars['lat']
            lon_var = spatial_coord_vars['lon']
            
            try:
                lat_val = float(input("Latitude de référence: ").strip())
                lon_val = float(input("Longitude de référence: ").strip())
                
                lats = ds[lat_var].values
                lons = ds[lon_var].values
                distances = ((lats - lat_val)**2 + (lons - lon_val)**2)**0.5
                
                closest_indices = np.argsort(distances)[:5]
                
                print(f"\nPoints les plus proches de ({lat_val:.4f}, {lon_val:.4f}):")
                for i, idx in enumerate(closest_indices):
                    point_name = ds.coords[coord_name].values[idx]
                    point_lat = lats[idx]
                    point_lon = lons[idx]
                    dist = distances[idx]
                    print(f"[{i}] {point_name} - lat={point_lat:.4f}, lon={point_lon:.4f} (dist={dist:.4f}°)")
                
                choice = int(input("Sélectionner (0-4): ").strip())
                if 0 <= choice < len(closest_indices):
                    idx = closest_indices[choice]
                    selected_point = ds.coords[coord_name].values[idx]
                    return ds.sel({dim_name: selected_point})
                        
            except (ValueError, IndexError):
                print("Entrée invalide.")
                return ds

    # Pour les données grillées (sélection du point le plus proche)
    elif 'grid' in spatial_dims:
        lat_dim, lon_dim = spatial_dims['grid']
        lat_coord, lon_coord = coord_names['grid']

        print("Coordonnées disponibles:")
        print(".2f")
        print(".2f")

        try:
            lat_val = float(input("Latitude souhaitée: ").strip())
            lon_val = float(input("Longitude souhaitée: ").strip())

            # Sélection du point le plus proche
            selected = ds.sel({lat_coord: lat_val, lon_coord: lon_val}, method='nearest')
            print(".2f")
            return selected

        except ValueError:
            print("Coordonnées invalides. Conservation de toutes les données.")
            return ds

def select_spatial_region(ds, grid_dims, coord_names):
    """Sélectionne une région dans une grille"""
    print("\nSélection d'une région:")

    lat_dim, lon_dim = grid_dims
    lat_coord, lon_coord = coord_names

    print("Coordonnées disponibles:")
    print(".2f")
    print(".2f")

    try:
        print("\nDéfinissez la région (laisser vide pour garder les limites):")

        lat_min_input = input(".2f").strip()
        lat_max_input = input(".2f").strip()
        lon_min_input = input(".2f").strip()
        lon_max_input = input(".2f").strip()

        # Utiliser les limites par défaut si vide
        lat_min = float(lat_min_input) if lat_min_input else float(ds.coords[lat_coord].min())
        lat_max = float(lat_max_input) if lat_max_input else float(ds.coords[lat_coord].max())
        lon_min = float(lon_min_input) if lon_min_input else float(ds.coords[lon_coord].min())
        lon_max = float(lon_max_input) if lon_max_input else float(ds.coords[lon_coord].max())

        # Appliquer la sélection
        selected = ds.sel({
            lat_coord: slice(lat_min, lat_max),
            lon_coord: slice(lon_min, lon_max)
        })

        print(".2f")
        print(f"Nouvelle taille: {dict(selected.sizes)}")

        return selected

    except ValueError:
        print("Coordonnées invalides. Conservation de toutes les données.")
        return ds

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
        ds = handle_spatial_dimensions(ds)

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

    return combined


def clean_dataframe(df):

    df_clean = df.copy()
    date_col = None

    # ✅ 1) Priorité aux noms évidents
    for candidate in ["Date", "date", "DATE", "time", "Time", "Dates", "dates", "DATES", "times", "Times", "TIME", "TIMES"]:
        if candidate in df_clean.columns:
            df_clean[candidate] = pd.to_datetime(
                df_clean[candidate],
                errors="coerce"
            )
            date_col = candidate
            print(f" Colonne date détectée par nom : {candidate}")
            break

    # ✅ 2) Sinon détection automatique
    if date_col is None:

        for col in df_clean.columns:

            # Ignorer colonnes numériques → évite faux positifs
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                continue

            # Déjà datetime
            if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                date_col = col
                print(f" Colonne date détectée (déjà datetime) : {col}")
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
                print(f" Colonne date détectée : {col} ({valid_ratio:.0%} valide)")
                break

    # ✅ Vérification finale
    if date_col is None:
        print(" Aucune colonne de date détectée.")
    else:
        print(f" Utilisation de '{date_col}' comme index temporel.")

    # --- Conversion des colonnes object en float ---
    for col in df_clean.select_dtypes(include="object"):
        df_clean[col] = pd.to_numeric(
            df_clean[col].str.replace(",", ".", regex=False),
            errors="coerce"
        )

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
    # Nettoyage = supprimer les colonnes ou lignes entièrement vides
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

    # --- Nettoyage du DataFrame et détection de la date ---
    df, date_col = clean_dataframe(df)

    # Identifier types de colonnes
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    object_cols = df.select_dtypes(include="object").columns.tolist()

    # --- Index temporel ---
    if date_col:
        df = df.set_index(date_col)
        df.index.name = "time"  # renommer pour xarray
    else:
        raise ValueError("⚠️ Aucune colonne de date détectée")

    # --- Conserver les colonnes catégorielles comme coordonnées ---
    # On exclut 'model' de la conversion en float pour la garder comme coordonnée
    cat_cols = [col for col in object_cols if col != "model"]

    for col in cat_cols:
        # conversion en float si possible
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Si colonne 'model' existe, la mettre comme coordonnée
    if "model" in object_cols:
        df = df.set_index("model", append=True)

    # Conversion en xarray
    ds = df.to_xarray()

    # Corriger type de time
    ds["time"] = pd.to_datetime(ds["time"])

    print(" Dataset xarray généré :")
    print(ds)

    return ds

############# OLD clean_dataframe and OLD CSV_TO_XARRAY ###############
#######################################################################
#######################################################################


'''
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
'''