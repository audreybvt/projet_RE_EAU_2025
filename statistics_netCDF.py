#Set of statistics functions to treat variables from netCDF files
#Called in the "# netCDF case" part of the main file

import xarray as xr

def mean_value(ds: xr.Dataset):
    # --- Liste des "colonnes" disponibles ---
    print("\nVariables disponibles dans le NetCDF :")
    vars_list = list(ds.data_vars)
    
    for i, var in enumerate(vars_list):
        da = ds[var]  # DataArray
        long_name = da.attrs.get("long_name", "—")
        units = da.attrs.get("units", "—")
        print(f" [{i}] {var}   | {long_name}, units = {units}")

    # --- Choix de la variable ---
    try:
        col_idx = int(input("\nIndex de la variable pour calculer la moyenne : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour l'index de la variable.")

    if col_idx < 0 or col_idx >= len(vars_list):
        raise IndexError("Index de variable invalide.")

    var_name = vars_list[col_idx]
    da = ds[var_name]

    # --- Nom automatique de la nouvelle variable ---
    new_var_name = f"mean_{var_name}"

    # Calcul de la moyenne
    try:
        mean_val = float(da.mean().values)
    except Exception as e:
        raise ValueError(f"Impossible de calculer la moyenne de '{var_name}' : {e}")

    # Ajouter une variable constante avec broadcast
    ds[new_var_name] = xr.full_like(da, fill_value=mean_val)

    print(f"\n✅ Variable '{new_var_name}' ajoutée avec la moyenne de '{var_name}' = {mean_val:.2f}")

    return ds

'''
#def moyenne_entre_plusieurs_colonnes()

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
    
'''