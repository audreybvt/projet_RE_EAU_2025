import pandas as pd
import numpy as np
import calendar

'''
def ask_date(message):
    #fonction pour ne pas avoir à tout relancer en cas d'erreur de saisie
    while True:
        user_input = input(message).strip()
        
        if user_input == "":
            return None  # L'utilisateur veut toute la période
        
        try:
            return pd.to_datetime(user_input, dayfirst=True)
        except Exception:
            print("Format invalide ; utilisez YYYY-MM-DD ou DD/MM/YYYY")
'''


def ask_date(message):
    while True:
        user_input = input(message).strip()

        if user_input == "":
            return None

        try:

            # format ISO
            if "-" in user_input:
                return pd.to_datetime(user_input, format="%Y-%m-%d")

            # format français
            elif "/" in user_input:
                return pd.to_datetime(user_input, format="%d/%m/%Y")

            else:
                raise ValueError

        except Exception:
            print("Format invalide ; utilisez YYYY-MM-DD ou DD/MM/YYYY")

        

def mean_value(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---  

    while True:
        try:
            col_idx = int(input("\nIndex de la colonne pour calculer la moyenne : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")


    
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


    # --- Choix de la période ---
    print("\nDéfinition de la période sur laquelle calculer la moyenne temporelle (laisser vide pour utiliser toute la période)")

    while True:
        start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date("Date de fin   (YYYY-MM-DD ou DD/MM/YYYY) : ")

        df_period = df.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]

        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break
    



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
    while True:
        try:
            colonnes_input = input("Index des colonnes entre lesquelles effectuer une moyenne (ex: 1,2,3) : ")

            colonnes = sorted(set(int(i.strip()) for i in colonnes_input.split(",")))

            for i in colonnes:
                if i < 0 or i >= len(df.columns):
                    raise IndexError

            break

        except ValueError:
            print("Les index doivent être des nombres entiers.")
        except IndexError:
            print("Un index de colonne est invalide.")

    
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





def maximum_value(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")
 

    while True:
        try:
            col_idx = int(input("\nIndex de la colonne pour calculer le maximum : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    col_name = df.columns[col_idx]
    date_col = df.columns[0]

    df_valid = df[df[col_name].notna()]

    if df_valid.empty:
        raise ValueError(f"Aucune donnée valide dans la colonne '{col_name}'")

    min_date = df_valid[date_col].min()
    max_date = df_valid[date_col].max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période sur laquelle calculer le maximum (laisser vide pour toute la période)")
    
    while True:
        start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

        df_period = df.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]

        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break

    max_val = df_period[col_name].astype(float).max()

    period_str = ""
    if start_date or end_date:
        period_str = f"_{start_date.date() if start_date else 'start'}_" \
                     f"{end_date.date() if end_date else 'end'}"

    new_col_name = f"max_{col_name}{period_str}"

    df[new_col_name] = np.where(df[col_name].isna(), np.nan, max_val)

    print(
        f"\nColonne '{new_col_name}' ajoutée\n"
        f"Maximum de '{col_name}' sur {len(df_period)} lignes = {max_val:.2f}"
    )

    return df

    

def minimum_value(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")
  

    while True:
        try:
            col_idx = int(input("\nIndex de la colonne pour calculer le minimum : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    col_name = df.columns[col_idx]
    date_col = df.columns[0]

    df_valid = df[df[col_name].notna()]

    if df_valid.empty:
        raise ValueError(f"Aucune donnée valide dans la colonne '{col_name}'")

    min_date = df_valid[date_col].min()
    max_date = df_valid[date_col].max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période sur laquelle calculer le minimum (laisser vide pour toute la période)")
       
    while True:
        start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

        df_period = df.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]

        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break


    min_val = df_period[col_name].astype(float).min()

    period_str = ""
    if start_date or end_date:
        period_str = f"_{start_date.date() if start_date else 'start'}_" \
                     f"{end_date.date() if end_date else 'end'}"

    new_col_name = f"min_{col_name}{period_str}"

    df[new_col_name] = np.where(df[col_name].isna(), np.nan, min_val)

    print(
        f"\nColonne '{new_col_name}' ajoutée\n"
        f"Minimum de '{col_name}' sur {len(df_period)} lignes = {min_val:.2f}"
    )

    return df
   


###############

def percentile(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")
   

    while True:
        try:
            col_idx = int(input("\nIndex de la colonne : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    col_name = df.columns[col_idx]
    date_col = df.columns[0]
   

    while True:
        try:
            q = float(input("Percentile souhaité (ex: 0.9 pour 90%) : "))
            if not 0 < q < 1:
                raise ValueError
            break
        except ValueError:
            print("Le percentile doit être un nombre entre 0 et 1.")

    df_valid = df[df[col_name].notna()]

    if df_valid.empty:
        raise ValueError(f"Aucune donnée valide dans '{col_name}'")

    min_date = df_valid[date_col].min()
    max_date = df_valid[date_col].max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période sur laquelle calculer le percentile (laisser vide pour toute la période)")
    
    while True:
        start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

        df_period = df.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]

        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break



    perc_val = df_period[col_name].astype(float).quantile(q)

    period_str = ""
    if start_date or end_date:
        period_str = f"_{start_date.date() if start_date else 'start'}_" \
                     f"{end_date.date() if end_date else 'end'}"

    new_col_name = f"percentile_{int(q*100)}_{col_name}{period_str}"

    df[new_col_name] = np.where(df[col_name].isna(), np.nan, perc_val)

    print(
        f"\nColonne '{new_col_name}' ajoutée\n"
        f"Percentile {int(q*100)}% de '{col_name}' sur {len(df_period)} lignes = {perc_val:.2f}"
    )

    return df
   


##################

def rolling_mean_value(df):
    
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---
    while True:
        try:
            col_idx = int(input("\nIndex de la colonne pour la moyenne glissante : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    col_name = df.columns[col_idx]

    # --- Colonne date (on suppose qu'elle est en 1ère position) ---
    date_col = df.columns[0]

    min_date = df[date_col].min()
    max_date = df[date_col].max()

    print("\nPériode disponible dans le fichier :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    # --- Choix de la période ---
    print("\nDéfinition de la période sur laquelle calculer la moyenne glissante (laisser vide pour utiliser toute la période)")
    
    while True:
        start_date = ask_date("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

        df_period = df.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]

        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break


    # --- Taille de la fenêtre ---   

    while True:
        try:
            window = int(input("\nTaille de la fenêtre pour la moyenne glissante (nombre de lignes) : "))
            if window <= 0:
                raise ValueError
            break
        except ValueError:
            print("La fenêtre doit être un entier strictement positif.")
            

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


# Interannual monthly average 

def monthly_interannual_average_xr(ds):
    # Variable selection
    vars_list = list(ds.data_vars)
    print("\nAvailable variables:")
    for i, var in enumerate(vars_list):
        print(f" [{i}] {var}")

    while True:
        try:
            var_idx = int(input("\nIndex of the variable to process: "))
            var_name = vars_list[var_idx]
            break
        except (ValueError, IndexError):
            print("Invalid index. Please try again.")

    active_da = ds[var_name]

    # list of dimensions to identify the time dimension 
    dims_list = list(active_da.dims)
    print(f"\nDimensions for '{var_name}':")
    for i, d in enumerate(dims_list):
        print(f" [{i}] {d}")

    while True:
        try:
            dim_idx = int(input("Index of the time dimension: "))
            time_dim = dims_list[dim_idx]
            break
        except (ValueError, IndexError):
            print("Invalid index. Please choose an existing dimension.")

    # Calculation of monthly means (1 to 12)
    print(f"\nCalculating interannual monthly averages for '{var_name}'...")
    
    try:
        # FIX: Instead of "time.month", use the variable time_dim selected by the user
        # This allows the function to work if the dimension is named 'date', 'T', etc.
        monthly_stats = active_da.groupby(f"{time_dim}.month").mean(dim=time_dim, skipna=True)
    except (AttributeError, KeyError):
        # If decode_cf=False prevents time.month access, we provide a warning
        print(f"\nError: Could not extract months from '{time_dim}'.")
        print("Ensure 'decode_cf=True' was used during loading and that the dimension is a datetime type.")
        return ds

    # Preparing the Coordinate (Month names)
    # We rename the 'month' coordinate to match the string names
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    monthly_stats = monthly_stats.assign_coords(month=month_names)

    # Variable naming
    base_name = f"interannual_month_{var_name}"
    occurrence = sum(1 for v in ds.data_vars if v.startswith(base_name)) + 1
    new_var_name = f"{base_name}_{occurrence}"

    # Add to Dataset
    ds[new_var_name] = monthly_stats

    # Display results
    print(f"\nVariable added: {new_var_name}")
    print(f"Resulting Shape: {monthly_stats.shape} (Dimensions: {list(monthly_stats.dims)})")
    
    # Preview
    print("\nPreview of January averages:")
    try:
        # Since we assigned coords, we select by the new 'month' coordinate
        jan_preview = monthly_stats.sel(month="January")
        print(jan_preview.head())
    except Exception:
        pass

    return ds