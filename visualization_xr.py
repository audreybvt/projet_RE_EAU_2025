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

_GUI_CALL = "_GUI_CALL"
colors_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

# ---------------- Helping Functions ----------------
def subset_time(ds, start, end):

    if start is not None:
        ds = ds.sel(time=slice(start, None))

    if end is not None:
        ds = ds.sel(time=slice(None, end))

    return ds

def _get_var_filters(dim_selections_gui, var_name):
    """
    Helper to extract filters specific to a variable.
    Supports either a global dictionary {dim: [values]} 
    or a nested dictionary {var_name: {dim: [values]}}.
    """
    if not dim_selections_gui:
        return None
    
    # Check if this is a per-variable nested dictionary
    if any(isinstance(v, dict) for v in dim_selections_gui.values()):
        return dim_selections_gui.get(var_name, {})
        
    return dim_selections_gui


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
        start_date = pd.to_datetime(start_gui) if start_gui else None
        end_date   = pd.to_datetime(end_gui)   if end_gui   else None
        return start_date, end_date

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

    # GUI mode: if plot_config_gui is provided (even empty or _GUI_CALL sentinel)
    if plot_config_gui is not None:
        # Handle _GUI_CALL sentinel or dict
        if plot_config_gui is _GUI_CALL:
            cfg = {}
        else:
            cfg = plot_config_gui or {}
        xlabel = cfg.get("xlabel") or cfg.get("x_label") or x_default or ""
        ylabel = cfg.get("ylabel") or cfg.get("y_label") or (y_defaults if isinstance(y_defaults, str) else (y_defaults[0] if y_defaults else ""))
        return {
            "x_label": xlabel,
            "y_label": ylabel,
            "legend_labels": cfg.get("legend_labels", y_defaults if isinstance(y_defaults, list) else []),
            "title": cfg.get("title") or "",
            "x_limits": cfg.get("x_limits", None),
            "y_limits": cfg.get("y_limits", None),
            "h_lines": cfg.get("h_lines", []),
            "v_lines": cfg.get("v_lines", [])
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
        "y_limits": y_limits,
        "h_lines": [],
        "v_lines": []
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


def apply_gui_filters(da: xr.DataArray, dim_selections_gui: dict) -> xr.DataArray:
    """
    Applies filters from dim_selections_gui to a DataArray.
    Supports single values, lists of values, and "mean".
    Automatically handles both flat dictionaries {dim: val} 
    and nested dictionaries {var: {dim: val}}.
    """
    if not dim_selections_gui:
        return da
        
    for dim, selection in dim_selections_gui.items():
        if isinstance(selection, dict):
            # Nested dict: handle inner dimension selections
            for d, s in selection.items():
                if d in da.dims:
                    if s == "mean":
                        da = da.mean(dim=d, skipna=True)
                    else:
                        try: da = da.sel({d: s})
                        except: pass
            continue
            
        if dim in da.dims:
            if selection == "mean":
                da = da.mean(dim=dim, skipna=True)
            elif isinstance(selection, (list, np.ndarray, pd.Index)):
                try: da = da.sel({dim: selection})
                except: pass
            else:
                try: da = da.sel({dim: selection})
                except: pass
    return da


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
    
    # GUI mode: treat ANY non-None dim_selections_gui or auto_mean_gui=True as GUI mode
    # An empty dict {} is also GUI mode (no prompts)
    is_gui = (dim_selections_gui is not None or auto_mean_gui is True)

    # Identify which dimensions need to be handled (those not in main_dims)
    dims = [d for d in da.dims if d not in main_dims]

    for dim in dims:
        if dim_selections_gui is not None and dim in dim_selections_gui:
            if dim_selections_gui[dim] == "mean":
                da = da.mean(dim=dim, skipna=True)
                continue
            else:
                selections[dim] = dim_selections_gui[dim]
                continue
        
        # In GUI mode: auto-average all extra dims to prevent blocking
        if is_gui or auto_mean_gui:
            da = da.mean(dim=dim, skipna=True)
            continue

        # ---- Terminal-only path (only reached when is_gui is False) ----
        coords = da.coords[dim].values
        n = len(coords)

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

        if n == 1:
            selections[dim] = list(coords)
            continue

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

    combos = [dict(zip(selections.keys(), v)) for v in itertools.product(*selections.values())] if selections else [{}]
    
    results = []
    for sel_dict in combos:
        # Slicer but handle potential issues if dim was already reduced
        actual_sel = {k: v for k, v in sel_dict.items() if k in da.dims}
        da_sliced = da.sel(**actual_sel) if actual_sel else da
        results.append((sel_dict, da_sliced))

    return results


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

def bar_chart(ds: xr.Dataset, x_name_gui=None, y_name_gui=None, y_names_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False, plot_envelope_gui=None, envelope_type_gui=None):
    """
    Create a bar chart from an xarray Dataset.
    """
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")

    # Handle parameter name variations from GUI
    if y_names_gui is not None and y_name_gui is None:
        y_name_gui = y_names_gui[0] if isinstance(y_names_gui, list) and len(y_names_gui) > 0 else y_names_gui

    # ----------------------
    # Variable selection
    # ----------------------
    
    x_name = ask_variable(ds, prompt="Variable for X-axis: ", var_gui=x_name_gui)
    y_name = ask_variable(ds, prompt="Variable for Y-axis: ", var_gui=y_name_gui)
    
    if not (x_name_gui or y_name_gui) and x_name == y_name:
        print("X and Y variables must be different. Please try again.")
        return None

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
    x_dim = x_arr.dims[0]
    
    if x_dim not in da_y.dims:
        raise ValueError(f"The selected X-axis '{x_name}' (dimension '{x_dim}') is not present in the variable '{y_name}'. No data could be plotted. Please change the X-axis, you may have several date variable. For example, for period-grouped variables, usually select 'period' or 'time_in_period'.")

    # Get filters for this variable
    var_filters = _get_var_filters(dim_selections_gui, y_name) or {}
    
    # Envelope logic for Bar Chart
    plot_envelope = plot_envelope_gui if plot_envelope_gui is not None else False
    envelope_type = envelope_type_gui if envelope_type_gui is not None else "average"

    # Define base for background envelope
    da_envelope_base = da_y.copy()
    for d, s in var_filters.items():
        if not isinstance(s, (list, np.ndarray, pd.Index)) and s != "mean" and d in da_envelope_base.dims:
            da_envelope_base = da_envelope_base.sel({d: s})

    # ----------------------
    # Sort setup
    # ----------------------
    x_str_array = pd.Series([str(v) for v in x_vals])
    sort_key = get_sort_key_for_category(x_str_array)
    if sort_key:
        categorical = apply_categorical_sort(x_str_array, sort_key)
        sort_idx = np.argsort(categorical)
    else:
        sort_idx = np.arange(len(x_vals))

    # ----------------------
    # Envelope plotting (background) — error bars on bars
    # ----------------------
    if plot_envelope:
        # Identify the dimension causing variability (e.g. 'model' or 'scenario')
        variability_dim = next((d for d in da_envelope_base.dims if d != x_dim and da_envelope_base.sizes[d] > 1), None)
        
        if variability_dim:
            y_min_env = da_envelope_base.min(dim=variability_dim, skipna=True).values.ravel()
            y_max_env = da_envelope_base.max(dim=variability_dim, skipna=True).values.ravel()
            y_mean_env = da_envelope_base.mean(dim=variability_dim, skipna=True).values.ravel()

            # Safe size alignment
            n_x = len(x_vals)
            y_min_env  = y_min_env[:n_x]  if len(y_min_env)  >= n_x else np.pad(y_min_env,  (0, n_x - len(y_min_env)),  constant_values=np.nan)
            y_max_env  = y_max_env[:n_x]  if len(y_max_env)  >= n_x else np.pad(y_max_env,  (0, n_x - len(y_max_env)),  constant_values=np.nan)
            y_mean_env = y_mean_env[:n_x] if len(y_mean_env) >= n_x else np.pad(y_mean_env, (0, n_x - len(y_mean_env)), constant_values=np.nan)

            # Apply sort (safe: sort_idx computed from x_vals length)
            y_min_env  = y_min_env[sort_idx]
            y_max_env  = y_max_env[sort_idx]
            y_mean_env = y_mean_env[sort_idx]

            # Store for error-bar drawing after the bar loop
            _env_min = y_min_env
            _env_max = y_max_env
            _env_mean = y_mean_env
        else:
            _env_min = _env_max = _env_mean = None
    else:
        _env_min = _env_max = _env_mean = None

    # ----------------------
    # Foreground filtering and multi-series logic
    # ----------------------
    da_y_filtered = apply_gui_filters(da_y, dim_selections_gui)
    results = handle_xarray_dimensions(da_y_filtered, main_dims=[x_dim], dim_selections_gui=var_filters, auto_mean_gui=auto_mean_gui)

    # Force split if multiple categories are selected in GUI
    if len(results) == 1:
        s0, d0 = results[0]
        split_dims = [d for d in d0.dims if d != x_dim and d0.sizes[d] > 1]
        if split_dims:
            d_split = split_dims[0]
            new_results = []
            for val in d0[d_split].values:
                ns = s0.copy(); ns[d_split] = val
                new_results.append((ns, d0.sel({d_split: val})))
            results = new_results

    # ----------------------
    # Plotting loop
    # ----------------------
    n_series = len(results)
    x_base = np.arange(len(x_vals))
    width = 0.8 / n_series if n_series > 1 else 0.4
    colors = cm.viridis(np.linspace(0, 1, n_series)) if n_series > 1 else [plt.cm.viridis(0)]

    for i, (sel, da_sel) in enumerate(results):
        y_vals = da_sel.values.ravel()
        if len(y_vals) != len(x_vals):
            y_vals = y_vals[:len(x_vals)] if len(y_vals) > len(x_vals) else np.pad(y_vals, (0, len(x_vals)-len(y_vals)), 'constant', constant_values=np.nan)

        y_num = pd.to_numeric(y_vals, errors='coerce')
        y_sorted = y_num[sort_idx]
        
        all_info = {**{k: v for k, v in var_filters.items() if not isinstance(v, (list, np.ndarray, pd.Index)) and v != 'mean'}, **sel}
        label = y_name
        if all_info:
            label += " (" + ", ".join(f"{v}" for v in all_info.values()) + ")"

        offset = (i - (n_series - 1)/2) * width if n_series > 1 else 0
        bar_positions = x_base + offset
        ax.bar(bar_positions, y_sorted, width=width, label=label, color=colors[i % len(colors)])

        # ── Error bars (envelope) on each bar series ──
        if _env_min is not None and _env_max is not None:
            yerr_lo = np.maximum(0, y_sorted - _env_min)   # downward error
            yerr_hi = np.maximum(0, _env_max - y_sorted)   # upward error
            ax.errorbar(
                bar_positions, y_sorted,
                yerr=[yerr_lo, yerr_hi],
                fmt='none', ecolor='dimgray', elinewidth=1.2, capsize=3, alpha=0.7,
                label="_nolegend_" if i > 0 else "Incertitude (min–max)"
            )

    # ----------------------
    # Styling
    # ----------------------
    ax.set_xticks(x_base)
    ax.set_xticklabels(x_str_array.iloc[sort_idx], rotation=45, ha='right')
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if labels.get("x_limits") is not None:
        ax.set_xlim(labels["x_limits"])
    if labels.get("y_limits") is not None:
        ax.set_ylim(labels["y_limits"])
    # ── Threshold lines (Curseurs) ──
    h_color = labels.get("thresh_color", "red")
    v_color = labels.get("thresh_color", "blue")
    t_style = labels.get("thresh_style", "--")
    
    for val in labels.get("h_lines", []):
        ax.axhline(float(val), color=h_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)
    for val in labels.get("v_lines", []):
        try:
            ax.axvline(float(val), color=v_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)
        except: pass

    if n_series > 1: ax.legend()
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
    # Filtering will be handled per variable in the loop below.

    plot_envelope = False
    envelope_type = "average"  # "average" or "individual"

    # GUI mode: use provided params
    if plot_envelope_gui is not None:
        plot_envelope = plot_envelope_gui
        if envelope_type_gui is not None:
            envelope_type = envelope_type_gui
    elif not is_gui:
        # Check if any categorical dimension exists that could act as a variability dimension
        has_variability = False
        for y_name in y_names:
            if any(d != x_name_gui and ds[y_name].sizes[d] > 1 for d in ds[y_name].dims if str(d).lower() not in ['time', 'date', 'lat', 'lon', 'x', 'y']):
                has_variability = True
                break

        if has_variability:
            while True:
                choice = input("Variability dimension detected. Plot envelopes (min-max)? (y/n): ").strip().lower()
                if choice in ["y", "n"]:
                    plot_envelope = (choice == "y")
                    break
                print("Please enter 'y' or 'n'.")
            if plot_envelope:
                while True:
                    choice = input("Show average across categories or individual model lines? (avg/individual): ").strip().lower()
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
    plotted_anything = False

    for y_name in y_names:

        da = ds_period[y_name]

        if x_dim not in da.dims:
            continue
            
        plotted_anything = True

        # -------- Case: envelope logic requested --------
        var_filters = _get_var_filters(dim_selections_gui, y_name) or {}
        
        # Identify the dimension causing variability
        variability_dim = next((d for d in da.dims if d != x_dim and da.sizes[d] > 1 and str(d).lower() not in ['time', 'lat', 'lon', 'x', 'y']), None)

        if plot_envelope and variability_dim is not None:
            # Apply non-variability filters to get the background envelope data
            non_var_filters = {k: v for k, v in var_filters.items() if k != variability_dim}
            da_envelope = apply_gui_filters(da, non_var_filters)

            # calculate global min/max for the background envelope
            main_dims_env = [x_dim, variability_dim]
            results_env = handle_xarray_dimensions(da_envelope, main_dims=main_dims_env, dim_selections_gui=non_var_filters, auto_mean_gui=auto_mean_gui)
            
            # Find a consistent color for this variable (to match its lines)
            i_var = y_names.index(y_name)
            c_env = colors_cycle[i_var % len(colors_cycle)]

            for sel_env, y_da_env in results_env:
                if variability_dim in y_da_env.dims:
                    y_min = y_da_env.min(dim=variability_dim, skipna=True).values
                    y_max = y_da_env.max(dim=variability_dim, skipna=True).values
                    x_vals_local = y_da_env[x_dim].values
                    
                    # Plot global envelope only if not in "individual" mode
                    if envelope_type != "individual":
                        ax.fill_between(x_vals_local, y_min, y_max, alpha=0.15,
                                        color=c_env, label=f"{y_name} (Enveloppe globale)")

            # Foreground: Selective models/variables
            da_selected = apply_gui_filters(da_envelope, {variability_dim: var_filters.get(variability_dim)})
            results_plot = handle_xarray_dimensions(
                da_selected,
                main_dims=[x_dim, variability_dim] if envelope_type != "average" else [x_dim],
                dim_selections_gui=var_filters,
                auto_mean_gui=auto_mean_gui
            )

            for sel, da_sel in results_plot:
                x_vals_local = da_sel[x_dim].values
                label_prefix = y_name
                # Merge current selection and fixed filters for labeling
                all_info = {**{k: v for k, v in var_filters.items() if not isinstance(v, (list, np.ndarray, pd.Index)) and v != 'mean'}, **sel}
                if all_info:
                    label_desc = ", ".join(f"{v}" for k, v in all_info.items())
                    label_prefix += f" ({label_desc})"

                if envelope_type == "average":
                    did_average = variability_dim in da_sel.dims and da_sel.sizes[variability_dim] > 1
                    y_mean = da_sel.mean(dim=variability_dim, skipna=True).values if variability_dim in da_sel.dims else da_sel.values
                    label_final = label_prefix + (" (average)" if did_average else "")
                    ax.plot(x_vals_local, y_mean, label=label_final, linewidth=2.5)
                else:
                    # Mode 'individual': draw ALL as thin transparent lines
                    if variability_dim in da_envelope.dims:
                        all_variability = da_envelope[variability_dim].values
                        selected_variability = var_filters.get(variability_dim, None)
                        if isinstance(selected_variability, list) and len(selected_variability) > 0:
                            selected_set = set(str(m) for m in selected_variability)
                        else:
                            selected_set = None

                        colors_models = plt.cm.tab20.colors
                        for m_idx in range(len(all_variability)):
                            m_name = str(all_variability[m_idx])
                            y_v = da_envelope.isel({variability_dim: m_idx}).values
                            if y_v.ndim > 1:
                                y_v = y_v.mean(axis=tuple(range(1, y_v.ndim)))
                            x_v = da_envelope[x_dim].values
                            is_selected = (selected_set is None or m_name in selected_set)
                            
                            m_color = colors_models[m_idx % len(colors_models)]
                            
                            ax.plot(x_v, y_v,
                                    color=m_color,
                                    alpha=0.25 if not is_selected else 0.0,
                                    linewidth=0.7, label="_nolegend_")

                        if variability_dim in da_sel.dims:
                            for m_idx in range(da_sel.sizes[variability_dim]):
                                m_name = str(da_sel[variability_dim].values[m_idx])
                                y_v = da_sel.isel({variability_dim: m_idx}).values
                                ax.plot(x_vals_local, y_v,
                                        label=f"{label_prefix} | {m_name}",
                                        alpha=0.9, linewidth=1.8)
                        else:
                            ax.plot(x_vals_local, da_sel.values, label=label_prefix, linewidth=1.8)
                    else:
                        ax.plot(x_vals_local, da_sel.values, label=label_prefix)
        else:
            da_filtered = apply_gui_filters(da, var_filters)
            results = handle_xarray_dimensions(da_filtered, main_dims=[x_dim], dim_selections_gui=var_filters, auto_mean_gui=auto_mean_gui)
            for sel, da_sel in results:
                x_vals_local = da_sel[x_dim].values
                all_info = {**{k: v for k, v in var_filters.items() if not isinstance(v, (list, np.ndarray, pd.Index)) and v != 'mean'}, **sel}
                label = y_name
                if all_info:
                    label += " (" + ", ".join(f"{v}" for v in all_info.values()) + ")"
                ax.plot(x_vals_local, da_sel.values, label=label)

    if not plotted_anything:
        raise ValueError(f"The selected X-axis '{x_name}' is not present in the variables ({', '.join(y_names)}). No data could be plotted. Please change the X-axis. You may have several date variable. For example, for period-grouped variables, usually select 'time_in_period'.")

    # Plot individual line
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    if labels.get("x_limits") is not None:
        ax.set_xlim(labels["x_limits"])
    if labels.get("y_limits") is not None:
        ax.set_ylim(labels["y_limits"])

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=False)
    
    # ── Threshold lines (Curseurs) ──
    h_color = labels.get("thresh_color", "red")
    v_color = labels.get("thresh_color", "blue")
    t_style = labels.get("thresh_style", "--")
    
    for val in labels.get("h_lines", []):
        ax.axhline(float(val), color=h_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)
    for val in labels.get("v_lines", []):
        try:
            ax.axvline(val, color=v_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)
        except: pass

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15))
    plt.subplots_adjust(bottom=0.3)
    fig.autofmt_xdate()

    return fig


# -------------- Scatter Plot ---------------

def scatter_chart(ds: xr.Dataset, var_gui=None, x_name_gui=None, y_names_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False, plot_envelope_gui=None, envelope_type_gui=None):
    """
    Create a scatter plot from an xarray Dataset.
    """
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Expected: xarray.Dataset")
    
    # Handle parameter name variations from GUI
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
        # Apply time subset if provided
        if start_gui or end_gui:
            start_date = pd.to_datetime(start_gui) if start_gui else None
            end_date = pd.to_datetime(end_gui) if end_gui else None
            ds = subset_time(ds, start_date, end_date)
            period_text = format_period_text(start_date, end_date)
        else:
            period_text = ""
        ds_period = ds
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
    
    y_arr_first = ds_period[y_names[0]]
    if x_arr.ndim == 1:
        x_dim = x_arr.dims[0]
    else:
        shared_dims = list(set(x_arr.dims) & set(y_arr_first.dims))
        x_dim = next((d for d in shared_dims if any(s in d.lower() for s in ['time', 'date', 'station', 'piezometre'])), shared_dims[0] if shared_dims else None)
        if not x_dim:
            raise ValueError(f"No shared point dimension found between X ({x_name}) and Y ({y_names[0]})")
            
    # GUI modes for envelope
    plot_envelope = plot_envelope_gui if plot_envelope_gui is not None else False
    envelope_type = envelope_type_gui if envelope_type_gui is not None else "average"

    # Identify the dimension causing variability
    variability_dim = next((d for d in x_arr.dims if d != x_dim and x_arr.sizes[d] > 1 and str(d).lower() not in ['time', 'lat', 'lon', 'x', 'y']), None)

    x_var_filters = _get_var_filters(dim_selections_gui, x_name)
    main_dims_x = [x_dim, variability_dim] if plot_envelope and variability_dim in x_arr.dims else [x_dim]
    x_results = handle_xarray_dimensions(x_arr, main_dims=main_dims_x, dim_selections_gui=x_var_filters, auto_mean_gui=auto_mean_gui)
    x_dict = {frozenset(sel.items()) if sel else frozenset(): da_sel for sel, da_sel in x_results}
    
    # -------- Y loop --------
    i_color = 0
    plotted_anything = False

    for i, y_name in enumerate(y_names):
        da = ds_period[y_name]
        if x_dim not in da.dims:
            continue
            
        plotted_anything = True
        
        var_filters = _get_var_filters(dim_selections_gui, y_name) or {}
        
        # Identify the dimension causing variability for Y
        variability_dim_y = next((d for d in da.dims if d != x_dim and da.sizes[d] > 1 and str(d).lower() not in ['time', 'lat', 'lon', 'x', 'y']), None)

        # Apply non-variability filters for global envelope
        non_var_filters = {k: v for k, v in var_filters.items() if k != variability_dim_y}
        da_envelope = apply_gui_filters(da, non_var_filters)

        if plot_envelope and variability_dim_y is not None and variability_dim_y in da_envelope.dims:
            # calculate global min/max for scatter envelope (errorbars)
            results_env = handle_xarray_dimensions(da_envelope, main_dims=[x_dim, variability_dim_y], dim_selections_gui=non_var_filters, auto_mean_gui=auto_mean_gui)
            for sel_env, y_da_env in results_env:
                sel_key_env = frozenset(sel_env.items()) if sel_env else frozenset()
                x_da_env = x_dict.get(sel_key_env)
                if x_da_env is None:
                    x_da_env = list(x_dict.values())[0]

                if variability_dim_y in y_da_env.dims and variability_dim in x_da_env.dims:
                    y_min_v = y_da_env.min(dim=variability_dim_y, skipna=True).values.ravel()
                    y_max_v = y_da_env.max(dim=variability_dim_y, skipna=True).values.ravel()
                    x_min_v = x_da_env.min(dim=variability_dim, skipna=True).values.ravel()
                    x_max_v = x_da_env.max(dim=variability_dim, skipna=True).values.ravel()
                
                # Background: Point cloud for ALL available data
                i_var = y_names.index(y_name)
                c_env = colors_cycle[i_var % len(colors_cycle)]
                
                x_all = x_da_env.values.ravel()
                y_all = y_da_env.values.ravel()
                ax.scatter(x_all, y_all, color=c_env, alpha=0.1, s=10, zorder=0, label=f"{y_name} (Enveloppe globale)")

            # Foreground: Selective models/variables
            da_selected = apply_gui_filters(da_envelope, {variability_dim_y: var_filters.get(variability_dim_y)})
            results_plot = handle_xarray_dimensions(da_selected, main_dims=[x_dim, variability_dim_y] if envelope_type != "average" else [x_dim],
                                                   dim_selections_gui=var_filters, auto_mean_gui=auto_mean_gui)
            
            for sel, y_da_sel in results_plot:
                # Include filters in the label
                all_sel = {**{k: v for k, v in var_filters.items() if not isinstance(v, (list, np.ndarray, pd.Index)) and v != 'mean'}, **sel}
                label_m = f"{y_name}"
                if all_sel:
                    label_m += " (" + ", ".join(f"{v}" for k, v in all_sel.items()) + ")"

                sel_key = frozenset({k: v for k, v in sel.items() if k != variability_dim_y}.items())
                x_da_sel = x_dict.get(sel_key)
                if x_da_sel is None:
                    x_da_sel = list(x_dict.values())[0]
                c = colors_cycle[i_color % len(colors_cycle)]
                i_color += 1
                
                if envelope_type == "average":
                    did_average = variability_dim_y in y_da_sel.dims and y_da_sel.sizes[variability_dim_y] > 1
                    y_m = y_da_sel.mean(dim=variability_dim_y).values.ravel() if variability_dim_y in y_da_sel.dims else y_da_sel.values.ravel()
                    x_m = x_da_sel.mean(dim=variability_dim).values.ravel() if variability_dim in x_da_sel.dims else x_da_sel.values.ravel()
                    label_final = label_m + (" (average)" if did_average else "")
                    ax.scatter(x_m, y_m, color=c, s=60, label=label_final, edgecolor='black')
                else:
                    if variability_dim_y in y_da_sel.dims:
                        for m_idx_s in range(y_da_sel.sizes[variability_dim_y]):
                            m_name = y_da_sel[variability_dim_y].values[m_idx_s]
                            label_ind = f"{y_name} ({m_name})"
                            ax.scatter(x_da_sel.isel({variability_dim: m_idx_s}).values if variability_dim in x_da_sel.dims else x_da_sel.values, 
                                       y_da_sel.isel({variability_dim_y: m_idx_s}).values, color=c, alpha=0.8, label=label_ind)
                    else:
                        ax.scatter(x_da_sel.values, y_da_sel.values, color=c, alpha=0.8, label=label_m)
        else:
            da_filtered = apply_gui_filters(da, var_filters)
            results = handle_xarray_dimensions(da_filtered, main_dims=[x_dim], dim_selections_gui=var_filters, auto_mean_gui=auto_mean_gui)
            for sel, y_da_sel in results:
                sel_key = frozenset(sel.items())
                x_da_sel = x_dict.get(sel_key)
                if x_da_sel is None:
                    x_da_sel = list(x_dict.values())[0]
                
                all_info = {**{k: v for k, v in var_filters.items() if not isinstance(v, (list, np.ndarray, pd.Index)) and v != 'mean'}, **sel}
                label_p = y_name
                if all_info:
                    label_p += " (" + ", ".join(f"{v}" for v in all_info.values()) + ")"

                ax.scatter(x_da_sel.values, y_da_sel.values, color=colors_cycle[i_color % len(colors_cycle)], label=label_p)
                i_color += 1
                
    if not plotted_anything:
        raise ValueError(f"The selected X-axis '{x_name}' (dimension '{x_dim}') is not present in any of the selected Y-axis variables. No data could be plotted. Please change the X-axis.")
    
    # -------- Styling --------
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if labels.get("x_limits") is not None:
        ax.set_xlim(labels["x_limits"])
    if labels.get("y_limits") is not None:
        ax.set_ylim(labels["y_limits"])
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=False)

    # ── Threshold lines (Curseurs) ──
    h_color = labels.get("thresh_color", "red")
    v_color = labels.get("thresh_color", "blue")
    t_style = labels.get("thresh_style", "--")
    
    for val in labels.get("h_lines", []):
        ax.axhline(float(val), color=h_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)
    for val in labels.get("v_lines", []):
        ax.axvline(float(val), color=v_color, linestyle=t_style, linewidth=1.5, alpha=0.8, zorder=5)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15))
    plt.subplots_adjust(bottom=0.3)
    fig.autofmt_xdate()
    
    return fig


# ---------------- Radar Chart ----------------

def radar_chart(ds: xr.Dataset, var_gui=None, cat_name_gui=None, value_names_gui=None, start_gui=None, end_gui=None, units_gui=None, title_gui=None, legend_gui=None, plot_config_gui=None, dim_selections_gui=None, auto_mean_gui: bool = False):
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
        search_dims = ds[value_names_gui[0]].dims if value_names_gui and value_names_gui[0] in ds else ds.dims
        cat_name_gui = next((d for d in search_dims if any(s in d.lower() for s in ['time', 'date', 'model', 'scenario'])), list(search_dims)[0])

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

    # Format categories
    if np.issubdtype(cat_arr.dtype, np.datetime64):
        categories = pd.to_datetime(cat_arr.values).strftime("%Y-%m-%d").tolist()
    else:
        categories = [str(v) for v in cat_arr.values]
    
    N = len(categories)
    if N < 3:
        raise ValueError("A radar chart requires at least 3 categories")
    
    # -------- Units & Title --------
    
    if units_gui is not None:
        units_input = units_gui
    elif is_gui:
        units_input = ""
    else:
        units_input = input("Units for radar variables (leave empty if none): ").strip()
        
    units_text = f" ({units_input})" if units_input else ""
    
    if title_gui is not None:
        custom_title = title_gui
    elif is_gui:
        custom_title = f"Radar chart: {', '.join(value_names)}{units_text}{period_text}"
    else:
        custom_title = input("Chart title (leave empty for automatic): ").strip()
        if custom_title == "":
            custom_title = f"Radar chart: {', '.join(value_names)}{units_text}{period_text}"
        else:
            custom_title = f"{custom_title}{units_text}"
    
    # -------- Angles --------
    
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    # -------- PRE-COMPUTE curves & values --------
    
    all_curves = []
    all_values = []

    for val_name in value_names:
        da = ds_period[val_name]

        if cat_dim not in da.dims:
            continue

        var_filters = _get_var_filters(dim_selections_gui, val_name)
        results = handle_xarray_dimensions(da, main_dims=[cat_dim], dim_selections_gui=var_filters, auto_mean_gui=auto_mean_gui)

        for sel, da_sel in results:
            y_vals = da_sel.values.ravel()
            y_numeric = pd.to_numeric(y_vals, errors='coerce')

            if len(y_numeric) != N:
                continue

            vals_numeric = np.array(y_numeric)

            if not np.any(np.isfinite(vals_numeric)):
                continue

            all_curves.append((val_name, sel, vals_numeric))
            all_values.extend(vals_numeric[np.isfinite(vals_numeric)])

    if len(all_curves) == 0:
        raise ValueError("No valid data to plot")

    # -------- Radial limits (GLOBAL) --------
    
    all_values = np.array(all_values)

    vmin = all_values.min()
    vmax = all_values.max()

    margin = 0.05 * (vmax - vmin) if vmax != vmin else 1

    # -------- Figure --------
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)

    ax.set_ylim(vmin - margin, vmax + margin)

    # -------- Colors --------
    
    colors = cm.viridis(np.linspace(0, 1, len(all_curves)))

    # -------- Plot --------
    
    for i, (val_name, sel, vals_numeric) in enumerate(all_curves):

        values_list = vals_numeric.tolist()
        values_list += values_list[:1]

        label = val_name
        if sel:
            label += " | " + ", ".join(f"{k}={v}" for k, v in sel.items())

        ax.plot(
            angles,
            values_list,
            label=label,
            color=colors[i]
        )

    # -------- Styling --------
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(custom_title)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15))
    plt.subplots_adjust(bottom=0.3)
    
    return fig


# ---------------- Histogram Chart ----------------

def histogram_chart(ds: xr.Dataset, var_gui=None, col_name_gui=None, x_name_gui=None, bins_gui=None, start_gui=None, end_gui=None, plot_config_gui: dict = None, dim_selections_gui: dict = None, auto_mean_gui: bool = False):
    """
    Plot a histogram from an xarray Dataset.
    Supports multiple series (e.g., two models) by plotting superimposed semi-transparent histograms.
    """
    is_gui = any(p is not None for p in [var_gui, col_name_gui, x_name_gui, bins_gui, start_gui, end_gui, plot_config_gui, dim_selections_gui])

    if col_name_gui is not None and var_gui is None:
        var_gui = col_name_gui
    if x_name_gui is not None and var_gui is None:
        var_gui = x_name_gui

    col_name = ask_variable(ds, prompt="Select variable to plot: ", var_gui=var_gui)

    if bins_gui is not None:
        bins = bins_gui
    else:
        bins = int(input("Number of bins for histogram: ").strip())

    # --- Period selection ---
    if is_gui:
        if start_gui or end_gui:
            start_date = pd.to_datetime(start_gui) if start_gui else None
            end_date = pd.to_datetime(end_gui) if end_gui else None
            ds_period = subset_time(ds, start_date, end_date)
            period_text = format_period_text(start_date, end_date)
        else:
            ds_period = ds
            period_text = ""
    else:
        start_date, end_date = ask_time_period(ds)
        ds_period = subset_time(ds, start_date, end_date)
        period_text = format_period_text(start_date, end_date)

    # -------- Figure --------
    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Split the variable into series based on categorical dimensions ---
    da = ds_period[col_name]

    # Identify categorical (non-time) dimensions that have multiple values
    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y', 'station', 'piezometre']
    time_dims = [d for d in da.dims if 'time' in d.lower() or d in standard_dims]

    # Build results: each entry is (label_dict, flat_data)
    # We split by any categorical dim that was filtered OR that has > 1 value
    if dim_selections_gui:
        # Use the provided filters to generate separate series
        results = handle_xarray_dimensions(
            da,
            main_dims=time_dims,
            dim_selections_gui=dim_selections_gui if dim_selections_gui else {},
            auto_mean_gui=False  # Don't auto-mean; we want separate series
        )
    else:
        # No filters: single series
        results = [({}, da)]

    # Determine global bin range so all series share the same bins
    all_vals_for_range = []
    for _, da_sel in results:
        v = da_sel.values.ravel().astype(float)
        v = v[np.isfinite(v)]
        if len(v) > 0:
            all_vals_for_range.extend(v.tolist())

    if not all_vals_for_range:
        ax.set_title(f"Histogram of {col_name}{period_text}")
        ax.text(0.5, 0.5, "No finite data to display", ha='center', va='center', transform=ax.transAxes)
        return fig

    global_min = float(np.min(all_vals_for_range))
    global_max = float(np.max(all_vals_for_range))

    # --- Configuration labels/title ---
    labels = configure_plot(
        x_default=col_name,
        y_defaults="Fréquence",
        period_text=period_text,
        x_limits=None,
        y_limits=[0, 1],    # placeholder, will be overridden after plotting
        multiple_y=False,
        plot_config_gui=plot_config_gui
    )

    x_label = labels["x_label"]
    y_label = labels["y_label"]
    legend_labels = labels.get("legend_labels", [])
    title = labels["title"] or f"Histogramme de {col_name}{period_text}"

    # -------- Plotting loop --------
    n_series = len(results)
    colors = cm.viridis(np.linspace(0, 1, max(n_series, 1)))
    alpha = 0.65 if n_series > 1 else 0.85

    for i, (sel, da_sel) in enumerate(results):
        data = da_sel.values.ravel().astype(float)
        data = data[np.isfinite(data)]
        if len(data) == 0:
            continue

        # Label
        if isinstance(legend_labels, list) and i < len(legend_labels) and legend_labels[i]:
            label = legend_labels[i]
        else:
            label = col_name
        if sel:
            label += " (" + ", ".join(f"{k}={v}" for k, v in sel.items()) + ")"

        ax.hist(
            data,
            bins=bins,
            range=(global_min, global_max),
            label=label,
            alpha=alpha,
            linewidth=0.8,
            color=colors[i],
            edgecolor='white'
        )

    # --- Chart styling ---
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label or "Fréquence")
    if labels.get("x_limits") is not None:
        ax.set_xlim(labels["x_limits"])
    if n_series > 1:
        ax.legend(loc="upper right")
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    return fig