
#Set of statistics functions to treat variables from netCDF files
#Called in the "# netCDF case" part of the main file

import xarray as xr
import pandas as pd
import numpy as np
import calendar


# functiun to ask for a date with error handling and support for multiple formats
def ask_date(ds):
    """
    Ask the user for a start and end date within the dataset time range.
    Returns (start_date, end_date) as pandas Timestamp or None.
    """


    time_values = pd.to_datetime(ds["time"].values)

    min_date = time_values.min()
    max_date = time_values.max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période (laisser vide pour tout afficher)")

    while True:

        start_input = input("Date de début (YYYY-MM-DD) : ").strip()
        end_input = input("Date de fin (YYYY-MM-DD) : ").strip()

        try:
            start_date = pd.to_datetime(start_input) if start_input else None
        except:
            print("Invalid date format.")
            continue

        try:
            end_date = pd.to_datetime(end_input) if end_input else None
        except:
            print("Invalid date format.")
            continue

        

        # --- vérifier cohérence ---
        if start_date and end_date and start_date > end_date:
            print("La date de début doit être antérieure à la date de fin.")
            continue

        # --- vérifier dans le domaine ---
        if start_date and start_date < min_date:
            print("La date de début est avant la période disponible.")
            continue

        if end_date and end_date > max_date:
            print("La date de fin est après la période disponible.")
            continue

        break

    return start_date, end_date












### Mean value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________


def mean_value_flexible(ds):
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

    # Identification of available dimensions
    available_dims = list(active_da.dims)
    dims_to_reduce = []
    
    print("\nWhich dimensions do you want to average across?")
    print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
    for i, d in enumerate(available_dims):
        print(f" [{i}] {d}")

    
    while True:

        choice_dims = input("Your choice: ").strip()

        if choice_dims == "":
            dims_to_reduce = available_dims
            break

        try:
            indices = list(set(int(x.strip()) for x in choice_dims.split(",")))
            dims_to_reduce = [available_dims[i] for i in indices]
            break

        except (ValueError, IndexError):
            print("Invalid input. Please enter valid indices separated by commas or leave blank to select all dimensions.")


        
    # Handling of time period if 'time' is selected 
    period_label = "" 

    if "time" in dims_to_reduce:

        print("\n--- Period configuration for the mean ---")

        while True:

            start_date, end_date = ask_date(ds)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

            break


    # Mean calculation
    print(f"\nCalculating mean across: {dims_to_reduce}...")
    mean_val = active_da.mean(dim=dims_to_reduce, skipna=True)

    # Variable naming
    # Create a suffix based on the reduced dimensions
    dims_suffix = "_mean_on_" + "_".join(dims_to_reduce)
    new_var_name = f"{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    # Inject the mean value. Xarray will automatically align/broadcast it across the remaining dimensions.
    ds[new_var_name] = xr.where(ds[var_name].isnull(), np.nan, mean_val)

    # Display results
    print(f"\n Variable added: {new_var_name}")
    if mean_val.size == 1:
        print(f"Unique mean value: {float(mean_val.values):.2f}")
    else:
        print(f"Remaining dimensions after mean: {list(mean_val.dims)}")
        print(f"Result shape: {mean_val.shape}")

    return ds






### Maximum value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def maximum_value_flexible(ds):
    # Variable selection
    vars_list = list(ds.data_vars)
    print("\nAvailable variables:")
    for i, var in enumerate(vars_list):
        print(f" [{i}] {var}")

    while True:
        try:
            var_idx = int(input("\nIndex of the variable to find the maximum: "))
            var_name = vars_list[var_idx]
            break
        except (ValueError, IndexError):
            print("Invalid index. Please try again.")

    active_da = ds[var_name]

    # Identification of available dimensions
    available_dims = list(active_da.dims)
    dims_to_reduce = []
    
    print("\nAcross which dimensions do you want to find the maximum?")
    print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
    for i, d in enumerate(available_dims):
        print(f" [{i}] {d}")

    
    while True:

        choice_dims = input("Your choice: ").strip()

        if choice_dims == "":
            dims_to_reduce = available_dims
            break

        try:
            indices = list(set(int(x.strip()) for x in choice_dims.split(",")))
            dims_to_reduce = [available_dims[i] for i in indices]
            break

        except (ValueError, IndexError):
            print("Invalid input. Please enter valid indices separated by commas or leave blank to select all dimensions .")



    # Handling of time period if 'time' is selected 
    period_label = "" 

    if "time" in dims_to_reduce:

        print("\n--- Period configuration for the maximum ---")

        while True:

            start_date, end_date = ask_date(ds)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

            break



    # Maximum calculation
    print(f"\nCalculating maximum across: {dims_to_reduce}...")
    max_val = active_da.max(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_max_on_" + "_".join(dims_to_reduce)
    new_var_name = f"max_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    # Broadcast the max result back to the original dataset shape for compatibility
    ds[new_var_name] = xr.where(ds[var_name].isnull(), np.nan, max_val)

    # 7. Display results
    print(f"\n Variable added: {new_var_name}")
    if max_val.size == 1:
        print(f"Unique maximum value: {float(max_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(max_val.dims)}")
        print(f"Result shape: {max_val.shape}")

    return ds

















### Minimum value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def minimum_value_flexible(ds):
    # Variable selection
    vars_list = list(ds.data_vars)
    print("\nAvailable variables:")
    for i, var in enumerate(vars_list):
        print(f" [{i}] {var}")

    while True:
        try:
            var_idx = int(input("\nIndex of the variable to find the minimum: "))
            var_name = vars_list[var_idx]
            break
        except (ValueError, IndexError):
            print("Invalid index. Please try again.")

    active_da = ds[var_name]

    # Identification of available dimensions
    available_dims = list(active_da.dims)
    dims_to_reduce = []
          

    print("\nAcross which dimensions do you want to find the minimum?")
    print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
    for i, d in enumerate(available_dims):
        print(f" [{i}] {d}")

    
    while True:

        choice_dims = input("Your choice: ").strip()

        if choice_dims == "":
            dims_to_reduce = available_dims
            break

        try:
            indices = list(set(int(x.strip()) for x in choice_dims.split(",")))
            dims_to_reduce = [available_dims[i] for i in indices]
            break

        except (ValueError, IndexError):
            print("Invalid input. Please enter valid indices separated by commas or leave blank to select all dimensions .")

    

    # Handling of time period if 'time' is selected 
    period_label = "" 

    if "time" in dims_to_reduce:

        print("\n--- Period configuration for the minimum ---")

        while True:

            start_date, end_date = ask_date(ds)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

            break

    # Minimum calculation
    print(f"\nCalculating minimum across: {dims_to_reduce}...")
    min_val = active_da.min(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_min_on_" + "_".join(dims_to_reduce)
    new_var_name = f"min_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    # Broadcast the min result back to the original dataset shape for compatibility
    ds[new_var_name] = xr.where(ds[var_name].isnull(), np.nan, min_val)

    # Display results
    print(f"\n Variable added: {new_var_name}")
    if min_val.size == 1:
        print(f"Unique minimum value: {float(min_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(min_val.dims)}")
        print(f"Result shape: {min_val.shape}")

    return ds






### Percentile value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def percentile_value_flexible(ds):
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

    # Percentile selection
    while True:
        try:
            q = float(input("Desired percentile (e.g., 0.9 for 90%): "))
            if not 0 <= q <= 1:
                raise ValueError
            break
        except ValueError:
            print("The percentile must be a number between 0 and 1.")

    # Identification of available dimensions
    available_dims = list(active_da.dims)
    dims_to_reduce = []
    
    print("\nAcross which dimensions do you want to calculate the percentile?")
    print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
    for i, d in enumerate(available_dims):
        print(f" [{i}] {d}")

    
    while True:

        choice_dims = input("Your choice: ").strip()

        if choice_dims == "":
            dims_to_reduce = available_dims
            break

        try:
            indices = list(set(int(x.strip()) for x in choice_dims.split(",")))
            dims_to_reduce = [available_dims[i] for i in indices]
            break

        except (ValueError, IndexError):
            print("Invalid input. Please enter valid indices separated by commas or leave blank to select all dimensions .")

    
    
    # Handling of time period if 'time' is involved
    period_label = "" 

    if "time" in dims_to_reduce:

        print("\n--- Period configuration for the percentile ---")

        while True:

            start_date, end_date = ask_date(ds)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

            break

    # Percentile calculation
    print(f"\nCalculating {int(q*100)}th percentile across: {dims_to_reduce}...")
    # Note: quantile() in xarray uses the 0-1 scale for q
    perc_val = active_da.quantile(q, dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = f"_perc{int(q*100)}_on_" + "_".join(dims_to_reduce)
    new_var_name = f"perc{int(q*100)}_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    # Broadcast the result back to the original dataset shape
    ds[new_var_name] = xr.where(ds[var_name].isnull(), np.nan, perc_val)

    # Display results
    print(f"\nVariable added: {new_var_name}")
    if perc_val.size == 1:
        print(f"Unique percentile value: {float(perc_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(perc_val.dims)}")
        print(f"Result shape: {perc_val.shape}")

    return ds













### rolling mean value of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def rolling_mean_value(ds):
    # Variable selection
    vars_list = list(ds.data_vars)
    print("\nAvailable variables:")
    for i, var in enumerate(vars_list):
        print(f" [{i}] {var}")

    while True:
        try:
            var_idx = int(input("\nIndex of the variable for rolling mean: "))
            var_name = vars_list[var_idx]
            break
        except (ValueError, IndexError):
            print("Invalid index. Please try again.")

    active_da = ds[var_name]

    # Handling of time period
    period_label = ""
    
    if "time" in active_da.dims:

        print("\n--- Period configuration for the rolling mean ---")

        while True:

            start_date, end_date = ask_date(ds)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

            break

    # Window size selection
    while True:
        try:
            window = int(input("\nWindow size (number of time steps): "))
            if window <= 0:
                raise ValueError
            break
        except ValueError:
            print("Window size must be a positive integer.")

    # Rolling mean calculation
    # min_periods=1 ensures we get values even at the start of the series
    print(f"\nCalculating rolling mean (window={window}) along 'time' dimension...")
    rolling_val = active_da.rolling(time=window, center=True, min_periods=1).mean()

    # Variable naming
    new_var_name = f"rolling_mean_{var_name}_w{window}{period_label}"

    # Add to Dataset
    # We use xr.where to maintain the original mask/null values
    ds[new_var_name] = xr.where(ds[var_name].isnull(), np.nan, rolling_val)

    # Display results
    print(f"\nVariable added: {new_var_name}")
    print(f"Result shape: {rolling_val.shape}")

    return ds













### Interannual grouping by month of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________


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

    # Check for time dimension
    if 'time' not in active_da.dims:
        print("Error: This variable does not have a 'time' dimension.")
        return ds

    # Calculation of monthly means (1 to 12)
    print(f"\nCalculating interannual monthly averages for '{var_name}'...")
    
    # Note: Even with decode_cf=False, we try to use the time components 
    # If time is raw integers, we convert to datetime objects first for grouping
    try:
        # We group by month and calculate the mean along the 'time' dimension
        # this reduces the 'time' dimension to a 'month' dimension (size 12)
        monthly_stats = active_da.groupby("time.month").mean(dim="time", skipna=True)
    except AttributeError:
        # If decode_cf=False prevents time.month access, we provide a warning
        print("Error: Time is not decoded. Cannot extract months from raw integers.")
        print("Please ensure 'decode_cf=True' was used during loading for this specific tool.")
        return ds

    # Preparing the Coordinate (Month names)
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    monthly_stats = monthly_stats.assign_coords(month=month_names)

    # Variable naming
    # We find how many interannual variables already exist to avoid overwriting
    base_name = f"interannual_month_{var_name}"
    occurrence = sum(1 for v in ds.data_vars if v.startswith(base_name)) + 1
    new_var_name = f"{base_name}_{occurrence}"

    # Add to Dataset
    # IMPORTANT: Unlike mean/max, we do NOT use xr.where here. 
    # Interannual stats have a different shape (12 months) than the daily series.
    # We add it as a new variable with its own dimension 'month'.
    ds[new_var_name] = monthly_stats

    # Display results
    print(f"\nVariable added: {new_var_name}")
    print(f"Resulting Shape: {monthly_stats.shape} (Dimensions: {list(monthly_stats.dims)})")
    
    # Preview of the first few stations if applicable
    print("\nPreview of January averages:")
    try:
        jan_preview = monthly_stats.sel(month="January")
        print(jan_preview.head())
    except:
        pass

    return ds