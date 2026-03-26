
#Set of statistics functions to treat variables from netCDF files
#Called in the "# netCDF case" part of the main file

import xarray as xr
import pandas as pd
import numpy as np
import calendar
from utils_xr import show_info


# functiun to ask for a date with error handling and support for multiple formats
def ask_date(ds, start_input_gui=None, end_input_gui=None, log_func=None):
    """
    Ask the user for a start and end date within the dataset time range.
    Returns (start_date, end_date) as pandas Timestamp or None.
    """
    time_values = pd.to_datetime(ds["time"].values)
    min_date = time_values.min()
    max_date = time_values.max()

    if start_input_gui is not None or end_input_gui is not None:
        start_date = pd.to_datetime(start_input_gui) if start_input_gui else None
        end_date = pd.to_datetime(end_input_gui) if end_input_gui else None
        return start_date, end_date

    # Detect if we should skip interactive input (e.g. if we are in a GUI environment)
    # We can't always know, so we'll check if any gui params were meant to be passed
    # In Streamlit, this function should generally NOT be called without gui params
    # but for safety let's assume if it is, we might block. 
    # Better: the calling functions in statistics_xr already have _gui params.

    show_info("\nPériode disponible :", log_func=log_func)
    show_info(f" Du {min_date.date()} au {max_date.date()}", log_func=log_func)
    show_info("\nDéfinition de la période (laisser vide pour tout afficher)", log_func=log_func)

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
        if start_date and end_date and start_date > end_date:
            print("La date de début doit être antérieure à la date de fin.")
            continue
        if start_date and start_date < min_date:
            print("La date de début est avant la période disponible.")
            continue
        if end_date and end_date > max_date:
            print("La date de fin est après la période disponible.")
            continue
        break
    return start_date, end_date


#function to apply to check if a time dimension is selected and allow user to select a specific period for the calculation.
# This function is called in the mean, max, min and percentile functions to avoid code repdef apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui=None, end_input_gui=None, log_func=None):
    period_label = ""
    time_dims = [d for d in active_da.dims if "time" in d]
    if not time_dims:
        return active_da, ""
    t_dim = time_dims[0]
    
    # If GUI params are provided, skip interactive loop
    if start_input_gui is not None or end_input_gui is not None:
        start_date, end_date = ask_date(ds, start_input_gui, end_input_gui, log_func=log_func)
        if start_date or end_date:
            slice_dict = {}
            if start_date and end_date:
                slice_dict[t_dim] = slice(start_date, end_date)
                period_label = f"_{start_date.date()}_{end_date.date()}"
            elif start_date:
                slice_dict[t_dim] = slice(start_date, None)
                period_label = f"_from_{start_date.date()}"
            else:
                slice_dict[t_dim] = slice(None, end_date)
                period_label = f"_until_{end_date.date()}"
            
            temp_da = active_da.sel(slice_dict)
            # Safety check: ensure the selection isn't empty
            if temp_da[t_dim].size == 0:
                # If GUI input leads to empty selection, return original and no label
                return active_da, ""
            return temp_da, period_label
        return active_da, "" # If GUI params are provided but result in no date, return original da

    show_info(f"\n--- Period configuration (detected dimension: {t_dim}) ---", log_func=log_func)
    while True:
        start_date, end_date = ask_date(ds, start_input_gui, end_input_gui, log_func=log_func)
        if start_date or end_date:
            slice_dict = {}
            if start_date and end_date:
                slice_dict[t_dim] = slice(start_date, end_date)
                period_label = f"_{start_date.date()}_{end_date.date()}"
            elif start_date:
                slice_dict[t_dim] = slice(start_date, None)
                period_label = f"_from_{start_date.date()}"
            else:
                slice_dict[t_dim] = slice(None, end_date)
                period_label = f"_until_{end_date.date()}"
            temp_da = active_da.sel(slice_dict)
        else:
            # If no dates entered, use the full range
            temp_da = active_da

        # Safety check: ensure the selection isn't empty
        if temp_da[t_dim].size == 0:
            print(f"No data available in this range for '{t_dim}'. Please try again.")
            if start_input_gui is not None:
                break
            continue

        # Update the DataArray and create the label
        active_da = temp_da
        if start_date or end_date:
            s = start_date.date() if start_date else "start"
            e = end_date.date() if end_date else "end"
            period_label = f"_{s}_{e}"
        
        break

    return active_da, period_label




### Mean value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________


def mean_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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
    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = [d for d in available_dims if "time" not in d.lower()]
        if not dims_to_reduce: dims_to_reduce = available_dims
    else:
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

    # Handling of time period if 'time' is contained in the selected dimensions
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui)

    # Mean calculation
    if not is_gui:
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

def maximum_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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
    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = [d for d in available_dims if "time" not in d.lower()]
        if not dims_to_reduce: dims_to_reduce = available_dims
    else:
        dims_to_reduce = []
        print("\nAcross which dimensions do you want to find the maximum?")
        print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
        for i, d in enumerate(available_dims):
            print(f" [{i}] {d} ({ds.dims[d]} values)")

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

    # Handling of time period if 'time' is contained in the selected dimensions
    active_da, period_label=apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui)

    # Maximum calculation
    print(f"\nCalculating maximum across: {dims_to_reduce}...")
    max_val = active_da.max(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_max_on_" + "_".join(dims_to_reduce)
    new_var_name = f"max_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    ds[new_var_name] = max_val

    # 7. Display results
    print(f"\n Variable added: {new_var_name}")
    if max_val.size == 1:
        print(f"Unique maximum value: {float(max_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(max_val.dims)}")
        print(f"Result shape: {max_val.shape}")

    return ds

















### Minimum value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def minimum_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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
    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = [d for d in available_dims if "time" not in d.lower()]
        if not dims_to_reduce: dims_to_reduce = available_dims
    else:
        dims_to_reduce = []
        print("\nAcross which dimensions do you want to find the minimum?")
        print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
        for i, d in enumerate(available_dims):
            print(f" [{i}] {d} ({ds.dims[d]} values)")

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

    # Handling of time period if 'time' is contained in the selected dimensions
    active_da, period_label=apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui)

    # Minimum calculation
    print(f"\nCalculating minimum across: {dims_to_reduce}...")
    min_val = active_da.min(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_min_on_" + "_".join(dims_to_reduce)
    new_var_name = f"min_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    ds[new_var_name] = min_val

    # Display results
    print(f"\n Variable added: {new_var_name}")
    if min_val.size == 1:
        print(f"Unique minimum value: {float(min_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(min_val.dims)}")
        print(f"Result shape: {min_val.shape}")

    return ds






### Median value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def median_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
        print("\nAvailable variables:")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")

        while True:
            try:
                var_idx = int(input("\nIndex of the variable to find the median: ").strip())
                var_name = vars_list[var_idx]
                break
            except (ValueError, IndexError):
                print("Invalid index. Please try again.")

    active_da = ds[var_name]

    # Identification of available dimensions
    available_dims = list(active_da.dims)
    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        # Default in GUI mode if not specified: reduce all dimensions except 'time' if possible, or just all
        dims_to_reduce = [d for d in available_dims if "time" not in d.lower()]
        if not dims_to_reduce: dims_to_reduce = available_dims
    else:
        dims_to_reduce = []
        print("\nAcross which dimensions do you want to find the median?")
        print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
        for i, d in enumerate(available_dims):
            print(f" [{i}] {d} ({ds.dims[d]} values)")

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
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui)

    # Median calculation
    print(f"\nCalculating median across: {dims_to_reduce}...")
    median_val = active_da.median(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_median_on_" + "_".join(dims_to_reduce)
    new_var_name = f"median_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    ds[new_var_name] = median_val

    # Display results
    print(f"\nVariable added: {new_var_name}")
    if median_val.size == 1:
        print(f"Unique median value: {float(median_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(median_val.dims)}")
        print(f"Result shape: {median_val.shape}")

    return ds


### Percentile value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def percentile_value_flexible(ds, var_name_gui=None, q_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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

    if q_gui is not None:
        q = q_gui
    else:
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
    is_gui = any(p is not None for p in [var_name_gui, q_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = [d for d in available_dims if "time" not in d.lower()]
        if not dims_to_reduce: dims_to_reduce = available_dims
    else:
        dims_to_reduce = []
        print("\nAcross which dimensions do you want to calculate the percentile?")
        print("Enter the indices separated by commas (e.g., 0,2). Leave blank to select all dimensions.")
        for i, d in enumerate(available_dims):
            print(f" [{i}] {d} ({ds.dims[d]} values)")

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

    # Handling of time period if 'time' is contained in the selected dimensions
    active_da, period_label=apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui)

    # Percentile calculation
    print(f"\nCalculating {int(q*100)}th percentile across: {dims_to_reduce}...")
    # Note: quantile() in xarray uses the 0-1 scale for q
    perc_val = active_da.quantile(q, dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = f"_perc{int(q*100)}_on_" + "_".join(dims_to_reduce)
    new_var_name = f"perc{int(q*100)}_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    ds[new_var_name] = perc_val

    # Display results
    print(f"\nVariable added: {new_var_name}")
    if perc_val.size == 1:
        print(f"Unique percentile value: {float(perc_val.values):.2f}")
    else:
        print(f"Remaining dimensions after calculation: {list(perc_val.dims)}")
        print(f"Result shape: {perc_val.shape}")

    return ds













### rolling mean value of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________

def rolling_mean_value(ds, var_name_gui=None, window_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)
    is_gui = any(p is not None for p in [var_name_gui, window_gui, start_input_gui, end_input_gui])
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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
        if not is_gui:
            print("\n--- Period configuration for the rolling mean ---")

        while True:

            start_date, end_date = ask_date(ds, start_input_gui, end_input_gui)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # vérifier s'il y a des données
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                if start_input_gui is not None:
                    break # Break if using GUI because we cannot prompt again
                continue

            # si la sélection est valide
            active_da = temp_da

            if start_date or end_date:

            # In GUI mode, if no date provided or if already applied, just break
                if any(p is not None for p in [var_name_gui, window_gui, start_input_gui, end_input_gui]):
                    break
            break

    if window_gui is not None:
        window = window_gui
    else:
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
    if not is_gui:
        print(f"\nCalculating rolling mean (window={window}) along 'time' dimension...")
    rolling_val = active_da.rolling(time=window, center=True, min_periods=1).mean()

    # Variable naming
    new_var_name = f"rolling_mean_{var_name}_w{window}{period_label}"

    # Add to Dataset
    ds[new_var_name] = rolling_val

    # Display results
    print(f"\nVariable added: {new_var_name}")
    print(f"Result shape: {rolling_val.shape}")

    return ds













### Interannual grouping by month of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset _____________________________________________


def monthly_interannual_average_xr(ds, var_name_gui=None, time_dim_gui=None):
    vars_list = list(ds.data_vars)
    if var_name_gui is not None:
        var_name = var_name_gui
    else:
        # Variable selection
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

    if time_dim_gui is not None:
        time_dim = time_dim_gui
    elif any(p is not None for p in [var_name_gui, time_dim_gui]):
        # Default to 'time' or first dimension in GUI mode
        time_dim = next((d for d in active_da.dims if "time" in d.lower()), active_da.dims[0])
    else:
        # list of dimensions to identify the time dimension 
        dims_list = list(active_da.dims)
        print(f"\nDimensions for '{var_name}':")
        for i, d in enumerate(dims_list):
            print(f" [{i}] {d} ({active_da.dims[d]} values)")

        while True:
            try:
                dim_idx = int(input("Which time dimension do you want to use for grouping ? "))
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
        fev_preview = monthly_stats.sel(month="February")
        print(fev_preview.head())
        mar_preview = monthly_stats.sel(month="March")
        print(mar_preview.head())
    except Exception:
        pass

    return ds