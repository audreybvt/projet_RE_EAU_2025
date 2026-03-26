from __future__ import annotations

import xarray as xr
import calendar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import matplotlib.dates as mdates
import itertools

# ---------------- Helper Functions ----------------
def subset_time(ds, start, end):

    if start is not None:
        ds = ds.sel(time=slice(start, None))

    if end is not None:
        ds = ds.sel(time=slice(None, end))

    return ds


def ask_variable(ds: xr.Dataset, multiple: bool = False, prompt: str = None, var_gui=None) -> list | str:
    """
    Allows choosing one or more variables/coords in an xarray Dataset.
    
    Parameters:
        ds       : xarray.Dataset
        multiple : True to choose multiple variables
        prompt   : custom prompt message
        var_gui  : optional GUI parameter
    
    Returns:
        str if single choice, list[str] if multiple
    """
    if var_gui is not None:
        return var_gui
    # List of all variables and coordinates
    choices = list(ds.data_vars) + list(ds.coords)
    
    # Default message
    message = prompt or ("Select variable(s) (comma-separated):" if multiple 
                        else "Select variable:")
    
    # Display options
    print("\nAvailable variables and coordinates:")
    for i, var in enumerate(choices):
        print(f" [{i}] {var}")
    
    while True:
        user_input = input(f"{message} ").strip()
        try:
            if multiple and user_input == "":
                print("Please select at least one variable.")
                continue
            if multiple:
                idx_list = sorted(set(int(i.strip()) for i in user_input.split(",")))
                selected = [choices[i] for i in idx_list]
            else:
                idx = int(user_input)
                selected = choices[idx]
            
            return selected
        except (ValueError, IndexError):
            print("Invalid input. Please enter the indices corresponding to available variables.")


def ask_time_period(ds, start_gui=None, end_gui=None):
    """
    Ask the user for a start and end date within the dataset time range.
    Returns (start_date, end_date) as pandas Timestamp or None.
    """
    
    if start_gui is not None or end_gui is not None:
        return start_gui, end_gui

    time_values = pd.to_datetime(ds["time"].values)

    min_date = time_values.min()
    max_date = time_values.max()

    print("\nAvailable period:")
    print(f" From {min_date.date()} to {max_date.date()}")

    print("\nDefine the period (leave empty to show all)")

    while True:

        start_input = input("Start date (YYYY-MM-DD): ").strip()
        end_input = input("End date (YYYY-MM-DD): ").strip()

        # --- secure parsing ---
        try:
            start_date = pd.to_datetime(start_input) if start_input else None
        except Exception:
            print("Invalid format for start date.")
            continue

        try:
            end_date = pd.to_datetime(end_input) if end_input else None
        except Exception:
            print("Invalid format for end date.")
            continue

        # --- check consistency ---
        if start_date and end_date and start_date > end_date:
            print("Start date must be before end date.")
            continue

        # --- check within range ---
        if start_date and start_date < min_date:
            print("Start date is before available period.")
            continue

        if end_date and end_date > max_date:
            print("End date is after available period.")
            continue

        break

    return start_date, end_date


def dataset_to_dataframe(ds):

    return ds.to_dataframe().reset_index()


def format_period_text(start_date, end_date):
    """
    Return a readable string describing the selected period.
    """

    if start_date and end_date:
        return f" ({start_date.date()} → {end_date.date()})"

    elif start_date:
        return f" (from {start_date.date()})"

    elif end_date:
        return f" (until {end_date.date()})"

    else:
        return ""
    

def configure_plot(
        x_default: str = None,
        y_defaults: list[str] | str = None,
        period_text: str = "",
        x_limits: list[float] = None,
        y_limits: list[float] = None,
        multiple_y: bool = False,
        plot_config_gui: dict = None
        ):
    """
    Generic plot configuration.

    Args:
        x_default: default X label
        y_default: default Y label
        legend_defaults: list of legend labels
        period_text: period text
        allow_x_limits: allow X axis scale adjustment
        allow_y_limits: allow Y axis scale adjustment
        plot_config_gui: dictionary from Streamlit with config params

    Returns:
        dict containing labels, title and limits
    """

    if plot_config_gui is not None:
        return {
            "x_label": plot_config_gui.get("x_label", x_default),
            "y_label": plot_config_gui.get("y_label", y_defaults),
            "legend_labels": plot_config_gui.get("legend_labels", []),
            "title": plot_config_gui.get("title", ""),
            "x_limits": plot_config_gui.get("x_limits", x_limits),
            "y_limits": plot_config_gui.get("y_limits", y_limits)
        }

    # ----------------------
    # X label
    # ----------------------

    if x_default is not None:

        x_label = input(
            f"Label for X-axis (leave empty for '{x_default}'): "
        ).strip()

        x_label = x_label if x_label else x_default

        x_unit = input("Unit for X-axis (leave empty for none): ").strip()

        x_label = build_axis_label(x_label, x_unit)

    else:
        x_label = None

    # ----------------------
    # Y label & legend
    # ----------------------

    if multiple_y:

        y_label_input = input(
            f"Label for Y-axis (leave empty for 'Values'): "
        ).strip()

        y_unit = input("Unit for Y-axis (leave empty for none): ").strip()

        y_label = build_axis_label(
            y_label_input if y_label_input != "" else "Values",
            y_unit
        )

        legend_input = input(
            f"Legend names for each Y (comma-separated, leave empty for defaults: {', '.join(y_defaults)}): "
        ).strip()

        if legend_input == "":
            legend_labels = y_defaults
        else:
            legend_labels = [l.strip() for l in legend_input.split(",")]

            if len(legend_labels) != len(y_defaults):
                raise ValueError("Number of legend labels must match number of Y variables")

    else:

        y_label_input = input(
            f"Label for Y-axis (leave empty for '{y_defaults}'): "
        ).strip()

        y_unit = input("Unit for Y-axis (leave empty for none): ").strip()

        y_label = build_axis_label(
            y_label_input if y_label_input != "" else y_defaults,
            y_unit
        )

        legend_labels = []

    # ----------------------
    # axis limits
    # ----------------------

    if x_limits is not None:
        

        while True:
            choice = input("Custom X axis limits? (y/n): ").strip().lower()
            if choice in ["y", "n"]:
                break
            print("Please enter 'y' or 'n'.")

        if choice == "y":
            
            [x_min, x_max] = x_limits

            print(f"\nX values range from {x_min:.3f} to {x_max:.3f}")

            while True:
                x_min_user = input(f"X min (leave empty for {x_min:.3f}) : ").strip()
                x_max_user = input(f"X max (leave empty for {x_max:.3f}) : ").strip()

                try:
                    x_min_final = float(x_min_user) if x_min_user != "" else x_min
                    x_max_final = float(x_max_user) if x_max_user != "" else x_max
                    break

                except ValueError:
                    print("Invalid numeric value. Please try again.")

            x_limits = (x_min_final, x_max_final)

    if y_limits is not None:

        while True:
            choice = input("Custom Y axis limits? (y/n): ").strip().lower()
            if choice in ["y", "n"]:
                break
            print("Please enter 'y' or 'n'.")

        if choice == "y":
            
            [y_min, y_max] = y_limits

            print(f"\nY values range from {y_min:.3f} to {y_max:.3f}")

            while True:
                y_min_user = input(f"Y min (leave empty for {y_min:.3f}) : ").strip()
                y_max_user = input(f"Y max (leave empty for {y_max:.3f}) : ").strip()

                try:
                    y_min_final = float(y_min_user) if y_min_user != "" else y_min
                    y_max_final = float(y_max_user) if y_max_user != "" else y_max
                    break

                except ValueError:
                    print("Invalid numeric value. Please try again.")
                
            y_limits = (y_min_final, y_max_final)

    # ----------------------
    # Title
    # ----------------------

    default_title = f"{y_defaults} vs {x_default}{period_text}" if x_default and y_defaults else ""

    title = input(
        f"Chart title (leave empty for '{default_title}'): "
    ).strip()

    title = title if title else default_title

    return {
        "x_label": x_label,
        "y_label": y_label,
        "legend_labels": legend_labels,
        "title": title,
        "x_limits": x_limits,
        "y_limits": y_limits
    }


def build_axis_label(label, unit):
    """
    Build axis label with unit if it exists.
    Example:
    label="Temperature", unit="°C" -> "Temperature (°C)"
    """
    unit = unit.strip()
    if unit == "":
        return label
    return f"{label} ({unit})"


def handle_xarray_dimensions(
    da: xr.DataArray,
    main_dims: list[str],
    dim_selections_gui: dict = None,
    auto_mean_gui: bool = False
):
    """
    Handle extra dimensions in an xarray DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Variable to process
    main_dims : list[str]
        Dimensions that must remain (ex: ["time"])
    dim_selections_gui : dict
        Optional GUI parameter for dimension choices
    auto_mean_gui : bool
        Optional GUI parameter to automatically average extra dims

    Returns
    -------
    list of tuples:
        (selection_dict, data_values)
    """

    selections = {}
    
    # Identify which dimensions need to be handled (those not in main_dims)
    dims = [d for d in da.dims if d not in main_dims]
    
    # Improved GUI mode detection:
    # If this is called from line_chart, bar_chart, etc., it should not block.
    # We'll check if we have any gui-related arguments or if we can rely on a safer check.
    # For now, let's assume if dim_selections_gui is a dict (even empty), it's GUI mode.
    is_gui = (dim_selections_gui is not None or auto_mean_gui is True)
    # If we are called with ANY GUI parameter (even if empty), we should NOT block
    # We can detect this by seeing if the caller is one of our GUI plotting functions 
    # OR if we pass a special flag. For now, let's look at the parameters.

    for dim in dims:
        if dim_selections_gui is not None and dim in dim_selections_gui:
            if dim_selections_gui[dim] == "mean":
                da = da.mean(dim=dim, skipna=True)
                continue
            else:
                selections[dim] = dim_selections_gui[dim]
                continue
        
        if auto_mean_gui:
            da = da.mean(dim=dim, skipna=True)
            continue
            
        coords = da.coords[dim].values
        n = len(coords)

        # In GUI mode, if no selection provided, we MUST NOT call input()
        # We'll default to mean for large dims and 'all' for small dims if no info
        if is_gui:
            if n > 30:
                da = da.mean(dim=dim, skipna=True)
            else:
                selections[dim] = list(coords)
            continue

        # ---- If dimension very large → propose mean (Terminal only)
        if n > 30:
            print(f"\nDimension '{dim}' has {n} values.")
            while True:
                choice = input(f"Average over '{dim}'? (y/n): ").strip().lower()
                if choice in ["y", "n"]: break
                print("Please enter 'y' or 'n'.")
            
            if choice == "y":
                da = da.mean(dim=dim, skipna=True)
                print(f"→ Averaged over {dim}")
                continue

        # ---- If single value
        if n == 1:
            selections[dim] = coords
            continue

        # ---- Ask user selection (Terminal only)
        print(f"\nDimension '{dim}' values:")
        for i, v in enumerate(coords):
            print(f"[{i}] {v}")

        while True:
            choice = input(f"indices for {dim} (ex: 0,1 or leave empty for all): ").strip()
            if choice == "" or choice.lower() == "all":
                selections[dim] = list(coords)
                break
            try:
                idx = [int(i.strip()) for i in choice.split(",")]
                if any(i < 0 or i >= n for i in idx): raise IndexError
                selections[dim] = [coords[i] for i in idx]
                break
            except (ValueError, IndexError):
                print("Invalid indices. Please try again.")


    # ---- Generate combinations

    if len(selections) == 0:

        return [({}, da.values)]

    combos = list(itertools.product(*selections.values()))
    dims_names = list(selections.keys())

    outputs = []

    for combo in combos:

        sel = dict(zip(dims_names, combo))

        da_sel = da.sel(**sel)

        outputs.append((sel, da_sel.values))

    return outputs


def get_sort_key_for_category(x_values):
    """
    Determine if values match months or seasons and return sort order.
    
    Parameters
    ----------
    x_values : array-like
        Values to check (typically x-axis data)
    
    Returns
    -------
    list or None
        Sort key list if months/seasons detected, None otherwise
    """
    month_order = [calendar.month_name[i] for i in range(1, 13)]
    season_order = ['Spring', 'Summer', 'Autumn', 'Winter']
    
    # Convert to strings for comparison
    x_str_values = [str(v) for v in x_values]
    
    if any(m in x_str_values for m in month_order):
        return month_order
    elif any(s in x_str_values for s in season_order):
        return season_order
    
    return None


def apply_categorical_sort(x_data, sort_key):
    """
    Apply categorical sorting to data.
    
    Parameters
    ----------
    x_data : array-like or pd.Series
        X-axis data to sort
    sort_key : list
        Order of categories
    
    Returns
    -------
    pd.Categorical
        Categorized and sorted data
    """
    x_str = pd.Series([str(v) for v in x_data])
    categorical = pd.Categorical(x_str, categories=sort_key, ordered=True)
    return categorical


# ---------------- Bar Chart ----------------

def bar_chart(ds: xr.Dataset, x_name_gui=None, y_name_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False):
    """
    Create a bar chart from an xarray Dataset.
    
    Interactive function that allows selection of:
    - X and Y variables
    - Time period
    - Custom labels, units, and title
    - Automatic sorting for months/seasons
    """
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")

    # ----------------------
    # Variable selection
    # ----------------------
    
    x_name = ask_variable(ds, prompt="Variable for X-axis: ", var_gui=x_name_gui)
    y_name = ask_variable(ds, prompt="Variable for Y-axis: ", var_gui=y_name_gui)
    
    if x_name == y_name:
        raise ValueError("X and Y variables must be different.")

    # ----------------------
    # Time period selection
    # ----------------------
    
    start_date, end_date = ask_time_period(ds, start_gui=start_gui, end_gui=end_gui)
    ds_period = subset_time(ds, start_date, end_date)
    period_text = format_period_text(start_date, end_date)

    # ----------------------
    # Figure setup
    # ----------------------
    
    fig, ax = plt.subplots(figsize=(8, 5))

    # ----------------------
    # Configuration of labels/title
    # ----------------------
    
    y_values = ds_period[y_name].values.astype(float).flatten()
    y_values = y_values[np.isfinite(y_values)]
    y_min = float(y_values.min()) if len(y_values) > 0 else 0
    y_max = float(y_values.max()) if len(y_values) > 0 else 1

    labels = configure_plot(
        x_default=x_name,
        y_defaults=y_name,
        period_text=period_text,
        x_limits=None,
        y_limits=[y_min, y_max],
        multiple_y=False,
        plot_config_gui=plot_config_gui
    )
    
    x_label = labels["x_label"]
    y_label = labels["y_label"]
    title = labels["title"] or f"Bar chart: {y_label} vs {x_label}{period_text}"
    
    if labels["y_limits"] is not None:
        ax.set_ylim(labels["y_limits"])

    # ----------------------
    # Extract X data
    # ----------------------
    
    x_arr = ds_period[x_name] if x_name in ds_period else ds_period.coords[x_name]
    if x_arr.ndim != 1:
        raise ValueError(f"X variable '{x_name}' must be 1D")
    
    x_vals = x_arr.values

    # ----------------------
    # Handle Y dimensions
    # ----------------------
    
    da_y = ds_period[y_name]
    
    # Get extra dimensions (not matching X dimension)
    x_dim = x_arr.dims[0]
    other_dims = [d for d in da_y.dims if d != x_dim]
    
    # Handle extra dimensions
    if other_dims:
        results = handle_xarray_dimensions(
            da_y, 
            main_dims=[x_dim],
            dim_selections_gui=dim_selections_gui,
            auto_mean_gui=auto_mean_gui
        )
    else:
        results = [({}, da_y.values)]

    # ----------------------
    # Sort data if months/seasons detected
    # ----------------------
    
    x_str_array = pd.Series([str(v) for v in x_vals])
    sort_key = get_sort_key_for_category(x_str_array)
    
    if sort_key:
        categorical = apply_categorical_sort(x_str_array, sort_key)
        sort_idx = np.argsort(categorical)
    else:
        sort_idx = np.arange(len(x_vals))

    # ----------------------
    # Plot
    # ----------------------
    
    for sel, y_vals in results:
        
        # Ensure proper length alignment
        if len(y_vals) != len(x_vals):
            if len(y_vals) == 1:
                y_vals = np.full_like(x_vals, y_vals[0], dtype=float)
            else:
                y_vals = y_vals[:len(x_vals)]
        
        # Convert to float
        try:
            y_vals = np.array(y_vals, dtype=float)
        except (ValueError, TypeError):
            y_vals = pd.to_numeric(y_vals, errors='coerce').values
        
        # Apply sorting
        x_sorted = x_str_array.iloc[sort_idx].values
        y_sorted = y_vals[sort_idx]
        
        # Create label for legend (if multiple datasets)
        label = y_name
        if sel:
            label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())
        
        # Plot
        colors = cm.viridis(np.linspace(0, 1, len(x_sorted)))
        ax.bar(x_sorted, y_sorted, color=colors, label=label)

    # ----------------------
    # Styling
    # ----------------------
    
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return fig

# ---------------- Line Chart ---------------- 

def line_chart(ds: xr.Dataset, var_gui=None, x_name_gui=None, y_names_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False, plot_envelope_gui=None, envelope_type_gui=None):

    if not isinstance(ds, xr.Dataset):
        raise TypeError("Attendu : xarray.Dataset")

    # -------- Variable selection --------
    # If var_gui is provided (list of Y variables), we use the first time-like or coord for X
    # unless x_name_gui is provided.
    if var_gui is not None and y_names_gui is None:
        y_names_gui = var_gui if isinstance(var_gui, list) else [var_gui]

    if x_name_gui is None:
        # Fallback for X: find the first dimension that looks like time/lat/lon
        x_name_gui = next((d for d in ds.dims if any(s in d.lower() for s in ['time', 'date', 'lat', 'lon', 'x', 'y'])), list(ds.dims)[0])

    x_name = ask_variable(ds, prompt="Variable for X: ", var_gui=x_name_gui)

    y_names = ask_variable(
        ds,
        multiple=True,
        prompt="Variables for Y (comma-separated): ",
        var_gui=y_names_gui
    )

    # -------- Period selection --------
    is_gui = any(p is not None for p in [var_gui, x_name_gui, y_names_gui, start_gui, end_gui, plot_config_gui, dim_selections_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        start_date, end_date = ask_time_period(ds, start_gui=start_gui, end_gui=end_gui)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)

    # -------- Figure --------

    fig, ax = plt.subplots(figsize=(10,6))

    # -------- Configuration labels --------
    # Use ds_period instead of ds here
    y_min = float(ds_period[y_names].to_array().min().values)
    y_max = float(ds_period[y_names].to_array().max().values)

    labels = configure_plot(
            x_default=x_name,
            y_defaults=y_names,
            period_text=period_text,
            x_limits=None,
            y_limits=[y_min,y_max],
            multiple_y=True,
            plot_config_gui=plot_config_gui
        )
    
    x_label = labels["x_label"]
    y_label = labels["y_label"]
    legend_labels = labels["legend_labels"]
    title = labels["title"] or f"Line chart: {', '.join(y_names)} vs {x_label}{period_text}"
    if labels["y_limits"] is not None:
        ax.set_ylim(labels["y_limits"])

    # -------- Check for model dimension and envelope option --------
    plot_envelope = False
    envelope_type = "average"  # "average" or "individual"

    if any('model' in ds_period[y_name].dims for y_name in y_names):
        if plot_envelope_gui is not None:
            plot_envelope = plot_envelope_gui
            if envelope_type_gui is not None:
                envelope_type = envelope_type_gui
        elif is_gui:
            # In GUI mode, if not specified, we default to False to avoid blocking
            plot_envelope = False
        else:
            while True:
                choice = input("Model dimension detected. Plot envelopes (min-max)? (y/n): ").strip().lower()
                if choice in ["y", "n"]:
                    plot_envelope = (choice == "y")
                    break
                print("Please enter 'y' or 'n'.")

            if plot_envelope:
                while True:
                    choice = input("Show average across models or individual model lines? (avg/individual): ").strip().lower()
                    if choice in ["avg", "average", "individual", "ind"]:
                        envelope_type = "average" if choice in ["avg", "average"] else "individual"
                        break
                    print("Please enter 'avg'/'average' or 'individual'/'ind'.")

    # -------- X --------

    x_arr = ds_period[x_name] if x_name in ds_period else ds_period.coords[x_name]

    if x_arr.ndim != 1:
        raise ValueError("X must be 1D")

    x_dim = x_arr.dims[0]
    x_vals = x_arr.values

    # -------- Y loop --------
    for y_name in y_names:

        da = ds_period[y_name]

        if x_dim not in da.dims:
            continue

        # -------- Case: model dimension exists and ensemble plot is requested --------
        if plot_envelope and 'model' in da.dims:
            # For envelope plotting, handle extra dimensions interactively
            results = handle_xarray_dimensions(
                da,
                main_dims=[x_dim, 'model'],  # Keep both time and model dimensions
                dim_selections_gui=dim_selections_gui,
                auto_mean_gui=auto_mean_gui
            )

            for sel, y_vals in results:
                # y_vals now has shape (n_models, n_time_points)
                # Calculate envelope statistics across models (axis=0)
                y_min = np.nanmin(y_vals, axis=0)
                y_max = np.nanmax(y_vals, axis=0)

                # Create label
                label = y_name
                if sel:
                    label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items() if k != 'model')

                # Plot envelope (min-max range)
                ax.fill_between(x_vals, y_min, y_max, alpha=0.3, label=f"{label} (min-max)")

                # Plot based on envelope type choice
                if envelope_type == "average":
                    y_mean = np.nanmean(y_vals, axis=0)
                    ax.plot(x_vals, y_mean, label=f"{label} (mean)", linewidth=2)
                else:  # individual
                    # Plot individual model lines
                    for i in range(y_vals.shape[0]):
                        model_label = f"{label} (model {i+1})"
                        ax.plot(x_vals, y_vals[i], label=model_label, alpha=0.7)
        else:
            # Normal plotting without envelope
            results = handle_xarray_dimensions(
                da,
                main_dims=[x_dim],
                dim_selections_gui=dim_selections_gui,
                auto_mean_gui=auto_mean_gui
            )

            for sel, y_vals in results:

                label = y_name

                if sel:
                    label += " | " + ", ".join(
                        f"{k}={v}" for k, v in sel.items()
                    )
                ax.plot(x_vals, y_vals, label=label)

    # Plot individual line
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", bbox_to_anchor=(1.05, 1))

    return fig

# ---------------- Bar Chart ---------------- 

def bar_chart(ds: xr.Dataset, var_gui=None, x_name_gui=None, y_names_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False):
    """
    Create a bar chart from an xarray Dataset.
    Same logic as line_chart but uses ax.bar.
    """
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Attendu : xarray.Dataset")

    if var_gui is not None and y_names_gui is None:
        y_names_gui = var_gui if isinstance(var_gui, list) else [var_gui]

    if x_name_gui is None:
        x_name_gui = next((d for d in ds.dims if any(s in d.lower() for s in ['time', 'date', 'lat', 'lon'])), list(ds.dims)[0])

    x_name = ask_variable(ds, prompt="Variable for X: ", var_gui=x_name_gui)
    y_names = ask_variable(ds, multiple=True, prompt="Variables for Y: ", var_gui=y_names_gui)

    # -------- Period selection --------
    is_gui = any(p is not None for p in [x_name_gui, y_names_gui, plot_config_gui, dim_selections_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        start_date, end_date = ask_time_period(ds)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)

    fig, ax = plt.subplots(figsize=(10,6))
    
    labels = configure_plot(x_default=x_name, y_defaults=y_names, period_text=period_text, plot_config_gui=plot_config_gui)
    title = labels["title"] or f"Bar chart: {', '.join(y_names)} vs {labels['x_label']}{period_text}"

    x_arr = ds_period[x_name] if x_name in ds_period else ds_period.coords[x_name]
    x_dim = x_arr.dims[0]
    
    # Selection of X values (handle_xarray_dimensions returns (sel, values) pairs)
    # We need to ensure we align the bars with the correct X values
    
    # Small helper for bar width
    n_vars = len(y_names)
    width = 0.8 / n_vars

    # We'll use the unique X values from the dataset to align the bars
    unique_x = x_arr.values
    x_indices = np.arange(len(unique_x))

    for i, y_name in enumerate(y_names):
        da = ds_period[y_name]
        # Use x_dim as the main dimension to preserve it
        results = handle_xarray_dimensions(
            da,
            main_dims=[x_dim],
            dim_selections_gui=dim_selections_gui,
            auto_mean_gui=auto_mean_gui
        )
        
        for sel, y_vals in results:
            label = y_name
            if sel:
                label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())
            
            # Simple bar plot (might overlap if multiple series from handle_xarray_dimensions)
            ax.bar(x_indices + (i - n_vars/2 + 0.5)*width, y_vals, width, label=label)

    ax.set_xticks(x_indices)
    # Format labels if they are dates
    if np.issubdtype(x_arr.dtype, np.datetime64):
        ax.set_xticklabels(pd.to_datetime(unique_x).strftime('%Y-%m-%d'), rotation=45)
    else:
        ax.set_xticklabels([str(v) for v in unique_x], rotation=45)

    ax.set_xlabel(labels["x_label"])
    ax.set_ylabel(labels["y_label"])
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()

    return fig

# -------------- Scatter Plot ---------------

def scatter_chart(ds: xr.Dataset, var_gui=None, x_name_gui=None, y_names_gui=None, y_name_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False):
    """
    Create a scatter plot from an xarray Dataset.
    """
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")
    
    # Handle parameter name variations from GUI
    if y_name_gui is not None and y_names_gui is None:
        y_names_gui = [y_name_gui]
    if var_gui is not None and y_names_gui is None:
        y_names_gui = var_gui if isinstance(var_gui, list) else [var_gui]

    # -------- Variable selection --------
    
    x_name = ask_variable(ds, prompt="Variable for X-axis: ", var_gui=x_name_gui)
    
    y_names = ask_variable(
        ds,
        multiple=True,
        prompt="Variables for Y-axis (comma-separated): ",
        var_gui=y_names_gui
    )
    
    # -------- Period selection --------
    is_gui = any(p is not None for p in [x_name_gui, y_names_gui, plot_config_gui, dim_selections_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        start_date, end_date = ask_time_period(ds)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)
    
    # -------- Figure setup --------
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # -------- Plot configuration --------
    
    x_min = float(ds_period[x_name].min().values)
    x_max = float(ds_period[x_name].max().values)
    y_min = float(ds_period[y_names].to_array().min().values)
    y_max = float(ds_period[y_names].to_array().max().values)
    
    labels = configure_plot(
        x_default=x_name,
        y_defaults=y_names,
        period_text=period_text,
        x_limits=[x_min, x_max],
        y_limits=[y_min, y_max],
        multiple_y=True,
        plot_config_gui=plot_config_gui
    )
    
    x_label = labels["x_label"]
    y_label = labels["y_label"]
    legend_labels = labels["legend_labels"]
    title = labels["title"] or f"Scatter chart: {', '.join(y_names)} vs {x_label}{period_text}"
    
    if labels["x_limits"] is not None:
        ax.set_xlim(labels["x_limits"])
    if labels["y_limits"] is not None:
        ax.set_ylim(labels["y_limits"])
    
    # -------- X variable --------
    
    x_arr = ds_period[x_name] if x_name in ds_period else ds_period.coords[x_name]
    
    if x_arr.ndim != 1:
        raise ValueError("X variable must be 1D")
    
    x_dim = x_arr.dims[0]
    x_vals = x_arr.values
    
    # Convert X to numeric and handle NaN
    x_numeric = pd.to_numeric(x_vals, errors='coerce')
    
    # Determine if we are in GUI mode
    is_gui_scatter = any(p is not None for p in [var_gui, x_name_gui, y_names_gui, y_name_gui, start_gui, end_gui, plot_config_gui, dim_selections_gui])

    for i, y_name in enumerate(y_names):
        
        da = ds_period[y_name]
        
        if x_dim not in da.dims:
            continue
        
        results = handle_xarray_dimensions(
            da,
            main_dims=[x_dim],
            dim_selections_gui=dim_selections_gui,
            auto_mean_gui=auto_mean_gui
        )
        
        for sel, y_vals in results:
            
            # Convert Y to numeric and handle NaN
            y_numeric = pd.to_numeric(y_vals, errors='coerce')
            
            # Create mask for valid (non-NaN) points
            valid_mask = ~(np.isnan(x_numeric) | np.isnan(y_numeric))
            
            # Filter to valid points only
            x_plot = x_numeric[valid_mask]
            y_plot = y_numeric[valid_mask]
            
            # Create label for legend
            label = legend_labels[i] if i < len(legend_labels) else y_name
            
            if sel:
                label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())
            
            # Plot scatter
            ax.scatter(x_plot, y_plot, label=label, color=colors[i], s=50)
    
    # -------- Styling --------
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc="upper right", bbox_to_anchor=(1.05, 1))
    
    return fig

# ---------------- Radar Chart ----------------
'''
def radar_chart(ds: xr.Dataset):
    """
    Create a radar chart from an xarray Dataset.
    
    Interactive function that allows selection of:
    - Category variable (for radar axes)
    - Value variables (for the radar data)
    - Time period
    - Custom units, title, and legend
    """
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")
    
    # -------- Variable selection --------
    
    cat_name = ask_variable(ds, prompt="Variable for category axis (radar axes): ")
    
    value_names = ask_variable(
        ds,
        multiple=True,
        prompt="Variables for radar values (comma-separated): "
    )
    
    # -------- Period selection --------
    
    start_date, end_date = ask_time_period(ds)
    ds_period = subset_time(ds, start_date, end_date)
    
    period_text = format_period_text(start_date, end_date)
    
    # -------- Get category data --------
    
    cat_arr = ds_period[cat_name] if cat_name in ds_period else ds_period.coords[cat_name]
    
    if cat_arr.ndim != 1:
        raise ValueError("Category variable must be 1D")
    
    cat_values = cat_arr.values
    categories = [str(v) for v in cat_values if pd.notna(v)]
    
    N = len(categories)
    if N < 3:
        raise ValueError("A radar chart requires at least 3 categories")
    
    # -------- Units for radar values --------
    
    units_input = input("Units for radar variables (e.g.: kW, %, ms, leave empty if none): ").strip()
    
    if units_input != "":
        units_text = f" ({units_input})"
    else:
        units_text = ""
    
    # -------- Title and legend configuration --------
    
    custom_title = input("Chart title (leave empty for automatic): ").strip()
    
    if custom_title == "":
        custom_title = f"Radar chart: {', '.join(value_names)}{units_text}{period_text}"
    else:
        custom_title = f"{custom_title}{units_text}"
    
    legend_input = input("Legend names (comma-separated, leave empty for defaults): ").strip()
    
    if legend_input == "":
        legend_labels = value_names
    else:
        legend_labels = [name.strip() for name in legend_input.split(",")]
        if len(legend_labels) != len(value_names):
            raise ValueError("Number of legend names must match number of value variables")
    
    # -------- Angle setup for radar --------
    
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    # -------- Figure setup --------
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    
    # Clockwise
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)
    
    # -------- Get radial limits --------
    
    all_values = []
    for val_name in value_names:
        da = ds_period[val_name]
        all_values.extend(da.values.flatten())
    all_values = np.array([v for v in all_values if np.isfinite(v)])
    
    if len(all_values) == 0:
        raise ValueError("No valid numeric values found")
    
    val_min = all_values.min()
    val_max = all_values.max()
    margin = 0.05 * (val_max - val_min) if val_max != val_min else val_max * 0.1
    ax.set_ylim(val_min - margin, val_max + margin)
    
    # -------- Color setup --------
    
    colors = cm.viridis(np.linspace(0, 1, len(value_names)))
    
    # -------- Plot loop --------
    
    for i, val_name in enumerate(value_names):
        
        da = ds_period[val_name]
        
        # Handle extra dimensions
        results = handle_xarray_dimensions(
            da,
            main_dims=[]
        )
        
        for sel, vals in results:
            
            # Convert to numeric, handle NaN, and truncate/pad to match categories
            vals_numeric = pd.to_numeric(vals.flatten(), errors='coerce')
            
            # Extract valid values for categories
            if len(vals_numeric) > N:
                vals_numeric = vals_numeric[:N]
            elif len(vals_numeric) < N:
                # Pad with NaN if needed
                vals_numeric = np.append(vals_numeric, np.repeat(np.nan, N - len(vals_numeric)))
            
            values_list = vals_numeric.tolist()
            values_list += values_list[:1]  # Close the radar
            
            label = legend_labels[i] if i < len(legend_labels) else val_name
            
            if sel:
                label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())
            
            ax.plot(angles, values_list, label=label, color=colors[i])
    
    # -------- Styling --------
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(custom_title)
    ax.legend(loc="upper right", bbox_to_anchor=(1.05, 1))
    
    return fig
'''

def radar_chart(ds: xr.Dataset, var_gui=None, cat_name_gui=None, value_names_gui=None, start_gui=None, end_gui=None, units_gui=None, title_gui=None, legend_gui=None, plot_config_gui=None):
    """
    Create a radar chart from an xarray Dataset.
    """

    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")
    
    if var_gui is not None and value_names_gui is None:
        value_names_gui = var_gui if isinstance(var_gui, list) else [var_gui]

    # -------- Variable selection --------
    
    # For radar, we need a category dimension (like 'time' or 'model')
    if cat_name_gui is None:
        cat_name_gui = next((d for d in ds.dims if any(s in d.lower() for s in ['time', 'date', 'model', 'scenario'])), list(ds.dims)[0])

    cat_name = ask_variable(ds, prompt="Variable for category axis (radar axes): ", var_gui=cat_name_gui)
    
    value_names = ask_variable(
        ds,
        multiple=True,
        prompt="Variables for radar values (comma-separated): ",
        var_gui=value_names_gui
    )
    
    # -------- Period selection --------
    is_gui = any(p is not None for p in [var_gui, cat_name_gui, value_names_gui, plot_config_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        start_date, end_date = ask_time_period(ds, start_gui=start_gui, end_gui=end_gui)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)
    
    # -------- Get category data --------
    
    cat_arr = ds_period[cat_name] if cat_name in ds_period else ds_period.coords[cat_name]
    
    if cat_arr.ndim != 1:
        raise ValueError("Category variable must be 1D")
    
    cat_dim = cat_arr.dims[0]

    # Format categories (important if datetime)
    if np.issubdtype(cat_arr.dtype, np.datetime64):
        categories = pd.to_datetime(cat_arr.values).strftime("%Y-%m-%d").tolist()
    else:
        categories = [str(v) for v in cat_arr.values]
    
    N = len(categories)
    if N < 3:
        raise ValueError("A radar chart requires at least 3 categories")
    
    # -------- Units --------
    
    if units_gui is not None:
        units_input = units_gui
    elif is_gui:
        units_input = ""
    else:
        units_input = input("Units for radar variables (leave empty if none): ").strip()
        
    units_text = f" ({units_input})" if units_input else ""
    
    # -------- Title --------
    
    if title_gui is not None:
        custom_title = title_gui
    elif is_gui:
        custom_title = ""
    else:
        custom_title = input("Chart title (leave empty for automatic): ").strip()
    
    if custom_title == "":
        custom_title = f"Radar chart: {', '.join(value_names)}{units_text}{period_text}"
    else:
        custom_title = f"{custom_title}{units_text}"
    
    # -------- Legend --------
    
    if legend_gui is not None:
        legend_input = legend_gui
    elif is_gui:
        legend_input = ""
    else:
        legend_input = input("Legend names (comma-separated, leave empty for defaults): ").strip()
    
    if legend_input == "":
        legend_labels = value_names
    else:
        legend_labels = [name.strip() for name in legend_input.split(",")]
        if len(legend_labels) != len(value_names):
            raise ValueError("Number of legend names must match number of value variables")
    
    # -------- Angles --------
    
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    # -------- Figure --------
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)
    
    # -------- Radial limits --------
    
    all_values = []
    for val_name in value_names:
        da = ds_period[val_name]

        if cat_dim not in da.dims:
            continue

        # ✅ FIX : moyenne sur dimensions supplémentaires
        other_dims = [d for d in da.dims if d != cat_dim]
        if other_dims:
            da = da.mean(dim=other_dims, skipna=True)

        all_values.extend(da.values.flatten())

    all_values = np.array([v for v in all_values if np.isfinite(v)])
    
    if len(all_values) == 0:
        raise ValueError("No valid numeric values found")
    
    val_min = all_values.min()
    val_max = all_values.max()
    margin = 0.05 * (val_max - val_min) if val_max != val_min else val_max * 0.1
    ax.set_ylim(val_min - margin, val_max + margin)
    
    # -------- Colors --------
    
    colors = cm.viridis(np.linspace(0, 1, len(value_names)))
    
    # -------- Plot --------
    
    for i, val_name in enumerate(value_names):
        
        da = ds_period[val_name]

        if cat_dim not in da.dims:
            continue

        #  FIX PRINCIPAL
        other_dims = [d for d in da.dims if d != cat_dim]
        if other_dims:
            da = da.mean(dim=other_dims, skipna=True)

        vals = da.values

        # Conversion propre
        vals_numeric = pd.to_numeric(vals, errors='coerce')

        if len(vals_numeric) != N:
            raise ValueError(f"{val_name}: mismatch between values and categories")

        values_list = vals_numeric.tolist()
        values_list += values_list[:1]  # close radar
        
        label = legend_labels[i] if i < len(legend_labels) else val_name
        
        ax.plot(angles, values_list, label=label, color=colors[i])
        # ax.fill(angles, values_list, alpha=0.1, color=colors[i])
    
    # -------- Styling --------
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(custom_title)
    ax.legend(loc="upper right", bbox_to_anchor=(1.05, 1))
    
    return fig

# ---------------- Histogram Chart ----------------

'''
def histogram_chart(ds: xr.Dataset):
    """
    Plot a histogram from an xarray Dataset.
    """
    col_name = ask_variable(ds, prompt="Select variable to plot: ")


    default_bins = 10

    while True:
        bins_input = input(f"Number of bins for histogram (leave empty for {default_bins}): ").strip()

        if bins_input == "":
            bins = default_bins
            break

        try:
            bins = int(bins_input)
            if bins <= 0:
                print("Number of bins must be positive.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


    
    # --- Period selection ---
    is_gui = any(p is not None for p in [var_gui, plot_config_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        start_date, end_date = ask_time_period(ds)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)

    # -------- Figure --------

    fig, ax = plt.subplots(figsize=(10,6))

    # --- Configuration labels/title ---
    data = ds_period[col_name].values.astype(float)
    data = data[np.isfinite(data)]

    counts, _ = np.histogram(data, bins=bins)

    y_min = 0
    y_max = counts.max()

    if y_max == 0:
        y_max = 1  # éviter axe plat

    labels = configure_plot(
            x_default=col_name,
            y_defaults="Frequency",
            period_text=period_text,
            x_limits=None,
            y_limits=[y_min, y_max],
            multiple_y=False
        )
    
    x_label = labels["x_label"]
    y_label = labels["y_label"]
    legend_labels = labels["legend_labels"]
    title = labels["title"] or f"Histogram of {col_name}{period_text}"
    if labels["y_limits"] is not None:
        ax.set_ylim(labels["y_limits"])

    # -------- Loop over selected variable --------

    da = ds_period[col_name]

    # Handle extra dimensions
    results = handle_xarray_dimensions(da, main_dims=["time"])

    colors = cm.viridis(np.linspace(0, 1, len(results)))

    for i, (sel, data) in enumerate(results):

        label = legend_labels

        if sel:
            label += " | " + ", ".join(
                f"{k}={v}" for k, v in sel.items()
            )

        ax.hist(
            data,
            bins=bins,
            label=label,
            linewidth=1,
            color=colors[i],
            edgecolor='black'
        )

    # --- Chart creation ---
    
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle='--', alpha=0.5)
    return fig
'''

def histogram_chart(ds: xr.Dataset, var_gui=None, x_name_gui=None, col_name_gui=None, bins_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict=None, dim_selections_gui: dict=None, auto_mean_gui: bool=False):
    """
    Plot a histogram from an xarray Dataset (robust + user-friendly).
    """
    if var_gui is not None and col_name_gui is None:
        col_name_gui = var_gui

    # -------- Variable selection --------
    col_name = ask_variable(ds, prompt="Select variable to plot: ", var_gui=col_name_gui)

    # -------- Bins selection --------
    default_bins = 10
    
    # Determine if we are in GUI mode
    is_gui = any(p is not None for p in [var_gui, x_name_gui, col_name_gui, start_gui, end_gui, plot_config_gui])

    if bins_gui is not None:
        bins = int(bins_gui)
    elif is_gui:
        bins = default_bins
    else:
        while True:
            bins_input = input(f"Number of bins for histogram (leave empty for {default_bins}): ").strip()

            if bins_input == "":
                bins = default_bins
                break

            try:
                bins = int(bins_input)
                if bins <= 0:
                    print("Number of bins must be positive.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

    # -------- Period selection --------
    is_gui = any(p is not None for p in [var_gui, x_name_gui, col_name_gui])
    
    if is_gui:
        ds_period = ds
        period_text = ""
    else:
        while True:
            start_date, end_date = ask_time_period(ds)
            ds_period = subset_time(ds, start_date, end_date)
            da = ds_period[col_name]
            raw_data = np.array(da.values, dtype=float)
            valid_data = raw_data[np.isfinite(raw_data)]
            if len(valid_data) == 0:
                print("No valid data in this period. Please choose another period.")
                continue
            break
        period_text = format_period_text(start_date, end_date)

    # -------- Handle dimensions --------
    # Use selected x_name to identify the dimension to "keep"
    x_arr_hist = ds_period[x_name] if x_name in ds_period else ds_period.coords[x_name]
    x_dim_hist = x_arr_hist.dims[0] if x_arr_hist.dims else None
    
    results = handle_xarray_dimensions(da, main_dims=[x_dim_hist] if x_dim_hist else [], dim_selections_gui=dim_selections_gui, auto_mean_gui=auto_mean_gui)

    # -------- Figure --------
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = cm.viridis(np.linspace(0, 1, len(results)))

    all_counts = []

    # -------- Plot loop --------
    for i, (sel, data) in enumerate(results):

        # Nettoyage données
        data = np.array(data, dtype=float)
        data = data[np.isfinite(data)]

        if len(data) == 0:
            print(f"No valid data for selection {sel}, skipping.")
            continue

        # Histogram (pour y max)
        counts, bin_edges = np.histogram(data, bins=bins)
        all_counts.append(counts)

        # Label
        label = col_name
        if sel:
            label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())

        # Plot
        ax.hist(
            data,
            bins=bins,
            label=label,
            linewidth=1,
            color=colors[i],
            edgecolor='black'
        )

    # -------- Sécurité --------
    if len(all_counts) == 0:
        print("No valid data after dimension filtering.")
        return fig

    # -------- Y limits --------
    y_max = max(c.max() for c in all_counts)
    if y_max == 0:
        y_max = 1

    # -------- Labels & config --------
    labels = configure_plot(
        x_default=col_name,
        y_defaults="Frequency",
        period_text=period_text,
        x_limits=None,
        y_limits=[0, y_max],
        multiple_y=False,
        plot_config_gui=plot_config_gui
    )

    ax.set_title(labels["title"] or f"Histogram of {col_name}{period_text}")
    ax.set_xlabel(labels["x_label"])
    ax.set_ylabel(labels["y_label"])

    ax.set_xticks(bin_edges)
    # ax.set_xticks(bin_edges[::2])  # 1 tick sur 2

    if labels["y_limits"] is not None:
        ax.set_ylim(labels["y_limits"])


    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    if len(all_counts) > 1:
        ax.legend()

    return fig