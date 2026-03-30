# Hydrological Indicators Calculation Functions
import numpy as np
import pandas as pd

# ---------------- Set Up Functions ----------------

def categorical_filter(ds, standard_dims, filter_choice_gui=None, dict_filters_gui=None):
    """
    Allows the operator to select a specific category (such as one model) to which 
    the indicator will be applied, if there are multiple. 

    Args:
        ds: The input Xarray Dataset.
        standard_dims: List of dimensions to skip (e.g., ['time', 'lat', 'lon']).
        filter_choice_gui: Optional GUI parameter 'y' or 'n'
        dict_filters_gui: Optional GUI dict for filters.

    Returns:
        active_ds: The Dataset after applying filters.
        selections_made: A list of strings recording which filters were used.
    """
    coords_list = list(ds.coords)
    # Identify extra dimensions that actually exist in the dimensions list
    extra_dims = [c for c in coords_list if c in ds.dims and c not in standard_dims]
    active_ds = ds.copy()
    selections_made = []

    if extra_dims:
        # Step 1: Identify dimensions requiring a manual choice
        selectable_dims = [d for d in extra_dims if ds.dims[d] > 1]
        
        # Step 2: Auto-filter single-value dimensions to clean up the data
        for d in extra_dims:
            if ds.dims[d] == 1:
                val = ds[d].values[0]
                active_ds = active_ds.sel({d: val})
                selections_made.append(f"{d}: {val} (auto)")

        if dict_filters_gui is not None:
            for k, v in dict_filters_gui.items():
                if k in selectable_dims:
                    active_ds = active_ds.sel({k: v})
                    selections_made.append(f"{k}: {v}")
            return active_ds, selections_made

        # Step 3: Interactive selection loop
        while selectable_dims:
            print("\nAvailable categories with multiple values:")
            for i, dim in enumerate(selectable_dims):
                print(f" [{i}] {dim} ({ds.dims[dim]} values)")
            

            while True:
                choice = input("\nDo you want to filter a specific category? (y/n): ").lower().strip()
                if choice in ["y", "n"]:
                    break
                print("Please enter 'y' or 'n'.")
            if choice != 'y':
                print("-> Indicator will be applied to all remaining categories.")
                break
            
        
            # Select dimension
            while True:
                dim_idx_input = input(f"Which category? Index (0-{len(selectable_dims)-1}): ").strip()
                if not dim_idx_input.isdigit(): 
                    print("Please enter a valid integer.")
                    continue
                dim_idx = int(dim_idx_input)
                if dim_idx < 0 or dim_idx >= len(selectable_dims):
                    print(f"Index out of range. Choose between 0 and {len(selectable_dims)-1}.")
                    continue
                dim_name = selectable_dims[dim_idx]
                break

            # Select value
            vals = ds[dim_name].values
            print(f"\nValues in '{dim_name}':")
            for j, v in enumerate(vals):
                print(f"  [{j}] {v}")

            while True:
                val_idx_input = input(f"Select value index for {dim_name}: ").strip()
                if not val_idx_input.isdigit():
                    print("Please enter a valid integer.")
                    continue
                val_idx = int(val_idx_input)
                if val_idx < 0 or val_idx >= len(vals):
                    print(f"Index out of range. Choose between 0 and {len(vals)-1}.")
                    continue
                break

            # Apply selection
            active_ds = active_ds.sel({dim_name: vals[val_idx]})
            selections_made.append(f"{dim_name}: {vals[val_idx]}")
            # Remove from list so it's not offered again
            selectable_dims.pop(dim_idx)
            print(f"-> Filter applied: {dim_name} = {vals[val_idx]}")

                
    return active_ds, selections_made

def get_time_freq(unite_gui=None, nb_gui=None):
    """
    Allows the operator to define the time frequency (such as 3 months) 
    over which the indicator will be calculated.

    Args:
        unite_gui: Optional GUI parameter 'd', 'm', or 'y'
        nb_gui: Optional int step

    Returns:
        frequence: The Xarray-compatible frequency string (e.g., '3MS').
        unite: The unit chosen (d, m, or y).
        nb: The numerical step value.
        label_unite: The plural label for the unit (e.g., 'months').
    """ 
    freq_map = {"d": "D", "m": "MS", "y": "AS"}
    
    if unite_gui is not None and nb_gui is not None:
        unite = unite_gui.lower()
        nb = int(nb_gui)
        label = {"d": "days", "m": "months", "y": "years"}.get(unite, "unknown")
        return f"{nb}{freq_map[unite]}", unite, nb, label
        
    while True:
        try:
            print("\nTime Period Configuration")
            unite = input("Choose time unit (d: days, m: months, y: years): ").lower().strip()
            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue
            
            label = {"d": "days", "m": "months", "y": "years"}[unite]
            nb_input = input(f"Enter time step (e.g., '3' to get the mean every 3 {label}): ").strip()
            if not nb_input:
                continue
            nb = int(nb_input)
            if nb <= 0: continue
            
            return f"{nb}{freq_map[unite]}", unite, nb, label
        except ValueError:
            print("Please enter a valid integer.")


# ---------------- Soil Water Balance Index ----------------

def soil_water_balance_index(ds, dict_filters_gui=None, var_p_gui=None, var_etr_gui=None, var_dr_gui=None):
    """
    Return the Soil Water Balance Index with the formula :
    Index = P - ETR - ΔR, where P is precipitation, ETR is actual evapotranspiration, and ΔR is the change in storage.

    Args:
        ds: Input xarray Dataset with P, ETR, and ΔR variables.
        dict_filters_gui: Dict for categorical filters.
        var_p_gui: Variable name for Precipitation.
        var_etr_gui: Variable name for ETR.
        var_dr_gui: Variable name for Storage Change.
    Returns:
        ds: Original dataset with added Soil_Water_Balance_Index variable.
    """
    #Possibility to filter categorical dimensions (scenarios, models...) if they exist
    coords_list = list(ds.coords)
    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    extra_dims = [c for c in coords_list if c not in standard_dims]

    active_ds = ds.copy()
    selections_made = []

    if dict_filters_gui is not None:
        for k, v in dict_filters_gui.items():
            if k in extra_dims:
                active_ds = active_ds.sel({k: v})
                selections_made.append(f"{k}: {v}")
    elif extra_dims:
        print("Categorical Filtering Phase")
        
        while True:
            print("Available categories:")
            for i, dim in enumerate(extra_dims):
                count = ds.dims[dim]
                print(f" [{i}] {dim} ({count} value(s) available)")
            
            while True:
                filter_choice = input("Do you want to filter a specific category? (y/n): ").lower().strip()
                if filter_choice in ['y', 'n']:
                    break
                print("Invalid input. Please enter 'y' or 'n'.")

            if filter_choice == 'n':
                print("-> Calculation will proceed without filtering all dimensions.")
                break
            
            while True:
                try:
                    dim_idx = int(input("Index of the dimension to filter: ").strip())
                    dim_name = extra_dims[dim_idx]
                    break
                except (ValueError, IndexError):
                    print(f"Invalid index. Please choose between 0 and {len(extra_dims)-1}.")

            available_values = ds[dim_name].values
            print(f"Values in '{dim_name}':")
            for j, val in enumerate(available_values):
                print(f"  [{j}] {val}")
            
            while True:
                try:
                    val_idx = int(input(f"Select index for {dim_name}: ").strip())
                    selected_val = available_values[val_idx]
                    break
                except (ValueError, IndexError):
                    print(f"Invalid index.")

            active_ds = active_ds.sel({dim_name: selected_val})
            selections_made.append(f"{dim_name}: {selected_val}")
            print(f"-> SUCCESS: Data subset to {dim_name} = {selected_val}")
            
            if len(selections_made) == len(extra_dims):
                break

    # Variable selection for index calculation
    if var_p_gui is not None and var_etr_gui is not None and var_dr_gui is not None:
        var_p, var_etr, var_dr = var_p_gui, var_etr_gui, var_dr_gui
    else:
        print(" Variable Selection ")
        vars_list = list(active_ds.data_vars)
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")

        while True:
            try:
                idx_p = int(input("Index of Precipitation (P): "))
                idx_etr = int(input("Index of Actual Evapotranspiration (ETR): "))
                idx_dr = int(input("Index of Storage Change (ΔR): "))
                var_p, var_etr, var_dr = vars_list[idx_p], vars_list[idx_etr], vars_list[idx_dr]
                break
            except (ValueError, IndexError):
                print("Invalid variable indices. Try again.")

    # Index Calculation: Index = P - ETR - ΔR
    new_var_name = "Soil_Water_Balance_Index"
    try:
        # Vectorized calculation across all active dimensions
        index_result = active_ds[var_p] - active_ds[var_etr] - active_ds[var_dr]
        
        # Save to main dataset
        ds[new_var_name] = index_result
        ds[new_var_name].attrs['description'] = f"Soil Water Balance Index ({var_p} - {var_etr} - {var_dr})"
        
    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary of results
    final_shape = ds[new_var_name].shape
    final_dims = ds[new_var_name].dims
    mean_val = float(ds[new_var_name].mean(skipna=True))
    
    # Selection Log
    if selections_made:
        print("Selection:")
        for item in selections_made:
            print(f" - {item}")
    else:
        print("Selection: none.")

    # Shape and Dimension explanation
    print(f"New Variable: '{new_var_name}'")
    print(f"Dimensions: {final_dims}")
    print(f"Shape: {final_shape}")
    
    # Global Mean (Spatial + Temporal + Categorical)
    print(f"Global Mean on the selection: {mean_val:.2f}")

    # Summary for GUI
    summary = {
        "method": "Soil Water Balance Index (IPS)",
        "var_name": new_var_name,
        "mean_val": mean_val,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    # Reminder for visualization
    if len([d for d in final_shape if d > 1]) > 1:
         print(f"Note: The indicator was calculated for each {final_dims}")
    
    return ds
    # Note: If the result is multidimensional,
    # the operator must select the specific dimension they wish to visualize. 
    # Otherwise, the system will average across all remaining dimensions. 
    # For example, if multiple models exist 
    # and the operator chooses to view the IPS over time at 'Piezometer 0', 
    # the values will be averaged across all models to produce a single time series.


# ---------------- Standardised Piezometric Level Indicator ----------------

def SPLI(ds):
    """
    Return the Standardised Piezometric Level Indicator (SPLI) for a chosen period.

    Args:
        ds: Input xarray Dataset with piezometric level variable.
    """
    print("Standardised Piezometric Level Indicator (SPLI) is not yet implemented.")
    return ds


# ---------------- Qmean/QA ----------------
#   Mean discharge over a chosen period

def Qmean(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, unite_gui=None, nb_gui=None):
    """
    Return the mean flow rate (Qmean) for a chosen period.

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and mean discharge variable.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time coordinate selection
    if time_coord_gui is not None:
        time_coord = time_coord_gui
    else:
        coords_list = list(ds.coords)
        print("\nAvailable coordinates for time:")
        for i, coord in enumerate(coords_list):
            print(f" [{i}] {coord}")
    
        while True:
            try:
                idx_t = int(input("Index of Date/Time coordinate: ").strip())
                time_coord = coords_list[idx_t]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    if var_q_gui is not None:
        var_q = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("\nAvailable variables (for Discharge):")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")
        
        while True:
            try:
                idx_q = int(input("Index of Discharge variable (Q): ").strip())
                var_q = vars_list[idx_q]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

    # Calculation
    new_time_dim = f"{time_coord}_Group_{nb}{unite}"
    new_var_name = f"Qmean_{nb}{unite}_{var_q}"

    try:
        print("Calculation Phase")
        resampled_da = active_ds[var_q].resample({time_coord: frequence}).mean(skipna=True)
        resampled_da = resampled_da.rename({time_coord: new_time_dim})
        
        ds[new_var_name] = resampled_da
        ds[new_var_name].attrs['description'] = f"Mean discharge over {nb} {label_unite} for {var_q}"
    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary
    print("Qmean calculation summary:")
    if selections_made:
        print("Selection:")
        for item in selections_made: print(f" - {item}")
    else:
        print("Selection: none (calculated across all categories).")

    print(f"New Temporal Coordinate added: '{new_time_dim}'")
    print(f"New Variable added: '{new_var_name}'")
    print(f"Dimensions: {ds[new_var_name].dims}")
    print(f"Shape: {ds[new_var_name].shape}")
    
    try:
        mean_val = float(ds[new_var_name].mean(skipna=True))
        print(f"Global Mean on the selection: {mean_val:.2f}")
    except:
        pass
    
    # Preview
    print("Variable Preview (First 5 values):")
    print(ds[new_var_name].values[:5])
    
    # Summary for GUI
    summary = {
        "method": "Mean Discharge (Qmean)",
        "var_name": new_var_name,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    # Summary for GUI
    summary = {
        "method": "Mean Discharge (Qmean)",
        "var_name": new_var_name,
        "mean_val": mean_val,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# ---------------- Q90/Q95 ----------------
#   High-flow Indicators (flow exceeded only 10% or 5% of the time)

def Q90_95(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, unite_gui=None, nb_gui=None):
    """
    Return the flow rates exceeded 90% and 95% of the time for a chosen period (xarray version).

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and Q90/Q95 variables.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering (reusing your existing helper)
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time coordinate selection
    if time_coord_gui is not None:
        time_coord = time_coord_gui
    else:
        coords_list = list(ds.coords)
        print("\nAvailable coordinates for time:")
        for i, coord in enumerate(coords_list):
            print(f" [{i}] {coord}")
        
        while True:
            try:
                idx_t = int(input("Index of Date/Time coordinate: ").strip())
                time_coord = coords_list[idx_t]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    if var_q_gui is not None:
        var_q = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("\nAvailable variables (for Discharge):")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")
        
        while True:
            try:
                idx_q = int(input("Index of Discharge variable (Q): ").strip())
                var_q = vars_list[idx_q]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config (reusing your get_time_freq function)
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

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

    # Summary for GUI
    summary = {
        "method": "Q90/Q95",
        "vars": [new_var_q90, new_var_q95],
        "first_5_vals": [float(v) for v in ds[new_var_q90].values.flatten()[:5]] if ds[new_var_q90].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    # Previews
    print(f"\nQ90 Preview (First 5 values):")
    print(ds[new_var_q90].values[:5])
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# ---------------- VCN10 ----------------
#   Minimum 10-day consecutive mean flow

def VCN10(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, unite_gui=None, nb_gui=None):
    """
    Return the minimum 10-day consecutive mean flow (VCN10) for a chosen period (xarray version).

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and VCN10 variable.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering (reusing your existing helper)
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time coordinate selection
    if time_coord_gui is not None:
        time_coord = time_coord_gui
    else:
        coords_list = list(ds.coords)
        print("\nAvailable coordinates for time:")
        for i, coord in enumerate(coords_list):
            print(f" [{i}] {coord}")
        
        while True:
            try:
                idx_t = int(input("Index of Date/Time coordinate: ").strip())
                time_coord = coords_list[idx_t]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    if var_q_gui is not None:
        var_q = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("\nAvailable variables (for Discharge):")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")
        
        while True:
            try:
                idx_q = int(input("Index of Discharge variable (Q): ").strip())
                var_q = vars_list[idx_q]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config (reusing your get_time_freq function)
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

    # Naming configuration
    new_time_dim = f"{time_coord}_Group_{nb}{unite}"
    new_var_name = f"VCN10_{nb}{unite}_{var_q}"

    try:
        print(f"Calculation Phase: Finding 10-day minimum mean within every {nb} {label_unite}...")
        
        # 1. Calculate the 10-day rolling mean
        # We assume the time step of the data is daily for VCN10 to make sense
        rolling_10d = active_ds[var_q].rolling({time_coord: 10}, center=False).mean()

        # 2. Resample to find the minimum of those 10-day means over the period
        resampled_vcn = rolling_10d.resample({time_coord: frequence}).min(skipna=True)
        
        # 3. Rename the time dimension to the grouped version
        resampled_vcn = resampled_vcn.rename({time_coord: new_time_dim})

        # Add to main dataset
        ds[new_var_name] = resampled_vcn
        ds[new_var_name].attrs['description'] = f"VCN10 (Min 10-day consecutive mean) over {nb} {label_unite} for {var_q}"

    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary
    print("\nVCN10 calculation summary:")
    if selections_made:
        print("Selection:")
        for item in selections_made: print(f" - {item}")
    else:
        print("Selection: none (calculated across all categories).")

    print(f"New Temporal Coordinate added: '{new_time_dim}'")
    print(f"New Variable added: '{new_var_name}'")
    print(f"Dimensions: {ds[new_var_name].dims}")
    print(f"Shape: {ds[new_var_name].shape}")
    
    # Previews
    print(f"\nVCN10 Preview (First 5 values):")
    print(ds[new_var_name].values[:5])

    # Summary for GUI
    summary = {
        "method": "Minimum 10-day mean (VCN10)",
        "var_name": new_var_name,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# ---------------- Q10/Q05 ----------------
#   Low flow indicators (flow exceeded only 10% or 5% of the time)

def Q10_05(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, unite_gui=None, nb_gui=None):
    """
    Return the flow rates exceeded 10% and 5% of the time for a chosen period (xarray version).

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and Q10/Q05 variables.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time coordinate selection
    if time_coord_gui is not None:
        time_coord = time_coord_gui
    else:
        coords_list = list(ds.coords)
        print("\nAvailable coordinates for time:")
        for i, coord in enumerate(coords_list):
            print(f" [{i}] {coord}")
        
        while True:
            try:
                idx_t = int(input("Index of Date/Time coordinate: ").strip())
                time_coord = coords_list[idx_t]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    if var_q_gui is not None:
        var_q = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("\nAvailable variables (for Discharge):")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")
        
        while True:
            try:
                idx_q = int(input("Index of Discharge variable (Q): ").strip())
                var_q = vars_list[idx_q]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

    # Naming configuration
    new_time_dim = f"{time_coord}_Group_{nb}{unite}"
    new_var_q10 = f"Q10_{nb}{unite}_{var_q}"
    new_var_q05 = f"Q05_{nb}{unite}_{var_q}"

    try:
        print("Calculation Phase (High-flow Quantiles)")
        # Note: Q10 is the 0.90 quantile (flow exceeded 10% of the time)
        # Note: Q05 is the 0.95 quantile (flow exceeded 5% of the time)
        
        resampled_group = active_ds[var_q].resample({time_coord: frequence})
        
        # Calculate Q10 (0.90 quantile)
        da_q10 = resampled_group.quantile(0.90, skipna=True).drop_vars('quantile')
        da_q10 = da_q10.rename({time_coord: new_time_dim})
        
        # Calculate Q05 (0.95 quantile)
        da_q05 = resampled_group.quantile(0.95, skipna=True).drop_vars('quantile')
        da_q05 = da_q05.rename({time_coord: new_time_dim})

        # Add to Dataset
        ds[new_var_q10] = da_q10
        ds[new_var_q10].attrs['description'] = f"Q10 (flow exceeded 10% of time) over {nb} {label_unite} for {var_q}"
        
        ds[new_var_q05] = da_q05
        ds[new_var_q05].attrs['description'] = f"Q05 (flow exceeded 5% of time) over {nb} {label_unite} for {var_q}"

    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary
    print("\nQ10/Q05 calculation summary:")
    if selections_made:
        print("Selection:")
        for item in selections_made: print(f" - {item}")
    else:
        print("Selection: none (calculated across all categories).")

    print(f"New Temporal Coordinate added: '{new_time_dim}'")
    print(f"New Variables added: '{new_var_q10}' and '{new_var_q05}'")
    print(f"Dimensions: {ds[new_var_q10].dims}")
    print(f"Shape: {ds[new_var_q10].shape}")

    # Summary for GUI
    summary = {
        "method": "Q10/Q05 (Low flows)",
        "vars": [new_var_q10, new_var_q05],
        "first_5_vals": [float(v) for v in ds[new_var_q10].values.flatten()[:5]] if ds[new_var_q10].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    # Preview Q10
    print(f"\nQ10 Preview (First 5 values):")
    print(ds[new_var_q10].values[:5])
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# ---------------- VCX3 ----------------
#   Maximum 3-day consecutive mean flow

def VCX3(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, unite_gui=None, nb_gui=None):
    """
    Return the maximum 3-day consecutive mean flow (VCX3) for a chosen period (xarray version).

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and VCX3 variable.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time coordinate selection
    if time_coord_gui is not None:
        time_coord = time_coord_gui
    else:
        coords_list = list(ds.coords)
        print("\nAvailable coordinates for time:")
        for i, coord in enumerate(coords_list):
            print(f" [{i}] {coord}")
        
        while True:
            try:
                idx_t = int(input("Index of Date/Time coordinate: ").strip())
                time_coord = coords_list[idx_t]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(coords_list)-1}.")

    # Discharge variable selection
    if var_q_gui is not None:
        var_q = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("\nAvailable variables (for Discharge):")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")
        
        while True:
            try:
                idx_q = int(input("Index of Discharge variable (Q): ").strip())
                var_q = vars_list[idx_q]
                break
            except (ValueError, IndexError):
                print(f"Invalid index. Please choose a number between 0 and {len(vars_list)-1}.")

    # Time config
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

    # Naming configuration
    new_time_dim = f"{time_coord}_Group_{nb}{unite}"
    new_var_name = f"VCX3_{nb}{unite}_{var_q}"

    try:
        print(f"Calculation Phase: Finding 3-day maximum mean within every {nb} {label_unite}...")
        
        # 1. Calculate the 3-day rolling mean
        # We assume daily data. center=False ensures we look at the previous 3 days.
        rolling_3d = active_ds[var_q].rolling({time_coord: 3}, center=False).mean()

        # 2. Resample to find the MAXIMUM of those 3-day means over the period
        resampled_vcx = rolling_3d.resample({time_coord: frequence}).max(skipna=True)
        
        # 3. Rename the time dimension to the grouped version
        resampled_vcx = resampled_vcx.rename({time_coord: new_time_dim})

        # Add to main dataset
        ds[new_var_name] = resampled_vcx
        ds[new_var_name].attrs['description'] = f"VCX3 (Max 3-day consecutive mean) over {nb} {label_unite} for {var_q}"

    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary
    print("\nVCX3 calculation summary:")
    if selections_made:
        print("Selection:")
        for item in selections_made: print(f" - {item}")
    else:
        print("Selection: none (calculated across all categories).")

    print(f"New Temporal Coordinate added: '{new_time_dim}'")
    print(f"New Variable added: '{new_var_name}'")
    print(f"Dimensions: {ds[new_var_name].dims}")
    print(f"Shape: {ds[new_var_name].shape}")
    
    # Previews
    print(f"\nVCX3 Preview (First 5 values):")
    print(ds[new_var_name].values[:5])

    # Summary for GUI
    summary = {
        "method": "Maximum 3-day mean (VCX3)",
        "var_name": new_var_name,
        "first_5_vals": [float(v) for v in ds[new_var_name].values.flatten()[:5]] if ds[new_var_name].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds


# ---------------- Over-threshold Indicator ----------------
#   Count of occurrences above a threshold with tolerance, and episode statistics

def over_threshold(ds, dict_filters_gui=None, time_coord_gui=None, var_q_gui=None, threshold_gui=None, tolerance_gui=None, unite_gui=None, nb_gui=None, start_gui=None, end_gui=None):
    """
    Identify and count exceedance episodes above a threshold with tolerance.
    Computes episode statistics (duration and Peak Over Threshold (POT)).

    Inputs:
    - ds: xarray Dataset containing the variable to analyze.
    - dict_filters_gui: Dict for categorical filters.
    - time_coord_gui: Time coordinate to use.
    - var_q_gui: Variable to analyze.
    - threshold_gui: Absolute threshold value.
    - tolerance_gui: Tolerance percentage (optional).
    - unite_gui: Time unit (e.g., 'm').
    - nb_gui: Time step (e.g., 1).
    - start_gui/end_gui: Start and end dates for the analysis (YYYY-MM-DD strings).
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering
    active_ds, selections_made = categorical_filter(ds, standard_dims, dict_filters_gui=dict_filters_gui)

    # Time Filtering (Period selection)
    t_coord = time_coord_gui or 'time'
    if (start_gui or end_gui) and t_coord in active_ds.dims:
        try:
            start_val = pd.to_datetime(start_gui) if start_gui else active_ds[t_coord].min().values
            end_val   = pd.to_datetime(end_gui)   if end_gui   else active_ds[t_coord].max().values
            active_ds = active_ds.sel({t_coord: slice(start_val, end_val)})
            print(f"-> Period filtering applied: {start_val.date()} to {end_val.date()}")
        except Exception as e:
            print(f"-> Warning: Period filtering failed: {e}")

    # Variable selection
    if var_q_gui is not None:
        var_name = var_q_gui
    else:
        vars_list = list(active_ds.data_vars)
        print("Over-threshold indicator: available variables")
        for i, var in enumerate(vars_list):
            print(f" [{i}] {var}")

        while True:
            try:
                idx = int(input("Index of the variable to analyze: ").strip())
                var_name = vars_list[idx]
                break
            except (ValueError, IndexError):
                print("Invalid index.")

    # Threshold and tolerance inputs
    if threshold_gui is not None:
        threshold = float(threshold_gui)
        tolerance = float(tolerance_gui) if tolerance_gui is not None else 0.0
    else:
        while True:
            try:
                threshold = float(input("Enter threshold value: "))
                break
            except ValueError:
                print("Threshold must be a number.")

        while True:
            try:
                tolerance = float(input("Tolerance percentage (%) around threshold: "))
                if tolerance < 0:
                    print("Tolerance must be positive.")
                    continue
                break
            except ValueError:
                print("Tolerance must be a number.")

    # Time config
    frequence, unite, nb, label_unite = get_time_freq(unite_gui, nb_gui)

    effective_threshold = threshold * (1 + tolerance / 100)
    print(f"Effective threshold used: {effective_threshold:.3f}")

    # Add Visualization Variable (Magnitude)
    new_var_magnitude = f"POT_magnitude_{var_name}"
    ds[new_var_magnitude] = ds[var_name] - effective_threshold
    ds[new_var_magnitude].attrs['description'] = f"Exceedance magnitude above {effective_threshold} for {var_name}"
    
    # Calculation
    new_time_dim = f"{time_coord_gui or 'time'}_Group_{nb}{unite}"
    new_var_name = f"Over_{threshold}_{var_name}"

    try:
        # Group detection could be more complex, but we'll stick to basic counting for now
        # per resampled period if unite provided
        da = active_ds[var_name]
        exceed = (da > effective_threshold).astype(int)
        
        if unite_gui:
            resampled_exceed = exceed.resample({time_coord_gui or 'time': frequence}).sum()
            resampled_exceed = resampled_exceed.rename({time_coord_gui or 'time': new_time_dim})
            ds[new_var_name] = resampled_exceed
            ds[new_var_name].attrs['description'] = f"Count of occurrences above {effective_threshold} for {var_name}"
        
    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Episode Detection Logic (for terminal summary)
    values = da.values.flatten()
    exceed_flat = (values > effective_threshold)

    episodes = []
    pot_values = []
    current_duration = 0
    current_peak = None

    for val, exc in zip(values, exceed_flat):
        if exc and np.isfinite(val):
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

    if current_duration > 0:
        episodes.append(current_duration)
        pot_values.append(current_peak)

    # Summary Statistics Output
    summary = {
        "var_name": var_name,
        "threshold": effective_threshold,
        "total_exceedances": int(np.sum(exceed_flat)),
        "n_episodes": len(episodes),
        "mean_duration": float(np.mean(episodes)) if episodes else 0.0,
        "max_pot": float(np.max(pot_values)) if pot_values else 0.0,
        "first_5_vals": [float(v) for v in ds[new_var_magnitude].values.flatten()[:5]] if ds[new_var_magnitude].size > 0 else []
    }
    ds.attrs['last_ind_summary'] = summary

    print(f"Global Results for {var_name}:")
    if len(episodes) > 0:
        print(f"Total occurrences above threshold: {summary['total_exceedances']}")
        print(f"Number of independent episodes: {summary['n_episodes']}")
        print(f"Mean episode duration: {summary['mean_duration']:.2f} time steps")
        print(f"Highest Peak Over Threshold (POT): {summary['max_pot']:.3f}")
    else:
        print("No exceedance episodes detected.")

    print(f"New variables added: '{new_var_magnitude}' and optionally '{new_var_name}'")
    
    return ds
