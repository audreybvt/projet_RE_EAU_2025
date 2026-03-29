import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from utils_xr import show_info

# ---------------- NetCDF Formatting ----------------

def handle_spatial_dimensions(ds, filename="dataset", spatial_gui: dict = None, log_func=None):
    """
    Handles the spatial dimensions of the dataset.
    Two options: (1) Keep everything, (2) Select a single entity (point/station).
    
    Parameters:
        ds: xarray.Dataset to process
        filename: filename for display (optional)
        spatial_gui: dict – keys 'choice' (1=keep all, 2=select by index) and 'index' (int, for choice=2)
                     If None, falls back to interactive terminal input.
        log_func: optional logging function for GUI
    """
    # Identify potential spatial dimensions
    spatial_dim = None

    # Look for point dimensions (piezometers, stations, etc.)
    point_dims = ['piezometre', 'station', 'stations', 'site', 'sites', 'location', 'locations']
    for dim in point_dims:
        if dim in ds.dims:
            spatial_dim = dim
            break

    # If no point dimension, look for grids
    if not spatial_dim:
        grid_dims = ['latitude', 'longitude', 'lat', 'lon', 'x', 'y']
        for dim in grid_dims:
            if dim in ds.dims:
                spatial_dim = dim
                break

    # If no spatial dimension detected, return the dataset as is
    if not spatial_dim:
        return ds

    is_gui = spatial_gui is not None

    # GUI mode: resolve choice from dict
    if is_gui:
        # 'keep_all' key means keep everything
        if spatial_gui.get('keep_all'):
            return ds
        choice = spatial_gui.get('choice', 1)
    else:
        # Display info (terminal mode only)
        print(f"\n Choice of the spatial dimension for the file : {filename}")
        print("Warning: Make sure to use the same choice across multiple files if applicable.")
        print(f"Spatial dimension detected: '{spatial_dim}' ({len(ds[spatial_dim])} values)")
        print("\nOptions:")
        print("[1] Keep all data")
        print("[2] Select a single entity")

        while True:
            try:
                choice = int(input("Your choice (1-2): ").strip())
                if choice in [1, 2]:
                    break
                print("Invalid choice. Enter 1 or 2.")
            except ValueError:
                print("Please enter a number.")

    # Option 1: Keep everything
    if choice == 1:
        show_info("→ Keeping all data", log_func=log_func)
        return ds

    # Option 2: Select an entity
    else:
        coords = ds.coords[spatial_dim].values

        if is_gui:
            idx = spatial_gui.get('index', 0)
            if 0 <= idx < len(coords):
                selected = coords[idx]
                show_info(f"→ Selection: {selected}", log_func=log_func)
                return ds.sel({spatial_dim: selected})
            else:
                show_info(f"Index {idx} out of bounds, keeping all data.", log_func=log_func)
                return ds
        else:
            print(f"\nAvailable entities in '{spatial_dim}':")
            for i, coord in enumerate(coords[:10]):
                print(f"[{i}] {coord}")
            if len(coords) > 10:
                print(f"... and {len(coords) - 10} others")

            while True:
                try:
                    idx = int(input(f"Index (0-{len(coords)-1}): ").strip())
                    if 0 <= idx < len(coords):
                        selected = coords[idx]
                        print(f"→ Selection: {selected}")
                        return ds.sel({spatial_dim: selected})
                    else:
                        print("Index out of bounds.")
                except ValueError:
                    print("Please enter a number.")

def select_spatial_point(ds, spatial_dims, coords_names, method_gui=None, idx_gui=None, lat_gui=None, lon_gui=None, log_func=None):
    """
    Selects a specific spatial point from the dataset.
    Two methods: (1) Select by index, (2) Select nearest to coordinates.

    Parameters:
        ds: xarray.Dataset
        spatial_dims: dict mapping 'points' or 'grid' to dimension names
        coords_names: dict mapping 'points' or 'grid' to coordinate names
        method_gui: 1 (index) or 2 (coords)
        idx_gui: index for method 1
        lat_gui, lon_gui: coordinates for method 2
        log_func: optional logging function
    """
    is_gui = method_gui is not None

    if not is_gui:
        print("\nSelection of a point/station:")
        print("[1] Select by index")
        print("[2] Select nearest point (by coordinates)")
        
        while True:
            try:
                method = int(input("Method (1-2): ").strip())
                if method in [1, 2]: break
            except ValueError: pass

    else:
        method = method_gui

    # Option 1: Index
    if method == 1:
        # Determine the dimension to index into
        if 'points' in spatial_dims:
            dim = spatial_dims['points'][0]
        elif 'grid' in spatial_dims:
            dim = spatial_dims['grid'][0] # Fallback
        else:
            return ds

        coords = ds.coords[dim].values
        
        if not is_gui:
            print(f"Available indices (0-{len(coords)-1}):")
            for i, c in enumerate(coords[:10]): print(f"[{i}] {c}")
            if len(coords) > 10: print(f"... and {len(coords)-10} others")
            
            while True:
                try:
                    idx = int(input(f"Index: ").strip())
                    if 0 <= idx < len(coords): break
                except ValueError: pass
        else:
            idx = idx_gui if idx_gui is not None else 0
            if not (0 <= idx < len(coords)):
                show_info(f"Warning: Index {idx} out of bounds. Using 0.", log_func=log_func)
                idx = 0

        selected = ds.isel({dim: idx})
        show_info(f"→ Selected point at index {idx}: {coords[idx]}", log_func=log_func)
        return selected

    # Option 2: Coordinates (Nearest)
    else:
        if 'grid' in spatial_dims:
            lat_dim, lon_dim = spatial_dims['grid'][0], spatial_dims['grid'][1]
            lat_coord, lon_coord = coords_names['grid'][0], coords_names['grid'][1]
        else:
            # Try to find lat/lon in points if grid not specified
            lat_coord = next((c for c in ['latitude', 'lat'] if c in ds.coords), None)
            lon_coord = next((c for c in ['longitude', 'lon'] if c in ds.coords), None)
            if not (lat_coord and lon_coord):
                show_info("Error: Latitude/Longitude coordinates not found.", log_func=log_func)
                return ds
            lat_dim, lon_dim = lat_coord, lon_coord

        if not is_gui:
            try:
                lat_val = float(input("Target Latitude: ").strip())
                lon_val = float(input("Target Longitude: ").strip())
            except ValueError:
                return ds
        else:
            lat_val = lat_gui if lat_gui is not None else 0.0
            lon_val = lon_gui if lon_gui is not None else 0.0

        selected = ds.sel({lat_coord: lat_val, lon_coord: lon_val}, method='nearest')
        
        # Determine labels for display
        sel_lat = float(selected[lat_coord].values) if lat_coord in selected.coords else lat_val
        sel_lon = float(selected[lon_coord].values) if lon_coord in selected.coords else lon_val
        show_info(f"→ Selected nearest point: Lat {sel_lat:.4f}, Lon {sel_lon:.4f}", log_func=log_func)
        
        return selected


def select_spatial_region(ds, grid_dims, coord_names, region_gui=None, log_func=None):
    """
    Selects a rectangular region from a grid.

    Parameters:
        ds: xarray.Dataset
        grid_dims: list [lat_dim, lon_dim]
        coord_names: list [lat_coord, lon_coord]
        region_gui: dict {'lat_min', 'lat_max', 'lon_min', 'lon_max'}
        log_func: optional logging function
    """
    lat_coord, lon_coord = coord_names[0], coord_names[1]
    is_gui = region_gui is not None

    if not is_gui:
        print("\nSelection of a region:")
        try:
            lat_min = float(input(f"Lat min (default {ds[lat_coord].min().values}): ") or ds[lat_coord].min().values)
            lat_max = float(input(f"Lat max (default {ds[lat_coord].max().values}): ") or ds[lat_coord].max().values)
            lon_min = float(input(f"Lon min (default {ds[lon_coord].min().values}): ") or ds[lon_coord].min().values)
            lon_max = float(input(f"Lon max (default {ds[lon_coord].max().values}): ") or ds[lon_coord].max().values)
        except ValueError:
            return ds
    else:
        lat_min = region_gui.get('lat_min', ds[lat_coord].min().values)
        lat_max = region_gui.get('lat_max', ds[lat_coord].max().values)
        lon_min = region_gui.get('lon_min', ds[lon_coord].min().values)
        lon_max = region_gui.get('lon_max', ds[lon_coord].max().values)

    selected = ds.sel({
        lat_coord: slice(min(lat_min, lat_max), max(lat_min, lat_max)),
        lon_coord: slice(min(lon_min, lon_max), max(lon_min, lon_max))
    })

    show_info(f"→ Selected region: Lat [{lat_min}, {lat_max}], Lon [{lon_min}, {lon_max}]", log_func=log_func)
    show_info(f"  New shape: {dict(selected.sizes)}", log_func=log_func)
    
    return selected


def load_multiple_datasets(paths, spatial_gui: dict = None):
    """
    Load multiple NetCDF files and add model and scenario dimensions
    before combining them.
    Uses dask to avoid memory issues.

    Parameters:
        paths: list of file paths
        spatial_gui: dict with 'choice' (1 or 2) and optionally 'index' (int)
    """

    datasets = []

    for path in paths:

        # Open without automatic decoding (by specifying the engine explicitly)
        try:
            ds = xr.open_dataset(path, decode_cf=False, engine='netcdf4')
        except Exception:
            # Fallback: try h5netcdf
            try:
                ds = xr.open_dataset(path, decode_cf=False, engine='h5netcdf')
            except Exception as e:
                print(f"Error opening file {path}: {e}")
                continue

        # Manual time decoding only
        if 'time' in ds:
            ds = ds.assign_coords(time=xr.coding.times.decode_cf_datetime(
                ds['time'], ds['time'].attrs.get('units', 'days since 1900-01-01'),
                calendar=ds['time'].attrs.get('calendar', 'standard')
            ))

        # Spatial dimension handling
        filename = Path(path).name  # Extract filename
        if spatial_gui is not None:
            ds = handle_spatial_dimensions(
                ds,
                filename=filename,
                spatial_gui=spatial_gui
            )
        else:
            ds = handle_spatial_dimensions(ds, filename=filename)

        #Create attributes for model and scenario
        # retrieve metadata if they exist
        scenario = ds.attrs.get("experiment_id", "unknown")
        gcm = ds.attrs.get("driving_model_id", "unknown")
        rcm = ds.attrs.get("model_id", "unknown")
        bc = ds.attrs.get("bc_method_id", "unknown")
        hy_model = ds.attrs.get("hy_model_id", "unknown")


        if "unknown" in (gcm, rcm, bc, hy_model, scenario) :
            print("The file format is not appropriate")
            return

        # Create a single "model_chain" dimension
        model_chain = f"{gcm}-{rcm}-{bc}-{hy_model}"

        # Extend the dataset with the two new dimensions
        ds = ds.expand_dims({
            "scenario": [scenario],
            "model": [model_chain]
        })

        # Convert to dask with intelligent chunking adapted to available dimensions
        chunk_dict = {}

        # Priority to temporal chunking if available
        if 'time' in ds.dims:
            chunk_dict['time'] = min(1000, ds.sizes['time'])

        # Chunking of spatial/point dimensions
        spatial_dims = ['piezometre', 'latitude', 'longitude', 'lat', 'lon', 'x', 'y']
        for dim in spatial_dims:
            if dim in ds.dims and ds.sizes[dim] > 1:
                chunk_dict[dim] = min(100, ds.sizes[dim])
                break  # Only one spatial chunking to avoid overload

        # If no known dimension, chunk the largest non-scalar dimension
        if not chunk_dict:
            for dim, size in ds.sizes.items():
                if size > 1 and dim not in ['scenario', 'model']:  # Avoid new dimensions
                    chunk_dict[dim] = min(1000, size)
                    break

        # Apply chunking if dimensions were found
        if chunk_dict:
            ds = ds.chunk(chunk_dict)
        else:
            # Fallback: automatic chunking
            ds = ds.chunk('auto')

        datasets.append(ds)

    # combination with dask
    combined = xr.combine_by_coords(datasets, combine_attrs='drop', join='outer', data_vars='all')
    print(f"\nCombination completed. Dataset: {combined}")
    return combined


# ---------------- CSV Formatting ----------------

def clean_dataframe(df):
    """
    Clean a DataFrame by detecting and converting date columns.

    Attempts to identify date columns by name first, then by automatic detection
    of columns that can be converted to datetime with high success rate.

    Parameters:
        df: pandas.DataFrame to clean

    Returns:
        tuple: (cleaned_df, date_column_name)
            - cleaned_df: DataFrame with date column converted to datetime
            - date_column_name: Name of the detected date column, or None
    """

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

def csv_to_xarray(filepath, skip_n_gui: int = None):
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
    if skip_n_gui is not None:
        skip_n = skip_n_gui
    else:
        while True:
            try:
                skip_n = int(input("How many metadata lines (before column names)? "))
                if skip_n < 0:
                    print("Please enter a positive number.")
                    continue
                break
            except ValueError:
                print("Please enter a valid integer.")

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


# ---------------- Excel Formatting ----------------

def excel_to_long_csv(input_excel_path="input/excel/donnees_sandra_feuille2_test.xlsx", output_csv_path="input/CSV/donnees_longues.csv"):
    """
    Convert an Excel file with a dual header (2-level MultiIndex) to a long CSV.

    This mirrors the previous standalone excel_to_csv.py script in a reusable function.

    Args:
        input_excel_path: source Excel file path.
        output_csv_path: destination CSV file path.

    Returns:
        pandas.DataFrame: long-format data (with 'Date', 'model', and value columns).
    """

    # Load Excel with the two header rows
    df = pd.read_excel(input_excel_path, header=[2, 3])

    # Fix Date column name for MultiIndex
    new_cols = list(df.columns)
    if "Date" in str(new_cols[0]) or "Unnamed" in str(new_cols[0]):
        new_cols[0] = ("Date", "")
    df.columns = pd.MultiIndex.from_tuples(new_cols)

    # Convert the Date column to datetime
    df[("Date", "")] = pd.to_datetime(
        df[("Date", "")],
        dayfirst=True,
        errors="coerce"
    )

    # Convert to long format by stacking the first level (models)
    df_long = (
        df
        .set_index(("Date", ""))
        .stack(level=0)
        .reset_index()
        .rename(columns={"level_1": "model"})
    )

    # Clean up the columns
    df_long.columns.name = None
    df_long = df_long.rename(columns={("Date", ""): "Date"})

    # Write CSV
    df_long.to_csv(output_csv_path, sep=";", index=False)
    print(f"Long-format CSV written: {output_csv_path}")

    return df_long
