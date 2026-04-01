#Set of statistics functions to treat variables from netCDF files

# Import of the packages needed
import xarray as xr
import pandas as pd
import numpy as np
import calendar
from utils_xr import show_info

# ---------------- Helping Functions ----------------
#   Function to ask for a date with error handling and support for multiple formats
def ask_date(ds, start_input_gui=None, end_input_gui=None, log_func=None, is_gui=False):
    """
    Ask the user for a start and end date within the dataset time range.
    Returns (start_date, end_date) as pandas Timestamp or None.
    """
    time_values = pd.to_datetime(ds["time"].values)
    min_date = time_values.min()
    max_date = time_values.max()

    # GUI mode: bypass all input() calls
    if is_gui or start_input_gui is not None or end_input_gui is not None:
        start_date = pd.to_datetime(start_input_gui) if start_input_gui else None
        end_date = pd.to_datetime(end_input_gui) if end_input_gui else None
        return start_date, end_date

    print("\nAvailable period:")
    print(f" From {min_date.date()} to {max_date.date()}")

    print("\nDefine period (leave blank for full range)")

    while True:

        start_input = input("Start date (YYYY-MM-DD): ").strip()
        end_input = input("End date (YYYY-MM-DD): ").strip()

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

        

        # --- verify consistency ---
        if start_date and end_date and start_date > end_date:
            print("Start date must be before end date.")
            continue

        # --- verify range ---
        if start_date and start_date < min_date:
            print("Start date is before available period.")
            continue
        if end_date and end_date > max_date:
            print("End date is after available period.")
            continue
        break
    return start_date, end_date

#   Function to apply to check if a time dimension is selected and allow user to select a specific period for the calculation.
#   This function is called in the mean, max, min and percentile functions to avoid code repetition.
def apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui=None, end_input_gui=None, log_func=None, is_gui=False):
    """
    Detects a time-related dimension, prompts the user for a period,
    and slices the DataArray accordingly.
    """

    period_label = ""

    # Detect time dimension among the ones we plan to reduce
    time_dims = [d for d in dims_to_reduce if "time" in d]

    # No time dimension → nothing to do
    if not time_dims:
        return active_da, ""

    t_dim = time_dims[0]

    # GUI mode: bypass all input() calls - handles None dates (= full range)
    if is_gui or start_input_gui is not None or end_input_gui is not None:
        start_date, end_date = ask_date(ds, start_input_gui, end_input_gui, log_func=log_func, is_gui=is_gui)
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
            if temp_da.sizes.get(t_dim, 0) == 0:
                return active_da, ""
            return temp_da, period_label
        return active_da, ""  # No dates = full range, no label

    # Terminal-only path
    print(f"\n--- Period configuration (detected dimension: {t_dim}) ---")

    while True:

        start_date, end_date = ask_date(ds, is_gui=False)

        # Apply slicing
        if start_date or end_date:
            temp_da = active_da.sel({t_dim: slice(start_date, end_date)})
        else:
            temp_da = active_da

        # Safety 1: dimension still present?
        if t_dim not in temp_da.dims:
            print("Time dimension disappeared after operation. Please try again.")
            continue

        # Safety 2: non-empty data?
        if temp_da.sizes.get(t_dim, 0) == 0:
            print("No data available in this period. Please try again.")
            continue

        # OK
        active_da = temp_da

        if start_date or end_date:
            s = start_date.date() if start_date else "start"
            e = end_date.date() if end_date else "end"
            period_label = f"_{s}_{e}"

        break

    return active_da, period_label


# ---------------- Mean ----------------
#   Mean value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset

def mean_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)

    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
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

    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = available_dims
    else:
        dims_to_reduce = []
        print("\nWhich dimensions do you want to average across?")
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
                print("Invalid input. Please enter valid indices separated by commas or leave blank to select all dimensions.")

        
    # Handling of time period if 'time' is contained in the selected dimensions
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui, is_gui=is_gui)

    # Mean calculation
    if not is_gui:
        print(f"\nCalculating mean across: {dims_to_reduce}...")
    mean_val = active_da.mean(dim=dims_to_reduce, skipna=True)

    # Variable naming
    # Create a suffix based on the reduced dimensions
    dims_suffix = "_mean_on_" + "_".join(dims_to_reduce)
    new_var_name = f"{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    # Direct assignment: do NOT use xr.where here because when reducing 
    # dimensions (e.g. 'model'), mean_val has fewer dimensions than ds[var_name].
    if 'time' in dims_to_reduce and 'time' in ds.dims:
        # broadcast mean_val to have the same time dimension as ds for consistent handling in future operations
        mean_val, _ = xr.broadcast(mean_val, ds['time'])

    ds[new_var_name] = mean_val

    # Summary
    summary = {
        "method": "Mean",
        "var_name": var_name,
        "reduced_dims": dims_to_reduce,
        "period": period_label.lstrip('_') if period_label else "full range",
        "new_var": new_var_name,
        "dims": ds[new_var_name].dims,
        "shape": ds[new_var_name].shape,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else [],
        "first_5_dates": [str(d) for d in ds["time"].values[:5]] if 'time' in ds[new_var_name].dims else None
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print("\nMean calculation summary:")
        print(f"Dimensions reduced: {dims_to_reduce}")
        if period_label:
            print(f"Time period: {period_label.lstrip('_')}")
        else:
            print("Time period: full range")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds


# ---------------- Maximum ----------------
#   Maximum value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset

def maximum_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)

    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
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

    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = available_dims
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
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui, is_gui=is_gui)

    # Maximum calculation
    if not is_gui:
        print(f"\nCalculating maximum across: {dims_to_reduce}...")
    max_val = active_da.max(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_max_on_" + "_".join(dims_to_reduce)
    new_var_name = f"max_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    if 'time' in dims_to_reduce and 'time' in ds.dims:
        # broadcast max_val to have the same time dimension as ds for consistent handling in future operations
        max_val, _ = xr.broadcast(max_val, ds['time'])

    ds[new_var_name] = max_val

    # Summary
    summary = {
        "method": "Maximum",
        "var_name": var_name,
        "reduced_dims": dims_to_reduce,
        "period": period_label.lstrip('_') if period_label else "full range",
        "new_var": new_var_name,
        "dims": ds[new_var_name].dims,
        "shape": ds[new_var_name].shape,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else [],
        "first_5_dates": [str(d) for d in ds["time"].values[:5]] if 'time' in ds[new_var_name].dims else None
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print("\nMaximum calculation summary:")
        print(f"Dimensions reduced: {dims_to_reduce}")
        if period_label:
            print(f"Time period: {period_label.lstrip('_')}")
        else:
            print("Time period: full range")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds


# ---------------- Minimum ----------------
#   Minimum value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset

def minimum_value_flexible(ds, var_name_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)

    is_gui = any(p is not None for p in [var_name_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
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

    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = available_dims
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
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui, is_gui=is_gui)

    # Minimum calculation
    if not is_gui:
        print(f"\nCalculating minimum across: {dims_to_reduce}...")
    min_val = active_da.min(dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = "_min_on_" + "_".join(dims_to_reduce)
    new_var_name = f"min_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    if 'time' in dims_to_reduce and 'time' in ds.dims:
        # broadcast min_val to have the same time dimension as ds for consistent handling in future operations
        min_val, _ = xr.broadcast(min_val, ds['time'])

    ds[new_var_name] = min_val

    # Summary
    summary = {
        "method": "Minimum",
        "var_name": var_name,
        "reduced_dims": dims_to_reduce,
        "period": period_label.lstrip('_') if period_label else "full range",
        "new_var": new_var_name,
        "dims": ds[new_var_name].dims,
        "shape": ds[new_var_name].shape,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else [],
        "first_5_dates": [str(d) for d in ds["time"].values[:5]] if 'time' in ds[new_var_name].dims else None
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print("\nMinimum calculation summary:")
        print(f"Dimensions reduced: {dims_to_reduce}")
        if period_label:
            print(f"Time period: {period_label.lstrip('_')}")
        else:
            print("Time period: full range")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds


# ---------------- Percentile ----------------
#   Percentile value of a variable (along any dimension), with optional period selection, and explicit naming of the new variable in the dataset

def percentile_value_flexible(ds, var_name_gui=None, q_gui=None, dims_to_reduce_gui=None, start_input_gui=None, end_input_gui=None):
    vars_list = list(ds.data_vars)

    is_gui = any(p is not None for p in [var_name_gui, q_gui, dims_to_reduce_gui, start_input_gui, end_input_gui])
    
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

    if dims_to_reduce_gui is not None:
        dims_to_reduce = dims_to_reduce_gui
    elif is_gui:
        dims_to_reduce = available_dims
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
    active_da, period_label = apply_time_selection(ds, active_da, dims_to_reduce, start_input_gui, end_input_gui, is_gui=is_gui)

    # Percentile calculation
    if not is_gui:
        print(f"\nCalculating {int(q*100)}th percentile across: {dims_to_reduce}...")
    # Note: quantile() in xarray uses the 0-1 scale for q
    # FIX dask pour percentile
    active_da = active_da.chunk({dim: -1 for dim in dims_to_reduce})

    perc_val = active_da.quantile(q, dim=dims_to_reduce, skipna=True)

    # Variable naming
    dims_suffix = f"_perc{int(q*100)}_on_" + "_".join(dims_to_reduce)
    new_var_name = f"perc{int(q*100)}_{var_name}{dims_suffix}{period_label}"

    # Add to Dataset
    if 'time' in dims_to_reduce and 'time' in ds.dims:
        # broadcast perc_val to have the same time dimension as ds for consistent handling in future operations
        perc_val, _ = xr.broadcast(perc_val, ds['time'])

    ds[new_var_name] = perc_val

    # Summary
    summary = {
        "method": f"Percentile {int(q*100)}%",
        "var_name": var_name,
        "reduced_dims": dims_to_reduce,
        "period": period_label.lstrip('_') if period_label else "full range",
        "new_var": new_var_name,
        "dims": ds[new_var_name].dims,
        "shape": ds[new_var_name].shape,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else [],
        "first_5_dates": [str(d) for d in ds["time"].values[:5]] if 'time' in ds[new_var_name].dims else None
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print(f"\nPercentile ({int(q*100)}th) calculation summary:")
        print(f"Dimensions reduced: {dims_to_reduce}")
        if period_label:
            print(f"Time period: {period_label.lstrip('_')}")
        else:
            print("Time period: full range")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds


# ---------------- Rolling Mean ----------------
#   Rolling mean value of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset

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

            start_date, end_date = ask_date(ds, start_input_gui, end_input_gui, is_gui=is_gui)

            if start_date or end_date:
                temp_da = active_da.sel(time=slice(start_date, end_date))
            else:
                temp_da = active_da

            # verify that data exists
            if temp_da.time.size == 0:
                print("No data available in this time range. Please choose another period.")
                if is_gui:
                    break  # Break if using GUI because we cannot prompt again
                continue

            # selection is valid
            active_da = temp_da

            if start_date or end_date:
                s = start_date.date() if start_date else "start"
                e = end_date.date() if end_date else "end"
                period_label = f"_{s}_{e}"

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

    # Summary
    summary = {
        "method": f"Rolling Mean (w={window})",
        "var_name": var_name,
        "period": period_label.lstrip('_') if period_label else "full range",
        "new_var": new_var_name,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print(f"\nRolling Mean (window={window}) calculation summary:")
        if period_label:
            print(f"Time period: {period_label.lstrip('_')}")
        else:
            print("Time period: full range")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds


# ---------------- Interannual Monthly Averages ----------------
#   Interannual grouping by month of a variable (along time), with optional period selection, and explicit naming of the new variable in the dataset

def monthly_interannual_average_xr(ds, var_name_gui=None, time_dim_gui=None):
    vars_list = list(ds.data_vars)
    is_gui = any(p is not None for p in [var_name_gui, time_dim_gui])

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
    elif is_gui:
        # Default to 'time' or first time-like dimension
        time_dim = next((d for d in active_da.dims if "time" in d.lower()), active_da.dims[0])
    else:
        # list of dimensions to identify the time dimension
        dims_list = list(active_da.dims)
        print(f"\nDimensions for '{var_name}':")
        for i, d in enumerate(dims_list):
            # Utiliser active_da.sizes[d] au lieu de active_da.dims[d]
            print(f" [{i}] {d} ({active_da.sizes[d]} values)")
        while True:
            try:
                dim_idx = int(input("Which time dimension do you want to use for grouping ? "))
                time_dim = dims_list[dim_idx]
                break
            except (ValueError, IndexError):
                print("Invalid index. Please choose an existing dimension.")

    # Calculation of monthly means (1 to 12)
    if not is_gui:
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

    # Summary
    summary = {
        "method": "Monthly Interannual Average",
        "var_name": var_name,
        "grouped_by": time_dim,
        "new_var": new_var_name,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_stat_summary'] = summary

    if not is_gui:
        print("\nInterannual monthly average summary:")
        print(f"Grouped by : {time_dim}")
        print(f"New Variable added: '{new_var_name}'")
        print(f"Dimensions: {list(ds[new_var_name].dims)}")
        print(f"Shape: {ds[new_var_name].shape}")

    return ds