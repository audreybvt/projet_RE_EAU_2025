# Hydrological Indicators Calculation Functions
import pandas as pd
import numpy as np
from sympy import true

# set up functions 

def categorical_filter(ds, standard_dims):
    """
    Allows the operator to select a specific category (such as one model) to which 
    the indicator will be applied, if there are multiple. 

    Args:
        ds: The input Xarray Dataset.
        standard_dims: List of dimensions to skip (e.g., ['time', 'lat', 'lon']).

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
            
        
            # Sélection dimension
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

            # Sélection valeur
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




def get_time_freq():
    """
    Allows the operator to define the time frequency (such as 3 months) 
    over which the indicator will be calculated.

    Args:
        None

    Returns:
        frequence: The Xarray-compatible frequency string (e.g., '3MS').
        unite: The unit chosen (d, m, or y).
        nb: The numerical step value.
        label_unite: The plural label for the unit (e.g., 'months').
    """ 
    freq_map = {"d": "D", "m": "MS", "y": "AS"}
    while True:
        try:
            print(" Time Period Configuration ")
            unite = input("Choose time unit (d: days, m: months, y: years): ").lower().strip()
            if unite not in freq_map:
                print("Unit must be d, m, or y.")
                continue
            
            label = {"d": "days", "m": "months", "y": "years"}[unite]
            nb = int(input(f"Enter time step (e.g., '3' to get the mean every 3 {label}): "))
            if nb <= 0: continue
            
            return f"{nb}{freq_map[unite]}", unite, nb, label
        except ValueError:
            print("Please enter a valid integer.")




# IPS (Soil Water Balance Index)
def IPS(ds):
    """
    Return the Index of Soil Precipitation (IPS) based on the water balance.

    Args:
        ds: Input xarray Dataset with P, ETR, and ΔR variables.
    Returns:
        ds: Original dataset with added IPS variable.
    """
    #Possibility to filter categorical dimensions (scenarios, models...) if they exist
    coords_list = list(ds.coords)
    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    extra_dims = [c for c in coords_list if c not in standard_dims]

    active_ds = ds.copy()
    selections_made = []

    if extra_dims:
        print("Categorical Filtering Phase ")
        
        while True:
            print("Available categories:")
            for i, dim in enumerate(extra_dims):
                # Count the number of elements in this dimension
                count = ds.dims[dim]
                print(f" [{i}] {dim} ({count} value(s) available)")
            
            # Choice to filter
            while True:
                filter_choice = input("Do you want to filter a specific category? (y/n): ").lower()
                if filter_choice in ['y', 'n']:
                    break
                print("Invalid input. Please enter 'y' or 'n'.")

            if filter_choice == 'n':
                print("-> Calculation will proceed without filtering all dimensions.")
                print("-> If there are multiple dimensions, the result will be multi-dimensional (e.g. one for each model,scenarios...).")
                break
            
            # Select Dimension
            while True:
                try:
                    dim_idx = int(input("Index of the dimension to filter: "))
                    dim_name = extra_dims[dim_idx]
                    break
                except (ValueError, IndexError):
                    print(f"Invalid index. Please choose between 0 and {len(extra_dims)-1}.")

            # Select Value
            available_values = ds[dim_name].values
            print(f"Values in '{dim_name}':")
            for j, val in enumerate(available_values):
                print(f"  [{j}] {val}")
            
            while True:
                try:
                    val_idx = int(input(f"Select index for {dim_name}: "))
                    selected_val = available_values[val_idx]
                    break
                except (ValueError, IndexError):
                    print(f"Invalid index.")

            # Apply Filter
            active_ds = active_ds.sel({dim_name: selected_val})
            selections_made.append(f"{dim_name}: {selected_val}")
            print(f"-> SUCCESS: Data subset to {dim_name} = {selected_val}")
            
            if len(selections_made) == len(extra_dims):
                break

    # Variable selection for IPS calculation
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

    # IPS Calculation: IPS = P - ETR - ΔR
    new_var_name = "IPS"
    try:
        # Vectorized calculation across all active dimensions
        ips_result = active_ds[var_p] - active_ds[var_etr] - active_ds[var_dr]
        
        # Save to main dataset
        ds[new_var_name] = ips_result
        ds[new_var_name].attrs['description'] = f"IPS ({var_p} - {var_etr} - {var_dr})"
        
    except Exception as e:
        print(f"Calculation Error: {e}")
        return ds

    # Summary of results
    
    print("IPS calculation completed")
    
    # Selection Log
    if selections_made:
        print("Selection:")
        for item in selections_made:
            print(f" - {item}")
    else:
        print("Selection: none.")

    # Shape and Dimension explanation
    final_shape = ds[new_var_name].shape
    final_dims = ds[new_var_name].dims
    print(f"New Variable: '{new_var_name}'")
    print(f"Dimensions: {final_dims}")
    print(f"Shape: {final_shape}")
    
    # Global Mean (Spatial + Temporal + Categorical)
    mean_val = float(ds[new_var_name].mean(skipna=True))
    print(f"Global Mean on the selection): {mean_val:.2f}")
    
    # Reminder for visualization
    if len([d for d in final_shape if d > 1]) > 1:
         print("Note: The IPS was calculated for each {final_dims}")
    return ds
    # Note: If the result is multidimensional,
    # the operator must select the specific dimension they wish to visualize. 
    # Otherwise, the system will average across all remaining dimensions. 
    # For example, if multiple models exist 
    # and the operator chooses to view the IPS over time at 'Piezometer 0', 
    # the values will be averaged across all models to produce a single time series.

# Qmean/QA (mean discharge over a chosen period)

def Qmean(ds):
    """
    Return the mean flow rate (Qmean) for a chosen period.

    Args:
        ds: Input xarray Dataset.
    Returns:
        ds: Original dataset with added resampled time coordinate and mean discharge variable.
    """

    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y']
    
    # Categorical Filtering
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

    # Time config
    frequence, unite, nb, label_unite = get_time_freq()

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
    
    print("Date Preview (First 5 dates):")
    print(ds[new_time_dim].values[:5])
    
    return ds