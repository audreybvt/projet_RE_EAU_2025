"""
gui_streamlit_xarray.py
Streamlit graphical interface for the RE_EAU 2025 project.
Allows loading NetCDF or CSV files, calculating hydrological indicators,
statistics, and generating visualizations.
"""
from __future__ import annotations

import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np
import os
import io
import tempfile

# ── Project Modules ──────────────────────────────────────────────────────────
import data_formatting as df_mod
import statistics_xr   as stats
import indicators_xr   as ind
import visualization_xr as viz

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Hydrological Analysis - 2026",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f2027 0%, #203a43 50%, #2c5364 100%); }
    section[data-testid="stSidebar"] * { color: #e0f7fa !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stFileUploader label { font-weight: 600; }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p  { margin: 0.3rem 0 0; font-size: 0.95rem; opacity: 0.85; }

    /* Cards */
    .info-card {
        background: #1e2a3a;
        border: 1px solid #2e4060;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        color: #cfd8e3;
    }

    /* Section titles */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4fc3f7;
        border-bottom: 2px solid #4fc3f7;
        padding-bottom: 0.3rem;
        margin: 1rem 0 0.8rem;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background: #1a2a3a;
        border-radius: 10px;
        padding: 0.8rem;
        border: 1px solid #2e4060;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0288d1, #01579b);
        color: #fff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0277bd, #014f86);
        box-shadow: 0 4px 12px rgba(2, 136, 209, 0.4);
        transform: translateY(-1px);
    }

    /* Tab styling */
    button[data-baseweb="tab"] { font-weight: 600; }

    /* Result boxes */
    .result-box {
        background: #162230;
        border-left: 4px solid #4fc3f7;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #b0bec5;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "ds": None,        # Current xarray Dataset
        "ds_info": {},     # Dataset metadata
        "logs": [],        # Operations history
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


def log(msg: str, level: str = "info"):
    icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(level, "ℹ️")
    st.session_state["logs"].append(f"{icon} {msg}")


def ds_vars() -> list[str]:
    if st.session_state["ds"] is None:
        return []
    return list(st.session_state["ds"].data_vars)


def ds_vars_and_coords() -> list[str]:
    if st.session_state["ds"] is None:
        return []
    return list(st.session_state["ds"].data_vars) + list(st.session_state["ds"].coords)


def ds_dims() -> list[str]:
    if st.session_state["ds"] is None:
        return []
    return list(st.session_state["ds"].dims.keys())

def render_categorical_filters(key_prefix="filter"):
    """
    Renders an expander with select/multi-select for dimensions not in standard_dims.
    Returns a dict {dim: selected_values}.
    """
    ds = st.session_state.get("ds")
    if ds is None: return {}
    
    standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y', 'station', 'piezometre']
    cat_dims = [d for d in list(ds.dims.keys()) if d not in standard_dims and not str(d).startswith('time_') and ds.dims[d] > 1]
    
    dict_filters = {}
    if cat_dims:
        with st.expander("🔎 Categorical filters (scenarios, models…)"):
            if key_prefix == "ind":
                st.info("💡 Select category values if you want to work on a specific model for example.")
            for dim in cat_dims:
                vals = ds[dim].values.tolist()
                options = [str(v) for v in vals]
                
                # In Viz tab (if key_prefix is 'viz'), use multiselect
                if "viz" in key_prefix:
                    selected_vals = st.multiselect(f"Filter for '{dim}'", options, default=[], key=f"{key_prefix}_{dim}")
                    if selected_vals:
                        # Map back to original values
                        orig_vals = ds[dim].values
                        matches = [v for v in orig_vals if str(v) in selected_vals]
                        dict_filters[dim] = matches
                else:
                    # In Ind tab, stay with single select for now (standard behavior)
                    selected_val = st.selectbox(f"Filter for '{dim}'", ["(All)"] + options, key=f"{key_prefix}_{dim}")
                    if selected_val != "(All)":
                        orig_vals = ds[dim].values
                        match = [v for v in orig_vals if str(v) == selected_val]
                        if match: dict_filters[dim] = match[0]
                        
    return dict_filters


def render_temporal_filters(key_prefix="time_filter"):
    """
    Renders an expander with date inputs for the time dimension.
    Returns (start_date_str, end_date_str) or (None, None).
    """
    ds = st.session_state.get("ds")
    if ds is None: return None, None
    
    t_coord = next((d for d in ds.dims if "time" in d.lower()), "time")
    if t_coord not in ds.dims:
        return None, None
        
    try:
        # Convert to pandas Timestamps to find min/max
        time_values = pd.to_datetime(ds[t_coord].values)
        min_dt = time_values.min().date()
        max_dt = time_values.max().date()
        
        with st.expander("📅 Temporal filtering (analysis period)"):
            st.info(
                "💡 **Temporal filtering**: Select the period over which you want to perform the calculation."
                ) 
            st.info(f"Available period: {min_dt} to {max_dt}")
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start date", min_dt, min_value=min_dt, max_value=max_dt, key=f"{key_prefix}_start")
            end_date = c2.date_input("End date", max_dt, min_value=min_dt, max_value=max_dt, key=f"{key_prefix}_end")
            
        return str(start_date), str(end_date)
    except Exception:
        return None, None


def time_like_dims() -> list[str]:
    return [d for d in ds_dims() if "time" in d.lower()]


def has_dataset() -> bool:
    return st.session_state["ds"] is not None


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR – Data Loading
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("💧 Projet Mention Ressources Energétiques 2026 - Audrey, Malvina, Marine et Raphaël")
    st.markdown("---")

    # ── Format ──────────────────────────────────────────────────────────────
    st.markdown("### 📁 Data Loading")
    file_format = st.radio("File format", ["NetCDF (.nc)", "CSV (.csv)", "Excel (.xlsx)"], horizontal=True)

    # ── Uploader ─────────────────────────────────────────────────────────────
    if file_format.startswith("NetCDF"):
        uploaded_files = st.file_uploader(
            "Drag and drop one or several NetCDF files",
            type=["nc"],
            accept_multiple_files=True,
            key="nc_uploader",
        )
    elif file_format.startswith("CSV"):
        uploaded_files = st.file_uploader(
            "Drag and drop a CSV file",
            type=["csv"],
            accept_multiple_files=False,
            key="csv_uploader",
        )
        skip_n = st.number_input("Metadata lines to ignore", min_value=0, value=0, step=1)
    else:  # Excel
        uploaded_files = st.file_uploader(
            "Drag and drop an Excel file",
            type=["xlsx", "xls"],
            accept_multiple_files=False,
            key="excel_uploader",
        )

    st.markdown("---")

    # ── Spatial Options (NetCDF) ───────────────────────────────────────────
    if file_format.startswith("NetCDF"):
        st.markdown("### 🗺️ Spatial Selection")
        spatial_mode = st.selectbox(
            "Spatial selection mode",
            [
                "Keep all",
                "Select a point by index",
                "Select a point (lat/lon)",
                "Select a region (lat/lon)",
            ],
        )

        spatial_gui_extra = {}
        if spatial_mode == "Select a point by index":
            pt_idx = st.number_input("Point index", min_value=0, value=0, step=1)
            spatial_gui_extra = {"method_gui": 1, "idx_gui": int(pt_idx)}

        elif spatial_mode == "Select a point (lat/lon)":
            col_lat, col_lon = st.columns(2)
            pt_lat = col_lat.number_input("Latitude", value=0.0, format="%.4f")
            pt_lon = col_lon.number_input("Longitude", value=0.0, format="%.4f")
            spatial_gui_extra = {"method_gui": 2, "lat_gui": pt_lat, "lon_gui": pt_lon}

        elif spatial_mode == "Select a region (lat/lon)":
            col1, col2 = st.columns(2)
            r_lat_min = col1.number_input("Lat min", value=0.0, format="%.2f")
            r_lat_max = col2.number_input("Lat max", value=90.0, format="%.2f")
            col3, col4 = st.columns(2)
            r_lon_min = col3.number_input("Lon min", value=-180.0, format="%.2f")
            r_lon_max = col4.number_input("Lon max", value=180.0, format="%.2f")
            spatial_gui_extra = {
                "region_gui": {
                    "lat_min": r_lat_min, "lat_max": r_lat_max,
                    "lon_min": r_lon_min, "lon_max": r_lon_max,
                }
            }

    st.markdown("---")

    # ── Load button ─────────────────────────────────────────────────
    load_btn = st.button("⬆️ Load dataset", use_container_width=True)

    if load_btn:
        if not uploaded_files:
            st.error("Please select at least one file.")
        else:
            with st.spinner("Loading in progress…"):
                try:
                    if file_format.startswith("NetCDF"):
                        files = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
                        tmp_paths = []
                        for f in files:
                            suffix = ".nc"
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                            tmp.write(f.read())
                            tmp.flush()
                            tmp_paths.append(tmp.name)

                        # --- Detect dimensions and prepare spatial_gui ---
                        # We open the first file to guess what kind of dimensions we have
                        try:
                            ds_first = xr.open_dataset(tmp_paths[0], decode_cf=False, engine='netcdf4')
                        except Exception:
                            try:
                                ds_first = xr.open_dataset(tmp_paths[0], decode_cf=False, engine='h5netcdf')
                            except Exception:
                                ds_first = xr.open_dataset(tmp_paths[0], decode_cf=False, engine='scipy')

                        if spatial_mode == "Keep all":
                            spatial_gui_val = {"keep_all": True}
                        else:
                            # Calculate 'choice' according to dimensions
                            has_grid = any(d in ds_first.dims for d in ['latitude', 'longitude', 'lat', 'lon', 'x', 'y'])
                            has_pts  = any(d in ds_first.dims for d in ['piezometre', 'station', 'stations', 'site', 'sites'])
                            
                            option_num = 1
                            options_map = {}
                            if has_grid:
                                options_map[option_num] = ('grid', 'keep'); option_num += 1
                                options_map[option_num] = ('grid', 'point'); option_num += 1
                                options_map[option_num] = ('grid', 'region'); option_num += 1
                            if has_pts:
                                options_map[option_num] = ('points', 'keep'); option_num += 1
                                options_map[option_num] = ('points', 'select'); option_num += 1
                            options_map[option_num] = ('all', 'keep')

                            if spatial_mode == "Select a point by index" and has_pts:
                                target = ('points', 'select')
                            elif spatial_mode == "Select a point (lat/lon)" and has_grid:
                                target = ('grid', 'point')
                            elif spatial_mode == "Select a region (lat/lon)" and has_grid:
                                target = ('grid', 'region')
                            else:
                                target = ('all', 'keep')

                            choice_num = next((k for k, v in options_map.items() if v == target), option_num)
                            spatial_gui_val = {"choice": choice_num}
                            
                            # Add extra parameters from spatial_gui_extra if they exist
                            if "idx_gui" in spatial_gui_extra: spatial_gui_val["idx_gui"] = spatial_gui_extra["idx_gui"]
                            if "lat_gui" in spatial_gui_extra: spatial_gui_val["lat_gui"] = spatial_gui_extra["lat_gui"]
                            if "lon_gui" in spatial_gui_extra: spatial_gui_val["lon_gui"] = spatial_gui_extra["lon_gui"]
                            if "region_gui" in spatial_gui_extra: spatial_gui_val["region_gui"] = spatial_gui_extra["region_gui"]

                        # Choose loading mode (single vs multi-files)
                        if len(tmp_paths) == 1:
                            ds_raw = ds_first # Reuse the one we opened
                            
                            if 'time' in ds_raw:
                                try:
                                    ds_raw = ds_raw.assign_coords(time=xr.coding.times.decode_cf_datetime(
                                        ds_raw['time'], ds_raw['time'].attrs.get('units', 'days since 1900-01-01'),
                                        calendar=ds_raw['time'].attrs.get('calendar', 'standard')
                                    ))
                                except Exception as e:
                                    pass

                            ds_loaded = df_mod.handle_spatial_dimensions(ds_raw, spatial_gui=spatial_gui_val)

                            # Handle advanced selection (re-selection on raw)
                            if spatial_mode == "Select a point by index" and "idx_gui" in spatial_gui_extra:
                                if has_pts:
                                    pt_dim = next(d for d in ['piezometre', 'station', 'stations', 'site', 'sites'] if d in ds_raw.dims)
                                    ds_loaded = df_mod.select_spatial_point(
                                        ds_raw, {'points': [pt_dim]}, {'points': [pt_dim]},
                                        method_gui=1, idx_gui=spatial_gui_extra["idx_gui"]
                                    )

                            elif spatial_mode == "Select a point (lat/lon)" and "lat_gui" in spatial_gui_extra:
                                if has_grid:
                                    g = next((['latitude', 'longitude'] if 'latitude' in ds_raw.dims else None) or
                                             (['lat', 'lon'] if 'lat' in ds_raw.dims else None) or
                                             (['x', 'y']), None)
                                    if g:
                                        ds_loaded = df_mod.select_spatial_point(
                                            ds_raw, {'grid': [g[0], g[1]]}, {'grid': [g[0], g[1]]},
                                            method_gui=2, lat_gui=spatial_gui_extra["lat_gui"], lon_gui=spatial_gui_extra["lon_gui"]
                                        )

                            elif spatial_mode == "Select a region (lat/lon)" and "region_gui" in spatial_gui_extra:
                                has_lat = next((d for d in ['latitude', 'lat'] if d in ds_raw.dims), None)
                                has_lon = next((d for d in ['longitude', 'lon'] if d in ds_raw.dims), None)
                                if has_lat and has_lon:
                                    ds_loaded = df_mod.select_spatial_region(
                                        ds_raw, [has_lat, has_lon], [has_lat, has_lon],
                                        region_gui=spatial_gui_extra["region_gui"]
                                    )
                        else:
                            # Multi-files
                            ds_loaded = df_mod.load_multiple_datasets(tmp_paths, spatial_gui=spatial_gui_val)

                        st.session_state["ds"] = ds_loaded

                    elif file_format.startswith("CSV"):
                        # CSV
                        f = uploaded_files
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                        tmp.write(f.read())
                        tmp.flush()
                        ds_loaded = df_mod.csv_to_xarray(tmp.name, skip_n_gui=int(skip_n))
                        st.session_state["ds"] = ds_loaded
                        
                    elif file_format.startswith("Excel"):
                        # Excel
                        st.info("Converting Excel to new format in progress... It may take a few minutes.")
                        f = uploaded_files
                        tmp_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                        tmp_excel.write(f.read())
                        tmp_excel.flush()
                        
                        tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                        
                        # existing function call
                        df_mod.excel_to_long_csv(tmp_excel.name, tmp_csv.name)
                        
                        # read format
                        ds_loaded = df_mod.csv_to_xarray(tmp_csv.name, skip_n_gui=0)
                        st.session_state["ds"] = ds_loaded

                    log("Dataset loaded successfully.", "success")
                    st.success("✅ Dataset loaded!")

                except Exception as e:
                    log(f"Loading error: {e}", "error")
                    st.error(f"Error: {e}")

    st.markdown("---")
    # ── Logs ─────────────────────────────────────────────────────────────────
    with st.expander("📋 Logs"):
        for line in reversed(st.session_state["logs"][-30:]):
            st.caption(line)
        if st.button("🗑️ Clear logs"):
            st.session_state["logs"] = []


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>💧 Hydrological Analysis - 2026</h1>
    <p>Graphical interface for climatic and hydrological data analysis (xArray)</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DATASET PREVIEW
# ══════════════════════════════════════════════════════════════════════════════
if has_dataset():
    ds = st.session_state["ds"]

    with st.expander("📊 Dataset Preview", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Variables", len(ds.data_vars))
        c2.metric("Dimensions", len(ds.dims))
        n_pts = 1
        for s in ds.sizes.values():
            n_pts *= s
        c3.metric("Total size", f"{n_pts:,}")
        t_dims = time_like_dims()
        if t_dims:
            try:
                t_vals = pd.to_datetime(ds[t_dims[0]].values)
                c4.metric("Period", f"{t_vals.min().date()} → {t_vals.max().date()}")
            except Exception:
                c4.metric("Time dimension", t_dims[0])

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Dimensions / Categories**")
            dim_rows = []
            for d, size in ds.dims.items():
                extrait = ""
                if d in ds.coords:
                    c_vals = ds[d].values
                    if size <= 10 or str(c_vals.dtype).startswith('<U') or str(c_vals.dtype) == 'object':
                        # Small lists or text: we display the content
                        extrait = str(list(c_vals[:min(5, size)]))
                        if size > 5: extrait = extrait.rstrip("]") + ", ...]"
                    elif np.issubdtype(c_vals.dtype, np.number):
                        extrait = f"Min: {float(c_vals.min()):.2g} | Max: {float(c_vals.max()):.2g}"
                    elif np.issubdtype(c_vals.dtype, np.datetime64) or "datetime" in str(c_vals.dtype).lower() or "cftime" in str(type(c_vals[0] if size>0 else None)):
                        try:
                            extrait = f"{pd.to_datetime(c_vals.min()).date()} → {pd.to_datetime(c_vals.max()).date()}"
                        except:
                            extrait = "..."
                else:
                    extrait = "No coords"
                dim_rows.append({"Dimension": d, "Nb Values": size, "Extract / Range": extrait})
            st.dataframe(pd.DataFrame(dim_rows), hide_index=True, use_container_width=True)

        with col_b:
            st.markdown("**Variables**")
            rows = []
            for v in ds.data_vars:
                da = ds[v]
                # Try to build a rich preview with dates and category context
                try:
                    # Build a flat index-based view
                    df_preview = da.to_dataframe().reset_index()
                    # Remove NaN in the value column
                    val_col = [c for c in df_preview.columns if c == v]
                    if val_col:
                        df_clean = df_preview[df_preview[val_col[0]].notna()].head(5)
                        if len(df_clean) > 0:
                            # Format datetime columns
                            for col in df_clean.columns:
                                if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                                    df_clean = df_clean.copy()
                                    df_clean[col] = df_clean[col].dt.strftime("%Y-%m-%d")
                            # Round numeric non-value columns
                            for col in df_clean.columns:
                                if col != v and pd.api.types.is_float_dtype(df_clean[col]):
                                    df_clean = df_clean.copy()
                                    df_clean[col] = df_clean[col].round(4)
                            extrait = df_clean.to_dict(orient="records")
                            extrait_str = "; ".join(
                                " | ".join(f"{k}: {val}" for k, val in row.items())
                                for row in extrait[:3]
                            )
                            if len(extrait) >= 3:
                                extrait_str += " ..."
                        else:
                            extrait_str = "(no non-NaN values)"
                    else:
                        extrait_str = str(list(da.values.flatten()[:5]))
                except Exception:
                    flat_vals = da.values.flatten()
                    try:
                        if np.issubdtype(da.dtype, np.number):
                            non_nans = flat_vals[~np.isnan(flat_vals.astype(float))]
                            extrait_str = str(list(np.round(non_nans[:5], 3)))
                        else:
                            extrait_str = str(list(flat_vals[:5]))
                    except Exception:
                        extrait_str = "..."

                rows.append({
                    "Variable": v,
                    "Dimensions": str(da.dims),
                    "Preview — date | category | value (first 5 non-NaN rows)": extrait_str
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.caption("💡 Each row shows up to 3 examples of values with their date and categorical context (model, scenario…).")

else:
    st.info("👈 Load a file from the sidebar to begin.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_stat, tab_ind, tab_viz = st.tabs([
    "📐 Statistics",
    "📏 Hydrological Indicators",
    "📈 Visualization",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 : STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_stat:
    st.markdown('<div class="section-title">Statistical Calculations</div>', unsafe_allow_html=True)

    stat_func = st.selectbox(
        "Statistical operation",
        [
            "Flexible mean",
            "Flexible maximum",
            "Flexible minimum",
            "Flexible median",
            "Flexible percentile",
            "Rolling mean",
            "Monthly interannual average",
            "Period grouping",
        ],
        help=(
            "Choose the type of calculation to perform on your variable. "
            "'Flexible' means you choose which dimensions to aggregate over. "
            "Ex: Flexible mean over 'time' = a single value for the whole period. "
            "Ex: Flexible mean over 'model' = a mean of the models each day. "
            "Rolling mean = smooths a series by averaging over a moving window (ideal for detecting trends). "
            "Period grouping = creates categories P1/P2/… that you can compare in charts."
        )
    )

    vars_list = ds_vars()
    all_dims  = ds_dims()

    col1, col2 = st.columns(2)

    with col1:
        var_name = st.selectbox(
            "Source variable",
            vars_list,
            key="stat_var",
            help=(
                "Variable on which to perform the statistical calculation. "
                "All dataset variables are available, including previously calculated ones "
                "(hydrological indicators, etc.)."
            )
        )

    if var_name:
        avail_dims = list(st.session_state["ds"][var_name].dims)
    else:
        avail_dims = all_dims

    with col2:
        if stat_func not in ("Monthly interannual average", "Rolling mean", "Period grouping"):
            dims_sel = st.multiselect(
                "Aggregate across these dimensions (calculate a single value per remaining combination)",
                avail_dims,
                default=avail_dims,
                key="stat_dims",
                help=(
                    "Select dimensions to 'flatten' by a statistical calculation. "
                    "Example 1: if your data has axes [time, model, scenario] and you select "
                    "model + scenario → you get one value per time step (averaged across all models and scenarios). "
                    "Example 2: selecting only 'time' → you get a single value per model/scenario combination. "
                    "Leave blank = aggregate everything into a single global value."
                ),
            )
        elif stat_func == "Monthly interannual average":
            t_dims_list = [d for d in avail_dims if "time" in d.lower()]
            time_dim_sel = st.selectbox(
                "Time dimension",
                t_dims_list if t_dims_list else avail_dims,
                key="stat_time_dim",
                help="Choose the dimension that represents time in your dataset (e.g. 'time', 'time_Group_1m', etc.)."
            )
        elif stat_func == "Rolling mean":
            window_val = st.number_input(
                "Window size (time steps)",
                min_value=1, value=7, step=1,
                help="Number of consecutive time steps used to calculate the rolling mean. E.g. 7 = 7-day average if data is daily."
            )
        elif stat_func == "Period grouping":
            st.markdown("**Comparison periods definition**")
            st.caption("💡 Define 2 or more periods to compare. Ex: P1 = 1950–1980 and P2 = 1980–2010. "
                       "Two new variables will be created: the mean per period (ideal for a bar chart) "
                       "and the time series per period (ideal for a line chart).")

            # Manage periods list in session state
            if "stat_periods" not in st.session_state:
                st.session_state["stat_periods"] = [("P1", "", ""), ("P2", "", "")]

            col_add, col_rm = st.columns([1, 1])
            if col_add.button("➕ Add period", key="add_period"):
                n = len(st.session_state["stat_periods"]) + 1
                st.session_state["stat_periods"].append((f"P{n}", "", ""))
            if col_rm.button("➖ Remove the last one", key="rm_period") and len(st.session_state["stat_periods"]) > 1:
                st.session_state["stat_periods"].pop()

            # Time range for date pickers
            _t_dims_s = time_like_dims()
            _t_min = _t_max = None
            if _t_dims_s:
                try:
                    _tv = pd.to_datetime(st.session_state["ds"][_t_dims_s[0]].values)
                    _t_min, _t_max = _tv.min().date(), _tv.max().date()
                except Exception:
                    pass

            updated_periods = []
            for pi, (p_name, p_start, p_end) in enumerate(st.session_state["stat_periods"]):
                cc1, cc2, cc3 = st.columns([1, 1.5, 1.5])
                new_name = cc1.text_input(f"Name P{pi+1}", value=p_name, key=f"pg_name_{pi}")
                try:
                    dflt_s = pd.to_datetime(p_start).date() if p_start else (_t_min or None)
                    dflt_e = pd.to_datetime(p_end).date()   if p_end else (_t_max or None)
                    new_start = cc2.date_input(f"Start P{pi+1}", value=dflt_s, min_value=_t_min, max_value=_t_max, key=f"pg_start_{pi}")
                    new_end   = cc3.date_input(f"End P{pi+1}",   value=dflt_e, min_value=_t_min, max_value=_t_max, key=f"pg_end_{pi}")
                except Exception:
                    new_start = cc2.text_input(f"Start P{pi+1} (YYYY-MM-DD)", value=p_start, key=f"pg_start_{pi}")
                    new_end   = cc3.text_input(f"End P{pi+1} (YYYY-MM-DD)",   value=p_end,   key=f"pg_end_{pi}")
                updated_periods.append((new_name, str(new_start), str(new_end)))
            st.session_state["stat_periods"] = updated_periods

            t_dims_pg = [d for d in avail_dims if "time" in d.lower()]
            time_dim_pg = st.selectbox(
                "Time dimension to use",
                t_dims_pg if t_dims_pg else avail_dims,
                key="pg_timedim",
                help="Choose the time dimension of your source variable. Usually 'time'."
            )
            if time_dim_pg and ("_group_" in time_dim_pg.lower() or "month" in time_dim_pg.lower()):
                st.warning(
                    f"⚠️ **Incompatible dimension detected**: The dimension `{time_dim_pg}` appears to be aggregated "
                    "(e.g. from an indicator like Qmean/VCN10 or a climatology). "
                    "Period grouping requires continuous data to correctly align "
                    "the dates between periods. Doing this on an already aggregated "
                    "variable will result in misaligned or corrupted period comparisons."
                )

    # Time period
    if stat_func not in ("Monthly interannual average",):
        t_dims = time_like_dims()
        if t_dims:
            with st.expander("⏳ Temporal filtering (optional)"):
                st.info(
                "💡 **Temporal filtering**: Select the period over which you want to perform the calculation."
                )  
                t_vals_raw = st.session_state["ds"][t_dims[0]].values
                try:
                    t_vals = pd.to_datetime(t_vals_raw)
                    t_min, t_max = t_vals.min().date(), t_vals.max().date()
                    c_s, c_e = st.columns(2)
                    d_start = c_s.date_input("Start date", value=t_min, min_value=t_min, max_value=t_max, key="stat_dstart")
                    d_end   = c_e.date_input("End date",   value=t_max, min_value=t_min, max_value=t_max, key="stat_dend")
                    start_str = str(d_start)
                    end_str   = str(d_end)
                except Exception:
                    start_str = None
                    end_str   = None
        else:
            start_str = None
            end_str   = None
    else:
        start_str = None
        end_str   = None

    # Specific percentile
    if stat_func == "Flexible percentile":
        q_val = st.slider("Percentile (%)", 1, 99, 90, key="stat_q") / 100.0

    # ── Calculation button ────────────────────────────────────────────────────────
    if st.button("▶️ Run statistical calculation", key="run_stat"):
        ds_work = st.session_state["ds"]
        try:
            # Security to avoid name 'dims_sel' is not defined
            _dims_input = dims_sel if 'dims_sel' in locals() else None
            dims_to_reduce = _dims_input if stat_func not in ("Monthly interannual average", "Rolling mean", "Period grouping") else None

            if stat_func == "Flexible mean":
                ds_work = stats.mean_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Flexible maximum":
                ds_work = stats.maximum_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Flexible minimum":
                ds_work = stats.minimum_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Flexible median":
                ds_work = stats.median_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Flexible percentile":
                ds_work = stats.percentile_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    q_gui=q_val,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Rolling mean":
                ds_work = stats.rolling_mean_value(
                    ds_work,
                    var_name_gui=var_name,
                    window_gui=int(window_val),
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Monthly interannual average":
                ds_work = stats.monthly_interannual_average_xr(
                    ds_work,
                    var_name_gui=var_name,
                    time_dim_gui=time_dim_sel,
                )

            elif stat_func == "Period grouping":
                ds_work = stats.period_grouping(
                    ds_work,
                    var_name_gui=var_name,
                    periods_gui=st.session_state.get("stat_periods", []),
                    time_dim_gui=time_dim_pg,
                )

            st.session_state["ds"] = ds_work
            new_vars = [v for v in ds_work.data_vars if v not in vars_list]
            log(f"Statistic '{stat_func}' calculated → {new_vars}", "success")
            st.success(f"✅ Calculation completed. New variables: {new_vars}")

            # --- Display statistical summary ---
            if "last_stat_summary" in ds_work.attrs:
                summary = ds_work.attrs["last_stat_summary"]
                st.markdown("---")
                st.subheader(f"📊 Results: {summary.get('method', stat_func)}")
                
                # Selection / Time period
                st.markdown(f"**Source variable:** `{summary.get('var_name', 'N/A')}`")
                st.markdown(f"**Time period:** `{summary.get('period', 'full range')}`")
                
                if "reduced_dims" in summary:
                    st.markdown(f"**Dimensions reduced:** `{summary['reduced_dims']}`")
                elif "grouped_by" in summary:
                    st.markdown(f"**Grouped by:** `{summary['grouped_by']}`")

                # New Variable Info
                nv = summary.get('new_var', 'N/A')
                st.markdown(f"**New Variable added:** `{nv}`")
                if nv in ds_work:
                    da_new = ds_work[nv]
                    st.markdown(f"**Dimensions:** `{da_new.dims}`")
                    st.markdown(f"**Shape:** `{da_new.shape}`")

                # Display structured preview
                if "preview_data" in summary and summary["preview_data"]:
                    with st.expander("👁️ Preview of the first 5 values (with dimensions)"):
                        st.markdown("**Preview table:**")
                        df_preview = pd.DataFrame(summary["preview_data"])
                        rename_map = {
                            "time": "Date",
                            "model": "Model",
                            "scenario": "Scenario",
                            "period": "Period",
                            0: "Value"
                        }
                        st.table(df_preview.rename(columns=rename_map))

                # Fallback: means per period for Period grouping
                elif "mean_per_period" in summary:
                    st.markdown("**Means per period:**")
                    period_df = pd.DataFrame.from_dict(
                        summary["mean_per_period"], orient='index', columns=["Mean"]
                    ).rename_axis("Period")
                    st.dataframe(period_df, use_container_width=True)
                    if "periods" in summary:
                        for p, rng in summary["periods"].items():
                            st.caption(f"  {p} : {rng}")
                
                st.markdown("---")

            # Preview of the new variable (existing)
            if new_vars:
                with st.expander("🔍 Technical details of new variables"):
                    for nv in new_vars:
                        da_new = ds_work[nv]
                        st.markdown(f"**{nv}** — dims: `{da_new.dims}`, shape: `{da_new.shape}`")
                        vals_flat = da_new.values.flatten()
                        vals_flat = vals_flat[~np.isnan(vals_flat.astype(float))]
                        if vals_flat.size > 0:
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Min", f"{float(vals_flat.min()):.3f}")
                            c2.metric("Mean", f"{float(vals_flat.mean()):.3f}")
                            c3.metric("Max", f"{float(vals_flat.max()):.3f}")
                            c4.metric("Data (excl. NaN)", f"{vals_flat.size:,}", help="Number of real non-null values resulting from the stat calculation.")

        except Exception as e:
            log(f"Statistical error: {e}", "error")
            st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 : HYDROLOGICAL INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
with tab_ind:
    st.markdown('<div class="section-title">Hydrological Indicators</div>', unsafe_allow_html=True)

    indicator = st.selectbox(
        "Indicator",
        [
            "Soil_Water_Balance_Index", 
            "Standardised Piezometric Level Indicator", 
            "Mean variable", 
            "Q90/95", 
            "Q10/05", 
            "VCN10", 
            "VCX3", 
            "over_threshold"
        ],
        key="ind_select",
        help=(
            "Choose the indicator to calculate. "
            "Mean = mean over the period (e.g. Qmean for discharge). "
            "Q90/95 = value exceeded 90% or 95% of the time (high values). "
            "Q10/05 = value exceeded only 10% or 5% of the time (low values). "
            "VCN10 = minimum of the rolling means over 10 consecutive time steps (extreme low). "
            "VCX3 = maximum of the means over 3 time steps (extreme high). "
            "over_threshold = detects threshold exceedances and calculates the deviation from this threshold."
        )
    )

    vars_list_ind = ds_vars()

    # ── Categorical and temporal filters ────────────────────────────────────
    dict_filters_gui = render_categorical_filters(key_prefix="ind")
    start_gui_ind, end_gui_ind = render_temporal_filters(key_prefix="ind_time")

    # ── Specific parameters for each indicator ─────────────────────────
    st.markdown("**Indicator parameters**")

    # Time period
    t_dims_ind = time_like_dims()
    time_coord_ind = t_dims_ind[0] if t_dims_ind else None
    unite_gui_val = None
    nb_gui_val    = None

    if indicator in ("Mean variable", "Q90/95", "Q10/05", "VCN10", "VCX3", "over_threshold"):
        col_tc, col_unit, col_nb = st.columns(3)
        if t_dims_ind:
            time_coord_ind = col_tc.selectbox(
                "Time coordinate",
                t_dims_ind,
                key="ind_tc",
                help=(
                    "Choose the time dimension of your variable. "
                    "Usually called 'time'. If you have already calculated an indicator, "
                    "there may be other time dimensions like 'time_Group_1m'."
                )
            )
        unite_gui_val = col_unit.selectbox(
            "Unit of the calculation period",
            ["d", "m", "y"],
            format_func=lambda x: {"d": "Days", "m": "Months", "y": "Years"}[x],
            key="ind_unite",
            help=(
                "Time unit used to resample your data before calculating the indicator. "
                "Ex: 1 month = calculate the indicator each month. 1 year = each year. "
                "3 months = each quarter."
            )
        )
        nb_gui_val = col_nb.number_input(
            "Time steps (number of units)",
            min_value=1, value=1, step=1,
            key="ind_nb",
            help=(
                "Number of units to group per calculation. "
                "Ex: unit=Months, step=3 → indicator is calculated every 3 months (per quarter). "
                "Unit=Days, step=10 → every 10 days."
            )
        )

    if indicator == "Soil_Water_Balance_Index":
        col_p, col_etr, col_dr = st.columns(3)
        var_p   = col_p.selectbox("Variable P (precipitations)", vars_list_ind, key="ips_p")
        var_etr = col_etr.selectbox("Variable ETR", vars_list_ind, key="ips_etr")
        var_dr  = col_dr.selectbox("Variable ΔR (storage variation)", vars_list_ind, key="ips_dr")
    
    elif indicator == "Standardised Piezometric Level Indicator":
        var_q = st.selectbox("Piezometric Level Variable", vars_list_ind, key="ind_varspli")

    elif indicator in ("Mean variable", "Q90/95", "Q10/05", "VCN10", "VCX3"):
        var_q = st.selectbox(
            "Variable to analyze",
            vars_list_ind,
            key="ind_varq",
            help=(
                "Select the variable on which to calculate the indicator. "
                "Can be discharge (m³/s), precipitation (mm/d), piezometric level (m), etc. "
                "The indicator will be calculated on the values of this variable."
            )
        )

    elif indicator == "over_threshold":
        var_q = st.selectbox(
            "Variable to analyze",
            vars_list_ind,
            key="ind_varq_ot",
            help=(
                "Select the variable for which you want to detect threshold exceedances. "
                "Ex: daily discharge, temperature, precipitation, etc."
            )
        )
        c1, c2 = st.columns(2)
        threshold = c1.number_input(
            "Threshold",
            value=0.0,
            format="%.4f",
            key="ind_thresh",
            help=(
                "The threshold value to detect exceedances. \n\n"
                "Examples:\n"
                "- **Floods**: set to 50 m³/s to find flood values.\n"
                "- **Heatwaves**: set to 30°C for temperature records.\n"
                "- **Droughts**: use a low threshold for groundwater levels (e.g., -0.5 m).\n\n"
                "Values **ABOVE** this threshold will be identified as exceedances."
            )
        )
        tolerance = c2.number_input(
            "Tolerance (%)",
            value=0.0,
            format="%.1f",
            key="ind_tol",
            help=(
                "A percentage added to the threshold to create a 'buffer zone'. \n\n"
                "Example: Threshold = 100, Tolerance = 5% → Effective Threshold = 105. \n\n"
                "Useful to avoid counting 'false exceedances' due to sensor noise near the threshold."
            )
        )

    # ── Indicator calculation button ─────────────────────────────────────────────
    if st.button("▶️ Calculate indicator", key="run_ind"):
        ds_work = st.session_state["ds"]
        prev_vars = set(ds_work.data_vars)
        try:
            if indicator == "Soil_Water_Balance_Index":
                ds_work = ind.IPS(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    var_p_gui=var_p,
                    var_etr_gui=var_etr,
                    var_dr_gui=var_dr,
                )
            elif indicator == "Mean variable":
                ds_work = ind.variable_mean(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )
            elif indicator == "Q90/95":
                ds_work = ind.Q90_95(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )
            elif indicator == "Q10/05":
                ds_work = ind.Q10_05(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )
            elif indicator == "VCN10":
                ds_work = ind.VCN10(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )
            elif indicator == "VCX3":
                ds_work = ind.VCX3(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )
            elif indicator == "Standardised Piezometric Level Indicator":
                st.warning("SPLI is not yet implemented in the calculation engine.")
                ds_work = ind.SPLI(ds_work)

            elif indicator == "over_threshold":
                ds_work = ind.over_threshold(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    threshold_gui=float(threshold),
                    tolerance_gui=float(tolerance),
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                    start_gui=start_gui_ind,
                    end_gui=end_gui_ind,
                )

            st.session_state["ds"] = ds_work
            new_vars = [v for v in ds_work.data_vars if v not in prev_vars]
            log(f"Indicator '{indicator}' calculated → {new_vars}", "success")
            
            # --- Display detailed results (Summary) ---
            if "last_ind_summary" in ds_work.attrs:
                summary = ds_work.attrs["last_ind_summary"]
                st.markdown("---")
                st.subheader(f"📊 Summary : {summary.get('method', indicator)}")
                
                # Selection
                if summary.get("selections"):
                    st.markdown("**Selection:**")
                    for sel in summary["selections"]:
                        st.markdown(f"- `{sel}`")
                else:
                    st.markdown("**Selection:** none (calculated across all categories).")

                # Time and Variables
                if summary.get("new_time_dim"):
                    st.markdown(f"**New Temporal Coordinate added:** `{summary['new_time_dim']}`")

                new_vars = summary.get("new_vars", [summary.get("var_name")] if summary.get("var_name") else [])
                if new_vars and new_vars != [None]:
                    st.markdown(f"**New Variable(s) added:** {', '.join([f'`{v}`' for v in new_vars])}")

                # Dimensions and Shape
                if summary.get("dims"):
                    st.markdown(f"**Dimensions:** `{summary['dims']}`")
                if summary.get("shape"):
                    st.markdown(f"**Shape:** `{summary['shape']}`")

                if summary.get("global_mean") is not None:
                    st.markdown(f"**Global Mean on the selection:** `{summary['global_mean']:.3f}`")

                # Specific to "Peak Over Threshold" (POT)
                if indicator == "over_threshold" or summary.get("method") == "Peak Over Threshold (POT)":
                    st.info(f"💡 Effective threshold used : **{summary.get('threshold', 0):.3f}**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total exceedances", summary.get("total_exceedances", 0))
                    c2.metric("Number of episodes", summary.get("n_episodes", 0))
                    c3.metric("Mean episode duration", f"{summary.get('mean_duration', 0):.2f} steps")
                    c4.metric("Highest Peak (POT)", f"{summary.get('max_pot', 0):.3f}")
                    
                    st.warning(
                        "📌 **Which variable to use for visualization?**\n"
                        "- **`POT_deviation_...`** : Use this for a **biphasic bar chart** (shows gaps above and below threshold).\n"
                        "- **`Exceedance_Count_...`** : Use this to see the **number of days** per month/year (if resampled).\n"
                        "- **`POT_magnitude_...`** : Values only when above threshold (0 otherwise)."
                    )

                # Previews
                if summary.get("preview_data"):
                    with st.expander("👁️ Preview of the first 5 values (with dimensions)"):
                        st.markdown("**Preview table:**")
                        # preview_data is a dict (orient='list') from a pandas DataFrame
                        df_preview = pd.DataFrame(summary["preview_data"])
                        
                        # Rename columns for better readability
                        rename_map = {
                            "time": "Date",
                            "model": "Model",
                            "scenario": "Scenario",
                            0: "Value"
                        }
                        df_preview = df_preview.rename(columns=rename_map)
                        
                        # If a column name is not in rename_map, it stays as is
                        st.table(df_preview)

                elif summary.get("first_5_vals"):
                    with st.expander("👁️ Preview (Old format)"):
                        st.markdown("**Preview of first 5 values:**")
                        preview_dict = {"Value": summary["first_5_vals"]}
                        if summary.get("first_5_dates"):
                            preview_dict["Date"] = summary["first_5_dates"]
                        
                        # Set column order nicely if dates are present
                        if "Date" in preview_dict:
                            preview_dict = {"Date": preview_dict["Date"], "Value": preview_dict["Value"]}
                            
                        st.table(pd.DataFrame(preview_dict))

                st.markdown("---")

            st.success(f"✅ Indicator calculated. New variables: {new_vars}")

            if new_vars:
                with st.expander("🔍 Technical details of new variables"):
                    for nv in new_vars:
                        da_new = ds_work[nv]
                        st.markdown(f"**{nv}** — dims: `{da_new.dims}`, shape: `{da_new.shape}`")
                        try:
                            vals_flat = da_new.values.flatten().astype(float)
                            vals_flat = vals_flat[~np.isnan(vals_flat)]
                            if vals_flat.size:
                                c1, c2, c3 = st.columns(3)
                                c1.metric("Min", f"{vals_flat.min():.3f}")
                                c2.metric("Mean", f"{vals_flat.mean():.3f}")
                                c3.metric("Max", f"{vals_flat.max():.3f}")
                        except Exception:
                            pass

        except Exception as e:
            log(f"Indicator error: {e}", "error")
            st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 : VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_viz:
    st.markdown('<div class="section-title">Visualization</div>', unsafe_allow_html=True)

    chart_type = st.selectbox(
        "Chart type",
        ["Line chart", "Bar chart", "Scatter plot", "Radar chart", "Histogram"],
        key="viz_type",
    )

    vars_viz = ds_vars_and_coords()

    # ── Common configuration ───────────────────────────────────────────────
    col_v1, col_v2 = st.columns(2)
    
    # Selection of variables based on chart type
    if chart_type == "Radar chart":
        vars_multi = col_v2.multiselect("Variables (values)", ds_vars(), key="viz_radar")
        var_x = col_v1.selectbox("Categorical variable (radar axes)", vars_viz, key="viz_radar_x")
        plot_vars_ui = vars_multi
    else:
        # For all other types, we can choose X and Y
        var_x = col_v1.selectbox("X Axis (abscissa)", vars_viz, key="viz_x")
        
        if chart_type == "Scatter plot":
            var_y = col_v2.selectbox("Main Y Axis (ordinate)", ds_vars(), key="viz_y")
            vars_extra_y = st.multiselect("Additional Y variables (optional)", ds_vars(), key="viz_extra_y")
            plot_vars_ui = [var_x, var_y] + (vars_extra_y or [])
        elif chart_type == "Histogram":
            var_main = col_v2.selectbox("Variable to analyze", ds_vars(), key="viz_main")
            plot_vars_ui = [var_main]
        else: # Line or Bar
            var_main = col_v2.selectbox("Main variable (Y)", ds_vars(), key="viz_main")
            vars_extra = st.multiselect("Additional variables (optional)", ds_vars(), key="viz_extra")
            plot_vars_ui = [var_main] + (vars_extra or [])

    # Categorical filters (Variable-specific)
    viz_filters = {}
    if plot_vars_ui:
        ds_viz = st.session_state["ds"]
        standard_dims = ['time', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y', 'station', 'piezometre','month']
        
        has_cat = False
        for v in plot_vars_ui:
            if v in ds_viz:
                if any(d not in standard_dims and not str(d).startswith('time_') and ds_viz.dims.get(d, 0) > 1 for d in ds_viz[v].dims):
                    has_cat = True
                    break
                    
        if has_cat:
            with st.expander(
                "🔎 Categorical filters (scenarios, models…) - Variable-specific",
            ):
                st.info(
                    "💡 **Categorical filters**: Select specific values for one or more categories. "
                    "Ex: by selecting `model = model1` you only plot this model. "
                    "Leave empty = the **mean** of all values of this dimension will be calculated automatically. "
                    "Select multiple values = one curve per value."
                )
                
                for i, var_n in enumerate(plot_vars_ui):
                    if var_n not in ds_viz: continue
                    da_viz = ds_viz[var_n]
                    cat_dims = [d for d in list(da_viz.dims) if d not in standard_dims and not str(d).startswith('time_') and ds_viz.dims.get(d, 0) > 1]
                    
                    if not cat_dims: continue
                    
                    st.markdown(f"**For `{var_n}` :**")
                    cols = st.columns(len(cat_dims))
                    var_dict = {}
                    for j, dim in enumerate(cat_dims):
                        options = [str(val) for val in ds_viz[dim].values.tolist()]
                        selected_vals = cols[j].multiselect(
                            f"{dim}", options, default=[], 
                            key=f"viz_filt_{i}_{var_n}_{dim}"
                        )
                        if selected_vals:
                            var_dict[dim] = [val for val in ds_viz[dim].values if str(val) in selected_vals]
                    
                    if var_dict:
                        viz_filters[var_n] = var_dict
                        
                    if i < len(plot_vars_ui) - 1:
                        st.markdown("---")

        # Specific options depending on the type
        st.markdown("---")

        if chart_type in ["Line chart", "Scatter plot", "Bar chart", "Radar chart"]:
            show_envelope = st.checkbox(
                "Show uncertainty envelope (min-max range between models/scenarios/categories)",
                value=False,
                help=(
                    "If your dataset contains multiple models or scenarios, the envelope represents "
                    "the range of possible values between the minimum and maximum of all available models at each point. "
                    "For Line/Scatter/Radar, it shows a shaded area or error bars. For Bar charts, it adds error bars on each bar."
                )
            )
            env_type = "average"
            if show_envelope:
                st.info(
                    "**Envelope**: The shaded area represents the interval "
                    "[min, max] calculated on all models or scenarios for each time step. "
                    "This allows visualizing the dispersion related to climatic projections. "
                    "Mode 'average': The shaded area shows the dispersion; the central line = the mean or the selected model(s)" +
                    ("\nMode 'individual': All unselected models are plotted inside the envelope (only Line/Scatter/Radar)" if chart_type != "Bar chart" else "")
                )
                
                env_options = ["average"]
                if chart_type not in ["Bar chart", "Radar chart"]:
                    env_options.append("individual")

                env_type = st.radio(
                    "Central curve of the envelope",
                    env_options,
                    index=0,
                    horizontal=True,
                    help="'average' plots the mean of all models. 'individual' plots a curve per model inside the envelope."
                )
            st.session_state["viz_envelope"] = show_envelope
            st.session_state["viz_env_type"] = env_type
            
        elif chart_type == "Histogram":
            nb_bins = st.number_input(
                "Number of bins",
                min_value=1, max_value=200, value=10,
                help=(
                    "Determines the resolution of the histogram. "
                    "Few bins = global view of the distribution. "
                    "Many bins = fine detail but noisier. "
                    "Rule of thumb: √(number of values) is a good starting point."
                )
            )
            st.session_state["viz_bins"] = nb_bins
            
            # ── Guard B3: period_grouping _by_period ➜ Histogram ──
            if any("_by_period" in v for v in plot_vars_ui if v):
                st.warning(
                    "⚠️ **Variable '_by_period' in Histogram**: This variable contains artificial `NaN` values used "
                    "to align periods of different lengths. While the Histogram automatically filters them, "
                    "make sure not to choose a time dimension as the X axis, as it no longer exists."
                )

    # ── Guard A1: Check if the selected variable's time dim is string-based (e.g. monthly climatology) ──
    _ds_check = st.session_state.get("ds")
    _has_real_time_dim = False
    _has_grouped_time_dim = False
    _pot_magnitude_selected = False
    _all_constant_selected = False
    if _ds_check is not None and plot_vars_ui:
        for _pv in plot_vars_ui:
            if _pv not in _ds_check: continue
            _da_check = _ds_check[_pv]
            for _d in _da_check.dims:
                # Check for various time-related dimension names
                _low_d = _d.lower()
                if any(s in _low_d for s in ["time", "month", "year", "season", "per", "day"]):
                    _coord_vals = _ds_check[_d].values if _d in _ds_check.coords else None
                    if _coord_vals is not None and len(_coord_vals) > 0:
                        import numpy as np
                        if np.issubdtype(np.array(_coord_vals).dtype, np.datetime64):
                            # Check it's not a grouped indicator dim (e.g. time_Group_1m)
                            if "_Group_" in _d or "_group_" in _d:
                                _has_grouped_time_dim = True
                            else:
                                _has_real_time_dim = True
            # POT magnitude check
            if _pv.startswith("POT_magnitude"):
                _pot_magnitude_selected = True
            # All-constant values check (broadcasted percentile/mean)
            try:
                _vals_flat = _da_check.values.ravel().astype(float)
                _vals_flat = _vals_flat[np.isfinite(_vals_flat)]
                if len(_vals_flat) > 1 and float(np.max(_vals_flat) - np.min(_vals_flat)) < 1e-10:
                    _all_constant_selected = True
            except Exception:
                pass

    # Time period filter — always visible if any time-like dim exists
    t_dims_viz = time_like_dims()
    start_viz = None
    end_viz   = None
    if t_dims_viz:
        with st.expander(
            "⏳ Temporal filtering",
        ):
            if not _has_real_time_dim:
                if _has_grouped_time_dim:
                    st.warning(
                        "⚠️ **Attention**: The selected variable uses a grouped time dimension "
                        "(e.g. `time_Group_1m`). Filtering by date might not work as expected on this type of dimension. "
                        "It is recommended to filter the time *before* calculating the indicators."
                    )
                else:
                    st.warning(
                        "⚠️ **Attention**: The selected variable does not have a continuous datetime dimension "
                        "(e.g. Month). Filtering by date might not work correctly. "
                        "You should filter the time *before* grouping or calculating results."
                    )
            
            st.info(
                "💡 **Temporal filtering**: Select the period to display on the chart. "
                "The chosen period will appear in the chart title. "
                "Leave default (min/max) = display all available history."
            )
            
            try:
                t_v = pd.to_datetime(st.session_state["ds"][t_dims_viz[0]].values)
                c1, c2 = st.columns(2)
                d_s = c1.date_input("Start", value=t_v.min().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_ds")
                d_e = c2.date_input("End",   value=t_v.max().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_de")
                start_viz = str(d_s)
                end_viz   = str(d_e)
            except Exception:
                st.error("⚠️ Error while parsing dates from the time dimension. Filtering might be unstable.")

    # ── Style options and zoom ──────────────────────────────────────────────
    with st.expander("🎨 Style options & 🔍 Zoom / Axis sliders"):
        col_t, col_xl, col_yl = st.columns(3)
        p_title  = col_t.text_input("Chart title", "", help="Main title displayed at the top of the chart.")
        p_xlabel = col_xl.text_input("X-axis label", "", help="Name of the horizontal axis (e.g. 'Time', 'Precipitation (mm/d)').")
        p_ylabel = col_yl.text_input("Y-axis label", "", help="Name of the vertical axis (e.g. 'Discharge (m³/s)', 'Temperature (°C)').")
        
        st.markdown("---")
        st.markdown(
            "**🔍 Manual zoom — Axis sliders**",
            help=(
                "Set the display limits of the axes. "
                "Leave the sliders at their min/max values to display all data. "
                "Useful for zooming in on a specific range of values."
            )
        )
        st.caption("💡 Move the sliders to zoom in on a range of values. Data outside the range will not be displayed.")

        # Compute data range dynamically for sliders
        _ds_cur = st.session_state.get("ds")
        _y_min_g, _y_max_g = 0.0, 1.0
        _x_min_g, _x_max_g = 0.0, 1.0

        if _ds_cur is not None and plot_vars_ui:
            _is_x_temporal = False
            try:
                _num_vars = [v for v in plot_vars_ui if v in _ds_cur and np.issubdtype(_ds_cur[v].dtype, np.number)]
                if _num_vars:
                    _all_y = np.concatenate([_ds_cur[v].values.ravel() for v in _num_vars])
                    _all_y = _all_y[np.isfinite(_all_y)]
                    if len(_all_y) > 0:
                        _y_min_g = float(_all_y.min())
                        _y_max_g = float(_all_y.max())
            except Exception:
                pass

            try:
                if var_x in _ds_cur:
                    import pandas as pd
                    # Temporal detection
                    if np.issubdtype(_ds_cur[var_x].dtype, np.datetime64) or pd.api.types.is_datetime64_any_dtype(_ds_cur[var_x].dtype):
                        _is_x_temporal = True
                        _all_x = _ds_cur[var_x].values
                        _x_min_g = pd.to_datetime(_all_x).min().date()
                        _x_max_g = pd.to_datetime(_all_x).max().date()
                    # Numeric detection
                    elif np.issubdtype(_ds_cur[var_x].dtype, np.number):
                        _all_x = _ds_cur[var_x].values.ravel()
                        _all_x = _all_x[np.isfinite(_all_x)]
                        if len(_all_x) > 0:
                            _x_min_g = float(_all_x.min())
                            _x_max_g = float(_all_x.max())
            except Exception:
                pass

        _y_range = _y_max_g - _y_min_g if _y_max_g != _y_min_g else 1.0
        _x_range = _x_max_g - _x_min_g if _x_max_g != _x_min_g else 1.0
        _y_step = float(f"{_y_range / 100:.4g}")
        if _is_x_temporal:
            _x_step = None # Step is not used for date sliders by default or handled by Streamlit
        else:
            _x_step = float(f"{_x_range / 100:.4g}")

        col_sly, col_slx = st.columns(2)

        with col_sly:
            use_y_zoom = st.checkbox("Enable Y-axis zoom", value=False, key="use_y_zoom")
            if use_y_zoom:
                y_slider = st.slider(
                    "Y-axis range",
                    min_value=float(_y_min_g),
                    max_value=float(_y_max_g),
                    value=(float(_y_min_g), float(_y_max_g)),
                    step=_y_step,
                    key="y_slider",
                    help=f"Y variable values: from {_y_min_g:.4g} to {_y_max_g:.4g}."
                )
                z_ymin, z_ymax = y_slider
            else:
                z_ymin, z_ymax = None, None

        with col_slx:
            use_x_zoom = st.checkbox("Enable X-axis zoom", value=False, key="use_x_zoom")
            if use_x_zoom:
                if _is_x_temporal:
                    x_slider = st.slider(
                        "X-axis range (dates)",
                        min_value=_x_min_g,
                        max_value=_x_max_g,
                        value=(_x_min_g, _x_max_g),
                        key="x_slider",
                        help=f"X period: from {_x_min_g} to {_x_max_g}."
                    )
                else:
                    x_slider = st.slider(
                        "X-axis range",
                        min_value=float(_x_min_g),
                        max_value=float(_x_max_g),
                        value=(float(_x_min_g), float(_x_max_g)),
                        step=_x_step,
                        key="x_slider",
                        help=f"X variable values: from {_x_min_g:.4g} to {_x_max_g:.4g}."
                    )
                z_xmin, z_xmax = x_slider
            else:
                z_xmin, z_xmax = None, None

        st.markdown("---")
        st.markdown(
            "📐 **Threshold lines (reference on the chart)**",
        )
        st.caption(
            "💡 Draw horizontal (Y) or vertical (X) lines on the chart to indicate a threshold or reference. "
            "Ex: draw Y=0 for the zero line, or X=1980 to mark a key year. Leave empty = no line."
        )
        col_thr_y, col_thr_x = st.columns(2)
        th_y_vals_raw = col_thr_y.text_input(
            "Horizontal Y threshold(s) (variable value)",
            value="",
            key="thresh_y",
            help=(
                "Enter one or more comma-separated numeric values to draw horizontal lines. "
                "Ex: '0' draws the zero line. '100, 200' draws two lines Y=100 and Y=200. "
                "Useful for visualizing a flood threshold, drought threshold, reference value..."
            )
        )
        th_x_vals_raw = col_thr_x.text_input(
            "Vertical X threshold(s) (X axis value)",
            value="",
            key="thresh_x",
            help=(
                "Enter one or more comma-separated values to draw vertical lines. "
                "Works if the X axis is numeric. For a time axis, enter a year (e.g. '1980'). "
                "Ex: '1980' draws a vertical line at the year 1980."
            )
        )
        col_thr_col, col_thr_sty = st.columns(2)
        thresh_color = col_thr_col.color_picker(
            "Threshold lines color", "#FF4B4B", key="thresh_color",
            help="Color applied to all threshold lines."
        )
        thresh_style = col_thr_sty.selectbox(
            "Line style",
            ["--", "-", "-.", ":"],
            key="thresh_style",
            help="Style du trait : -- = tirets, - = plein, -. = tiret-point, : = pointé."
        )

        st.markdown("---")
        col_save, col_fmt = st.columns(2)
        save_fig = col_save.checkbox("Save figure", value=False)
        save_fmt = col_fmt.selectbox("Format", ["png", "pdf", "svg"], key="save_fmt")
        save_path = ""
        if save_fig:
            save_path = st.text_input("Save path (e.g. output/fig.png)", "output/figure.png", key="save_path")

    x_lim_val = [z_xmin, z_xmax] if (z_xmin is not None or z_xmax is not None) else None
    y_lim_val = [z_ymin, z_ymax] if (z_ymin is not None or z_ymax is not None) else None

    # Parsing thresholds
    h_lines = [float(x.strip()) for x in th_y_vals_raw.split(",") if x.strip()] if th_y_vals_raw else []
    v_lines = []
    if th_x_vals_raw:
        for x in th_x_vals_raw.split(","):
            x = x.strip()
            if not x: continue
            try: v_lines.append(pd.to_datetime(x))
            except:
                try: v_lines.append(float(x))
                except: v_lines.append(x)

    plot_config_gui = {
        "title":    p_title  or None,
        "xlabel":   p_xlabel or None,
        "ylabel":   p_ylabel or None,
        "save_path": save_path if save_fig else None,
        "x_limits": x_lim_val,
        "y_limits": y_lim_val,
        "h_lines": h_lines,
        "v_lines": v_lines,
        "thresh_color": thresh_color,
        "thresh_style": thresh_style
    }

    # ── Plot button ────────────────────────────────────────────────────────

    # ── Guard B1: rolling_mean → bar chart ──────────────────────────────
    if chart_type == "Bar chart" and any(v.startswith("rolling_mean") for v in plot_vars_ui if v):
        st.warning(
            "⚠️ **Chart type mismatch**: The selected variable is a **rolling mean** (continuous time series). "
            "A **Bar chart** is adapted for discrete aggregated values (e.g. monthly means, annual indicators). "
            "➡️ Consider using a **Line chart** instead for better readability."
        )

    # ── Guard B2/A3: all-constant variable (broadcasted statistic) → line/scatter ──
    if _all_constant_selected and chart_type in ["Line chart", "Scatter plot"]:
        st.warning(
            "⚠️ **Constant variable detected**: The selected variable has the same value at every time step. "
            "This usually happens when a **Percentile** or **Mean** was reduced over `time` and then broadcast back. "
            "The chart will display a flat horizontal line. This is mathematically correct but may not be what you expect."
        )

    # ── Guard A4: POT magnitude → histogram ─────────────────────────────
    if chart_type == "Histogram" and _pot_magnitude_selected:
        st.warning(
            "⚠️ **Histogram of POT_magnitude**: This variable contains artificial zeros (all values below the "
            "threshold are replaced by 0). The histogram will be dominated by these zeros and will not "
            "faithfully represent the distribution of exceedance episodes. "
            "➡️ Use `POT_deviation_*` instead for a biphasic Bar chart, or filter zeros manually before visualizing."
        )

    # ── Guard B4: radar chart with too many categories ───────────────────
    if chart_type == "Radar chart" and _ds_check is not None:
        _cat_var = var_x if 'var_x' in dir() else None
        if _cat_var and _cat_var in _ds_check:
            _n_cats = _ds_check[_cat_var].size
            if _n_cats > 30:
                st.error(
                    f"🚫 **Radar chart impossible**: The variable `{_cat_var}` contains **{_n_cats} values**. "
                    "A Radar chart requires a small number of categories (max ~30, ideally ≤ 12). "
                    "➡️ Apply a **Climatologie Mensuelle** first to group data by month, or choose a categorical variable "
                    "(model, scenario, season…) with fewer values."
                )

    if st.button("📈 Plot", key="run_viz"):
        ds_work = st.session_state["ds"]

        # Temporal subset if requested
        ds_plot = ds_work
        if t_dims_viz and start_viz and end_viz:
            for dim in t_dims_viz:
                try:
                    ds_plot = ds_plot.sel({dim: slice(start_viz, end_viz)})
                except Exception:
                    pass

        try:
            fig = None

            # Always pass auto_mean_gui=True and dim_selections_gui={} so that
            # handle_xarray_dimensions never prompts the terminal.
            # The plot_config_gui dict provides labels from the Streamlit sidebar.
            gui_config = {
                "xlabel": plot_config_gui.get("xlabel") or "",
                "ylabel": plot_config_gui.get("ylabel") or "",
                "title": plot_config_gui.get("title") or "",
                "x_limits": plot_config_gui.get("x_limits"),
                "y_limits": plot_config_gui.get("y_limits"),
                "h_lines": plot_config_gui.get("h_lines"),
                "v_lines": plot_config_gui.get("v_lines"),
                "thresh_color": plot_config_gui.get("thresh_color"),
                "thresh_style": plot_config_gui.get("thresh_style"),
            }

            if chart_type == "Line chart":
                plot_vars = [var_main] + (vars_extra or [])
                fig = viz.line_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=plot_vars,
                    start_gui=start_viz,
                    end_gui=end_viz,
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters,
                    plot_envelope_gui=st.session_state.get("viz_envelope", False),
                    envelope_type_gui=st.session_state.get("viz_env_type", "average")
                )

            elif chart_type == "Bar chart":
                plot_vars = [var_main] + (vars_extra or [])
                fig = viz.bar_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=plot_vars,
                    start_gui=start_viz,
                    end_gui=end_viz,
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters,
                    plot_envelope_gui=st.session_state.get("viz_envelope", False),
                    envelope_type_gui=st.session_state.get("viz_env_type", "average")
                )

            elif chart_type == "Scatter plot":
                plot_vars_y = [var_y] + (vars_extra_y or [])
                fig = viz.scatter_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=plot_vars_y,
                    start_gui=start_viz,
                    end_gui=end_viz,
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters,
                    plot_envelope_gui=st.session_state.get("viz_envelope", False),
                    envelope_type_gui=st.session_state.get("viz_env_type", "average")
                )

            elif chart_type == "Radar chart":
                if not vars_multi:
                    st.warning("Please select at least two variables for the radar chart.")
                else:
                    fig = viz.radar_chart(
                        ds_plot, 
                        var_gui=vars_multi,
                        cat_name_gui=var_x,
                        start_gui=start_viz,
                        end_gui=end_viz,
                        plot_config_gui=gui_config,
                        dim_selections_gui=viz_filters,
                        auto_mean_gui=True,
                        plot_envelope_gui=st.session_state.get("viz_envelope", False),
                        envelope_type_gui=st.session_state.get("viz_env_type", "average")
                    )

            elif chart_type == "Histogram":
                fig = viz.histogram_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    col_name_gui=var_main,
                    bins_gui=st.session_state.get("viz_bins", 10),
                    start_gui=start_viz,
                    end_gui=end_viz,
                    plot_config_gui=gui_config,
                    dim_selections_gui=viz_filters,
                    auto_mean_gui=True
                )

            if fig is not None:
                # ── Threshold lines ─────────────────────
                _tc = st.session_state.get("thresh_color", "#FF4B4B")
                _ts = st.session_state.get("thresh_style", "--")
                _th_y_raw = st.session_state.get("thresh_y", "")
                _th_x_raw = st.session_state.get("thresh_x", "")

                def _parse_thresh(raw):
                    vals = []
                    for tok in str(raw).split(","):
                        tok = tok.strip()
                        if tok:
                            try:
                                vals.append(float(tok))
                            except ValueError:
                                pass
                    return vals

                _th_y_vals = _parse_thresh(_th_y_raw)
                _th_x_vals = _parse_thresh(_th_x_raw)

                if _th_y_vals or _th_x_vals:
                    for ax_t in fig.get_axes():
                        for yv in _th_y_vals:
                            ax_t.axhline(y=yv, color=_tc, linestyle=_ts, linewidth=1.4,
                                         label=f"Threshold Y={yv:.4g}", zorder=10)
                        for xv in _th_x_vals:
                            ax_t.axvline(x=xv, color=_tc, linestyle=_ts, linewidth=1.4,
                                         label=f"Threshold X={xv:.4g}", zorder=10)
                        # Refresh legend if new lines were added
                        handles, labels_leg = ax_t.get_legend_handles_labels()
                        if handles:
                            ax_t.legend(handles, labels_leg, loc="upper center",
                                        bbox_to_anchor=(0.5, -0.15), ncol=min(4, len(handles)))
                    fig.tight_layout()

                st.pyplot(fig, use_container_width=True)


                # ── Download ────────────────────────────────────────
                buf = io.BytesIO()
                fmt = save_fmt if save_fig else "png"
                fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
                buf.seek(0)
                fname = os.path.splitext(os.path.basename(save_path))[0] if (save_fig and save_path) else "figure"
                st.download_button(
                    label=f"⬇️ Download ({fmt.upper()})",
                    data=buf,
                    file_name=f"{fname}.{fmt}",
                    mime=f"image/{fmt}",
                )
                log(f"Chart '{chart_type}' generated.", "success")

        except Exception as e:
            log(f"Visualization error: {e}", "error")
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT CSV OF CREATED VARIABLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">⬇️ Export variables to CSV</div>', unsafe_allow_html=True)

with st.expander("📊 Download calculated variables", expanded=False):
    st.info(
        "💡 **How to use this export**: Select one or more variables below "
        "(including indicators and statistics you just calculated) and download them as CSV. "
        "The file will contain all dimensions as columns (date, model, scenario...) "
        "followed by the values of each selected variable."
    )
    
    all_vars_export = list(st.session_state["ds"].data_vars)
    export_vars = st.multiselect(
        "Variables to export",
        all_vars_export,
        default=[],
        key="export_vars",
        help=(
            "Select the variables to include in the CSV file. "
            "You can export all your original variables as well as those calculated "
            "(indicators, statistics...). Example: selecting 'Qmean_1m_discharge' will export "
            "the monthly mean discharge with date and value columns."
        )
    )

    if export_vars:
        try:
            ds_export = st.session_state["ds"][export_vars]
            
            # Determine if dataset has mixed time dimensions (some vars may have different time coords)
            export_dfs = []
            for v in export_vars:
                try:
                    df_v = st.session_state["ds"][v].to_dataframe().reset_index()
                    export_dfs.append(df_v)
                except Exception:
                    pass
            
            if export_dfs:
                # Try a simple merge if all have the same index, else concat
                try:
                    if len(export_dfs) == 1:
                        df_final = export_dfs[0]
                    else:
                        # Merge on common index columns
                        df_final = export_dfs[0]
                        for df_next in export_dfs[1:]:
                            common_cols = [c for c in df_final.columns if c in df_next.columns
                                         and c not in export_vars]
                            if common_cols:
                                df_final = pd.merge(df_final, df_next, on=common_cols, how='outer')
                            else:
                                df_final = pd.concat([df_final, df_next], axis=1)
                except Exception:
                    df_final = pd.concat(export_dfs, axis=0, ignore_index=True)

                # Format datetime columns for CSV readability
                for col in df_final.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_final[col]):
                        df_final[col] = df_final[col].dt.strftime("%Y-%m-%d")

                st.markdown(f"**CSV Preview ({len(df_final):,} rows, {len(df_final.columns)} columns):**")
                st.dataframe(df_final.head(10), use_container_width=True)

                csv_buffer = io.StringIO()
                df_final.to_csv(csv_buffer, index=False, float_format="%.6g")
                csv_bytes = csv_buffer.getvalue().encode("utf-8")

                export_filename = "_".join(export_vars[:3]) + "_export.csv"
                st.download_button(
                    label=f"⬇️ Download CSV ({len(df_final):,} rows)",
                    data=csv_bytes,
                    file_name=export_filename,
                    mime="text/csv",
                    key="csv_download_btn",
                )
                st.caption(f"📁 File: `{export_filename}` — Columns: {', '.join(df_final.columns.tolist())}")
            else:
                st.warning("Cannot convert selected variables to table.")

        except Exception as e:
            st.error(f"Error during export: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.caption("Select at least one variable to enable download.")


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption("Projet Mention Ressources Energétiques 2026 — Streamlit GUI | Climatic & Hydrological Data xArray")
