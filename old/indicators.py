# Hydrological Indicators Calculation Functions
import pandas as pd
import numpy as np

freq_map = {'d': 'D', 'm': 'M', 'y': 'Y'}


# IPS (Soil Water Balance Index) _____________________________________________________
def IPS(df):
    """
    Return the Index of Soil Precipitation (IPS) based on the water balance.

    Args:
        df: Input data with P, ETR, and ΔR columns.
    Returns:
        df: Original dataframe with added IPS column.
    """
    print("IPS Calculation: available columns")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    
    # Column selection
    while True:
        try:
            idx_p = int(input("\nIndex of Precipitation column (P): "))
            idx_etr = int(input("Index of Actual Evapotranspiration column (ETR): "))
            idx_dr = int(input("Index of Storage Change column (ΔR): "))

            if idx_p < 0 or idx_p >= len(df.columns):
                raise IndexError("P index out of range")

            if idx_etr < 0 or idx_etr >= len(df.columns):
                raise IndexError("ETR index out of range")

            if idx_dr < 0 or idx_dr >= len(df.columns):
                raise IndexError("ΔR index out of range")

            col_p = df.columns[idx_p]
            col_etr = df.columns[idx_etr]
            col_dr = df.columns[idx_dr]

            break

        except ValueError:
            print("Please enter integer indices.")

        except IndexError as e:
            print(e)



    # New column name
    new_col_name = "IPS"

    # IPS Calculation
    # Formula: IPS = P - ETR - ΔR
    try:
        df[new_col_name] = (
            df[col_p].astype(float) - 
            df[col_etr].astype(float) - 
            df[col_dr].astype(float)
        )
    except Exception as e:
        raise ValueError(f"Error during mathematical calculation: {e}")

    # Display results
    mean_recharge = df[new_col_name].mean()
    print(f"Column '{new_col_name}' added.")
    print(f"Calculated mean water balance: {mean_recharge:.2f}")

    return df






# Qmean/QA (mean discharge over a chosen period)

def Qmean(df):
    """
    Return the mean flow rate for a chosen period.

    Args:
        df: Input data with date and discharge columns.
    Returns:
        df: Original dataframe with added new-date and mean discharge (Qmean) stats.
    """
    print("Mean Discharge Calculation (Qmean): available columns")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    
    # Column selection
    while True:
        try:
            idx_t = int(input("\nIndex of Date column: "))
            if not 0 <= idx_t < len(df.columns):
                print("Date index out of range.")
                continue

            idx_q = int(input("Index of Discharge column (Q): "))
            if not 0 <= idx_q < len(df.columns):
                print("Discharge index out of range.")
                continue

            col_t = df.columns[idx_t]
            col_q = df.columns[idx_q]
            break

        except ValueError:
            print("Please enter integer indices.")

    
    
    while True:
        try:
            unite = input("Choose time unit (d: days, m: months, y: years): ").lower().strip()

            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue

            label_unite = {"d": "days", "m": "months", "y": "years"}[unite]

            nb = int(input(f"Enter time step (e.g., '3' to get the mean every 3 {label_unite}): "))
            if nb <= 0:
                print("Time step must be positive.")
                continue

            frequence = f"{nb}{freq_map[unite]}"
            break

        except ValueError:
            print("Please enter a valid integer.")

    # Calculation and adding to dataframe
    df[col_t] = pd.to_datetime(df[col_t])
    
    try:
        new_col_date = f"Date_Group_{nb}{unite}"
        new_col_q = f"Qmean_{nb}{unite}"

        # Grouped calculation (using label='left' for the start of the period)
        df_resampled = df.set_index(col_t)[col_q].astype(float).resample(frequence, label='left').mean().reset_index()
        df_resampled.columns = [new_col_date, new_col_q]

        # Add columns to existing df
        df = pd.concat([df, df_resampled], axis=1)

        print(f" Columns '{new_col_date}' and '{new_col_q}' added.")
        print(df[[new_col_date, new_col_q]].dropna().head())

    except Exception as e:
        raise ValueError(f"Calculation error: {e}")

    return df


# Q90/95 Drought Indicators (flow exceeded 90% or 95% of the time)

def Q90_95_xr(ds):
    """
    Return the flow rates exceeded 90% and 95% of the time for a chosen period (xarray version).

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and Q90/Q95 variables.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering (reusing your existing helper)
    active_ds, selections_made = categorical_filter(ds, standard_dims)

    # Time coordinate selection
    coords_list = list(ds.coords)
    print("\nAvailable coordinates for time:")
    for i, coord in enumerate(coords_list):
        print(f" [{i}] {coord}")
    
    while True:
        try:
            idx_t = int(input("Index of Date/Time coordinate: "))
            time_coord = coords_list[idx_t]
            break
        except (ValueError, IndexError):
            print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    vars_list = list(active_ds.data_vars)
    print("\nAvailable variables (for Discharge):")
    for i, var in enumerate(vars_list):
        print(f" [{i}] {var}")
    
    while True:
        try:
            idx_q = int(input("Index of Discharge variable (Q): "))
            var_q = vars_list[idx_q]
            break
        except (ValueError, IndexError):
            print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config (reusing your get_time_freq function)
    frequence, unite, nb, label_unite = get_time_freq()

    # Naming configuration
    new_time_dim = f"{time_coord}_Group_{nb}{unite}"
    new_var_q90 = f"Q90_{nb}{unite}_{var_q}"
    new_var_q95 = f"Q95_{nb}{unite}_{var_q}"

    try:
        print("Calculation Phase (Quantiles)")
        # Note: Q90 is the 0.10 quantile (flow exceeded 90% of the time)
        # Note: Q95 is the 0.05 quantile (flow exceeded 95% of the time)
        
        resampled_group = active_ds[var_q].resample({time_coord: frequence})
        
        # Calculate Q90
        # We use .drop_vars because xarray adds a 'quantile' coordinate by default
        da_q90 = resampled_group.quantile(0.10, skipna=True).drop_vars('quantile')
        da_q90 = da_q90.rename({time_coord: new_time_dim})
        
        # Calculate Q95
        da_q95 = resampled_group.quantile(0.05, skipna=True).drop_vars('quantile')
        da_q95 = da_q95.rename({time_coord: new_time_dim})

        # Add to main dataset
        ds[new_var_q90] = da_q90
        ds[new_var_q90].attrs['description'] = f"Q90 (exceeded 90% of time) over {nb} {label_unite} for {var_q}"
        
        ds[new_var_q95] = da_q95
        ds[new_var_q95].attrs['description'] = f"Q95 (exceeded 95% of time) over {nb} {label_unite} for {var_q}"

    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary
    print("\nQ90/95 calculation summary:")
    if selections_made:
        print("Selection:")
        for item in selections_made: print(f" - {item}")
    else:
        print("Selection: none (calculated across all categories).")

    print(f"New Temporal Coordinate added: '{new_time_dim}'")
    print(f"New Variables added: '{new_var_q90}' and '{new_var_q95}'")
    print(f"Dimensions: {ds[new_var_q90].dims}")
    print(f"Shape: {ds[new_var_q90].shape}")
    
    # Previews
    print(f"\nQ90 Preview (First 5 values):")
    print(ds[new_var_q90].values[:5])
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# VCN10 drought index (minimum 10-day consecutive mean flow) 

def VCN10(df):
    """
    Return the minimum 10-day consecutive mean flow for a chosen period.

    Args:
        df: Input data with date and discharge columns.
    Returns:
        df: Original dataframe with added new-date and VCN10 stats.
    """
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # Column selection
    
    while True:
        try:
            idx_t = int(input("\nIndex Date: "))
            if not 0 <= idx_t < len(df.columns):
                print("Date index out of range.")
                continue

            idx_q = int(input("Index Discharge (Q): "))
            if not 0 <= idx_q < len(df.columns):
                print("Discharge index out of range.")
                continue

            col_t, col_q = df.columns[idx_t], df.columns[idx_q]
            break

        except ValueError:
            print("Please enter integer indices.")

      

    while True:
        try:
            unite = input("Unit (d: days, m: months, y: years): ").lower().strip()

            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue

            label_unite = {"d": "days", "m": "months", "y": "years"}[unite]

            nb = int(input(f"Enter the calculation period in {label_unite} (e.g., '3' to find the minimum 10-day mean within every 3 {label_unite}): "))
            if nb <= 0:
                print("Time step must be positive.")
                continue

            frequence = f"{nb}{freq_map[unite]}"
            break

        except ValueError:
            print("Please enter a valid integer.")
    
    # Date conversion
    df[col_t] = pd.to_datetime(df[col_t])
    
    # Calculate 10-day rolling mean and Resample to find the minimum of these means over the specified period 
    # Date = first day of the period
    stats = df.set_index(col_t)[col_q].astype(float).rolling(window=10).mean().resample(frequence, label='left').min().reset_index()

    suffixe = f"_{nb}{unite}"
    stats.columns = [f"Date_VCN{suffixe}", f"VCN10{suffixe}"]
    
    # Combine results
    df = pd.concat([df, stats], axis=1)
    
    print(f"Column 'VCN10{suffixe}' added.")
    print(stats.dropna().head())
    
    return df






# Q10/Q05 High-flow Indicators (flow exceeded only 10% or 5% of the time)

def Q10_05(df):
    """
    Return the flow rates exceeded 10% and 5% of the time for a chosen period.

    Args:
        df: Input data with date and discharge columns.
    Returns:
        df: Original dataframe with added new-date, Q10 and Q05 stats columns.
    """
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

        

    while True:
        try:
            idx_t = int(input("\nIndex Date: "))
            if not 0 <= idx_t < len(df.columns):
                print("Date index out of range.")
                continue

            idx_q = int(input("Index Discharge (Q): "))
            if not 0 <= idx_q < len(df.columns):
                print("Discharge index out of range.")
                continue

            col_t, col_q = df.columns[idx_t], df.columns[idx_q]
            break

        except ValueError:
            print("Please enter integer indices.")
   


    while True:
        try:
            unite = input("Unit (d: days, m: months, y: years): ").lower().strip()

            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue

            label_unite = {"d": "days", "m": "months", "y": "years"}[unite]

            nb = int(input(f"Enter the calculation period in {label_unite} (e.g., '1' for the high-flow quantiles every 1 {label_unite}): "))
            if nb <= 0:
                print("Time step must be positive.")
                continue

            frequence = f"{nb}{freq_map[unite]}"
            break

        except ValueError:
            print("Please enter a valid integer.")



    df[col_t] = pd.to_datetime(df[col_t])
    
    # Calculation of Q10 (0.90 quantile) and Q05 (0.95 quantile)
    # These represent the high flows exceeded only 10% and 5% of the time.
    try:
        stats = df.set_index(col_t)[col_q].astype(float).resample(frequence, label='left').agg(
            Q10=lambda x: x.quantile(0.90),
            Q05=lambda x: x.quantile(0.95)
        ).reset_index()

        suffixe = f"_{nb}{unite}"
        stats.columns = [f"Date{suffixe}", f"Q10{suffixe}", f"Q05{suffixe}"]
        
        df = pd.concat([df, stats], axis=1)
        
        print(f"\n Columns 'Q10{suffixe}' and 'Q05{suffixe}' added.")
        print(stats.dropna().head())
        
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
    
    return df






# VCX3 High-flow index (maximum 3-day consecutive mean flow)

def VCX3(df):
    """
    Return the maximum 3-day consecutive mean flow for a chosen period.

    Args:
        df: Input data with date and discharge columns.
    Returns:
        df: Original dataframe with added new-date and VCX3 stats.
    """
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # Column selection
    
    while True:
        try:
            idx_t = int(input("\nIndex Date: "))
            if not 0 <= idx_t < len(df.columns):
                print("Date index out of range.")
                continue

            idx_q = int(input("Index Discharge (Q): "))
            if not 0 <= idx_q < len(df.columns):
                print("Discharge index out of range.")
                continue

            col_t, col_q = df.columns[idx_t], df.columns[idx_q]
            break

        except ValueError:
            print("Please enter integer indices.")

   

    while True:
        try:
            unite = input("Unit (d: days, m: months, y: years): ").lower().strip()

            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue

            label_unite = {"d": "days", "m": "months", "y": "years"}[unite]

            nb = int(input(f"Enter the calculation period in {label_unite} (e.g., '3' to find the maximum 3-day consecutive mean flow every 3 {label_unite}): "))
            if nb <= 0:
                print("Time step must be positive.")
                continue

            frequence = f"{nb}{freq_map[unite]}"
            break

        except ValueError:
            print("Please enter a valid integer.")



    
    # Date conversion
    df[col_t] = pd.to_datetime(df[col_t])
    
    # 1. Rolling window: Calculate the average of 3 consecutive days
    # 2. Resampling: Find the MAXIMUM of those 3-day averages within the period
    try:
        stats = df.set_index(col_t)[col_q].astype(float).rolling(window=3).mean().resample(frequence, label='left').max().reset_index()

        suffixe = f"_{nb}{unite}"
        stats.columns = [f"Date_VCX{suffixe}", f"VCX3{suffixe}"]
        
        # Combine results
        df = pd.concat([df, stats], axis=1)
        
        print(f"\nColumn 'VCX3{suffixe}' added.")
        print(f"This represents the highest 3-day mean discharge recorded per {nb} {label_unite}.")
        print(stats.dropna().head())
        
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
    
    return df







def over_threshold(df):    ### Renvoie des valeurs numériques, ne modifie pas le DataFrame d'entrée
    """
    Count occurrences above a threshold with tolerance,
    and compute episode statistics (duration and Peak Over Threshold (POT)).
    """

    print("\nOver-threshold indicator: available columns")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Column selection ---  

    while True:
        try:
            idx = int(input("\nIndex of the column to analyse: "))
            if not 0 <= idx < len(df.columns):
                print("Index out of range.")
                continue

            col = df.columns[idx]
            break

        except ValueError:
            print("Please enter an integer index.")


    # --- Threshold value ---
       
    while True:
        try:
            seuil = float(input("Enter threshold value: "))
            break
        except ValueError:
            print("Threshold must be a number.")
    


    # --- Tolerance percentage ---
        
    while True:
        try:
            tol = float(input("Tolerance percentage (%) around threshold: "))
            if tol < 0:
                print("Tolerance must be positive.")
                continue
            break
        except ValueError:
            print("Tolerance must be a number.")
            

    # --- Effective threshold ---
    seuil_effectif = seuil * (1 + tol / 100)

    print(f"\nEffective threshold used: {seuil_effectif:.3f}")
    print(f"(threshold {seuil} with tolerance {tol}%)")

    # --- Convert to numeric ---
    try:
        values = df[col].astype(float)
    except Exception:
        raise ValueError("Selected column cannot be converted to numeric values.")

    # --- Count exceedances ---
    exceed = values > seuil_effectif
    count = exceed.sum()

    print(f"\nNumber of occurrences above threshold: {count}")
    print(f"Total observations: {len(values)}")
    print(f"Percentage of exceedance: {100 * count / len(values):.2f}%")

    # ======================================================
    # Episode detection
    # ======================================================

    episodes = []
    pot_values = []

    current_duration = 0
    current_peak = None

    for val, exc in zip(values, exceed):

        if exc:
            current_duration += 1

            if current_peak is None:
                current_peak = val
            else:
                current_peak = max(current_peak, val)

        else:
            if current_duration > 0:
                episodes.append(current_duration)
                pot_values.append(current_peak)

            current_duration = 0
            current_peak = None

    # dernier épisode si la série finit au-dessus du seuil
    if current_duration > 0:
        episodes.append(current_duration)
        pot_values.append(current_peak)

    # ======================================================
    # Episode statistics
    # ======================================================

    if len(episodes) > 0:

        mean_duration = np.mean(episodes)

        print("\nEpisode statistics:")
        print(f"Number of independent episodes: {len(episodes)}")
        print(f"Mean episode duration: {mean_duration:.2f}")

        print("\nPeak Over Threshold (POT) values:")
        print(pot_values[:10])  # affiche les 10 premiers

    else:
        print("\nNo exceedance episodes detected.")

    return df
