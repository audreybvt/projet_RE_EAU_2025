"""
gui_streamlit_xarray.py
Interface graphique Streamlit pour le projet RE_EAU 2025.
Permet de charger des fichiers NetCDF ou CSV, calculer des indicateurs
hydrologiques, des statistiques et générer des visualisations.
"""
from __future__ import annotations

import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np
import os
import io
import tempfile

# ── Modules du projet ──────────────────────────────────────────────────────────
import data_formatting as df_mod
import statistics_xr   as stats
import indicators_xr   as ind
import visualization_xr as viz

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="RE_EAU 2025 – Analyse Hydrologique",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé ───────────────────────────────────────────────────────────
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
        "ds": None,        # Dataset xarray courant
        "ds_info": {},     # Métadonnées du dataset
        "logs": [],        # Historique des opérations
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
        with st.expander("🔎 Filtres catégoriels (scénarios, modèles…)"):
            if key_prefix == "ind":
                st.info("💡 Sélectionner des valeurs de catégorie si vous voulez travailler sur un modèle spécifique par exemple.")
            for dim in cat_dims:
                vals = ds[dim].values.tolist()
                options = [str(v) for v in vals]
                
                # In Viz tab (if key_prefix is 'viz'), use multiselect
                if "viz" in key_prefix:
                    selected_vals = st.multiselect(f"Filtre pour '{dim}'", options, default=[], key=f"{key_prefix}_{dim}")
                    if selected_vals:
                        # Map back to original values
                        orig_vals = ds[dim].values
                        matches = [v for v in orig_vals if str(v) in selected_vals]
                        dict_filters[dim] = matches
                else:
                    # In Ind tab, stay with single select for now (standard behavior)
                    selected_val = st.selectbox(f"Filtre pour '{dim}'", ["(Tout)"] + options, key=f"{key_prefix}_{dim}")
                    if selected_val != "(Tout)":
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
        
        with st.expander("📅 Filtrage temporel (période d'analyse)"):
            st.info(
                "💡 **Filtrage temporel** : Sélectionnez la période sur laquelle vous voulez effectuer le calcul. "
                ) 
            st.info(f"Période disponible : {min_dt} au {max_dt}")
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Date de début", min_dt, min_value=min_dt, max_value=max_dt, key=f"{key_prefix}_start")
            end_date = c2.date_input("Date de fin", max_dt, min_value=min_dt, max_value=max_dt, key=f"{key_prefix}_end")
            
        return str(start_date), str(end_date)
    except Exception:
        return None, None


def time_like_dims() -> list[str]:
    return [d for d in ds_dims() if "time" in d.lower()]


def has_dataset() -> bool:
    return st.session_state["ds"] is not None


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR – Chargement de données
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💧 RE_EAU 2025")
    st.markdown("---")

    # ── Format ──────────────────────────────────────────────────────────────
    st.markdown("### 📁 Chargement des données")
    file_format = st.radio("Format du fichier", ["NetCDF (.nc)", "CSV (.csv)", "Excel (.xlsx)"], horizontal=True)

    # ── Uploader ─────────────────────────────────────────────────────────────
    if file_format.startswith("NetCDF"):
        uploaded_files = st.file_uploader(
            "Glissez-déposez un ou plusieurs fichiers NetCDF",
            type=["nc"],
            accept_multiple_files=True,
            key="nc_uploader",
        )
    elif file_format.startswith("CSV"):
        uploaded_files = st.file_uploader(
            "Glissez-déposez un fichier CSV",
            type=["csv"],
            accept_multiple_files=False,
            key="csv_uploader",
        )
        skip_n = st.number_input("Lignes de métadonnées à ignorer", min_value=0, value=0, step=1)
    else:  # Excel
        uploaded_files = st.file_uploader(
            "Glissez-déposez un fichier Excel",
            type=["xlsx", "xls"],
            accept_multiple_files=False,
            key="excel_uploader",
        )

    st.markdown("---")

    # ── Options spatiales (NetCDF) ───────────────────────────────────────────
    if file_format.startswith("NetCDF"):
        st.markdown("### 🗺️ Sélection spatiale")
        spatial_mode = st.selectbox(
            "Mode de sélection spatiale",
            [
                "Conserver tout",
                "Sélectionner un point par index",
                "Sélectionner un point (lat/lon)",
                "Sélectionner une région (lat/lon)",
            ],
        )

        spatial_gui_extra = {}
        if spatial_mode == "Sélectionner un point par index":
            pt_idx = st.number_input("Index du point", min_value=0, value=0, step=1)
            spatial_gui_extra = {"method_gui": 1, "idx_gui": int(pt_idx)}

        elif spatial_mode == "Sélectionner un point (lat/lon)":
            col_lat, col_lon = st.columns(2)
            pt_lat = col_lat.number_input("Latitude", value=0.0, format="%.4f")
            pt_lon = col_lon.number_input("Longitude", value=0.0, format="%.4f")
            spatial_gui_extra = {"method_gui": 2, "lat_gui": pt_lat, "lon_gui": pt_lon}

        elif spatial_mode == "Sélectionner une région (lat/lon)":
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

    # ── Bouton de chargement ─────────────────────────────────────────────────
    load_btn = st.button("⬆️ Charger le dataset", use_container_width=True)

    if load_btn:
        if not uploaded_files:
            st.error("Veuillez sélectionner au moins un fichier.")
        else:
            with st.spinner("Chargement en cours…"):
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

                        if spatial_mode == "Conserver tout":
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

                            if spatial_mode == "Sélectionner un point par index" and has_pts:
                                target = ('points', 'select')
                            elif spatial_mode == "Sélectionner un point (lat/lon)" and has_grid:
                                target = ('grid', 'point')
                            elif spatial_mode == "Sélectionner une région (lat/lon)" and has_grid:
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

                        # Choisir mode de chargement (simple vs multi-fichiers)
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
                            if spatial_mode == "Sélectionner un point par index" and "idx_gui" in spatial_gui_extra:
                                if has_pts:
                                    pt_dim = next(d for d in ['piezometre', 'station', 'stations', 'site', 'sites'] if d in ds_raw.dims)
                                    ds_loaded = df_mod.select_spatial_point(
                                        ds_raw, {'points': [pt_dim]}, {'points': [pt_dim]},
                                        method_gui=1, idx_gui=spatial_gui_extra["idx_gui"]
                                    )

                            elif spatial_mode == "Sélectionner un point (lat/lon)" and "lat_gui" in spatial_gui_extra:
                                if has_grid:
                                    g = next((['latitude', 'longitude'] if 'latitude' in ds_raw.dims else None) or
                                             (['lat', 'lon'] if 'lat' in ds_raw.dims else None) or
                                             (['x', 'y']), None)
                                    if g:
                                        ds_loaded = df_mod.select_spatial_point(
                                            ds_raw, {'grid': [g[0], g[1]]}, {'grid': [g[0], g[1]]},
                                            method_gui=2, lat_gui=spatial_gui_extra["lat_gui"], lon_gui=spatial_gui_extra["lon_gui"]
                                        )

                            elif spatial_mode == "Sélectionner une région (lat/lon)" and "region_gui" in spatial_gui_extra:
                                has_lat = next((d for d in ['latitude', 'lat'] if d in ds_raw.dims), None)
                                has_lon = next((d for d in ['longitude', 'lon'] if d in ds_raw.dims), None)
                                if has_lat and has_lon:
                                    ds_loaded = df_mod.select_spatial_region(
                                        ds_raw, [has_lat, has_lon], [has_lat, has_lon],
                                        region_gui=spatial_gui_extra["region_gui"]
                                    )
                        else:
                            # Multi-fichiers
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
                        st.info("Conversion de l'Excel en format long en cours...")
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

                    log("Dataset chargé avec succès.", "success")
                    st.success("✅ Dataset chargé !")

                except Exception as e:
                    log(f"Erreur de chargement : {e}", "error")
                    st.error(f"Erreur : {e}")

    st.markdown("---")
    # ── Logs ─────────────────────────────────────────────────────────────────
    with st.expander("📋 Journaux"):
        for line in reversed(st.session_state["logs"][-30:]):
            st.caption(line)
        if st.button("🗑️ Effacer les logs"):
            st.session_state["logs"] = []


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>💧 RE_EAU 2025 – Analyse Hydrologique</h1>
    <p>Interface graphique pour l'analyse de données climatiques et hydrologiques (xArray)</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  APERÇU DU DATASET
# ══════════════════════════════════════════════════════════════════════════════
if has_dataset():
    ds = st.session_state["ds"]

    with st.expander("📊 Aperçu du Dataset", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Variables", len(ds.data_vars))
        c2.metric("Dimensions", len(ds.dims))
        n_pts = 1
        for s in ds.sizes.values():
            n_pts *= s
        c3.metric("Taille totale", f"{n_pts:,}")
        t_dims = time_like_dims()
        if t_dims:
            try:
                t_vals = pd.to_datetime(ds[t_dims[0]].values)
                c4.metric("Période", f"{t_vals.min().date()} → {t_vals.max().date()}")
            except Exception:
                c4.metric("Dimension temps", t_dims[0])

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Dimensions / Catégories**")
            dim_rows = []
            for d, size in ds.dims.items():
                extrait = ""
                if d in ds.coords:
                    c_vals = ds[d].values
                    if size <= 10 or str(c_vals.dtype).startswith('<U') or str(c_vals.dtype) == 'object':
                        # Petites listes ou texte : on affiche le contenu
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
                    extrait = "Pas de coord."
                dim_rows.append({"Dimension": d, "Nb Valeurs": size, "Extrait / Plage": extrait})
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
                    "Aperçu — date | catégorie | valeur (5 premières lignes non-NaN)": extrait_str
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.caption("💡 Chaque ligne montre jusqu'à 3 exemples de valeurs avec leur date et leur contexte catégoriel (modèle, scénario…).")

else:
    st.info("👈 Chargez un fichier depuis le panneau latéral pour commencer.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  ONGLETS PRINCIPAUX
# ══════════════════════════════════════════════════════════════════════════════
tab_stat, tab_ind, tab_viz = st.tabs([
    "📐 Statistiques",
    "📏 Indicateurs hydrologiques",
    "📈 Visualisation",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 : STATISTIQUES
# ══════════════════════════════════════════════════════════════════════════════
with tab_stat:
    st.markdown('<div class="section-title">Calculs Statistiques</div>', unsafe_allow_html=True)

    stat_func = st.selectbox(
        "Opération statistique",
        [
            "Moyenne flexible",
            "Maximum flexible",
            "Minimum flexible",
            "Médiane flexible",
            "Percentile flexible",
            "Moyenne glissante (rolling)",
            "Moyenne interannuelle mensuelle",
            "Groupement par périodes",
        ],
        help=(
            "Choisissez le type de calcul à effectuer sur votre variable. "
            "'Flexible' signifie que vous choisissez sur quelles dimensions agréger le calcul. "
            "Ex: Moyenne flexible sur 'time' = une valeur unique pour toute la période. "
            "Ex: Moyenne flexible sur 'modèle' = une moyenne des modèles chaque jour. "
            "Moyenne glissante = lisse une série en moyennant sur une fenêtre mobile (idéal pour détecter des tendances). "
            "Groupement par périodes = crée des catégories P1/P2/… que vous pouvez comparer dans les graphiques."
        )
    )

    vars_list = ds_vars()
    all_dims  = ds_dims()

    col1, col2 = st.columns(2)

    with col1:
        var_name = st.selectbox(
            "Variable source",
            vars_list,
            key="stat_var",
            help=(
                "Variable sur laquelle effectuer le calcul statistique. "
                "Toutes les variables du dataset sont disponibles, y compris celles calculées précédemment "
                "(indicateurs hydrologiques, etc.)."
            )
        )

    if var_name:
        avail_dims = list(st.session_state["ds"][var_name].dims)
    else:
        avail_dims = all_dims

    with col2:
        if stat_func not in ("Moyenne interannuelle mensuelle", "Moyenne glissante (rolling)", "Groupement par périodes"):
            dims_sel = st.multiselect(
                "Agréger sur ces axes (calculer une valeur unique par combinaison restante)",
                avail_dims,
                default=avail_dims,
                key="stat_dims",
                help=(
                    "Sélectionnez les dimensions à 'aplatir' par un calcul statistique. "
                    "Exemple 1 : si vos données ont les axes [time, model, scenario] et que vous sélectionnez "
                    "model + scenario → vous obtenez une valeur par pas de temps (moyennée sur tous les modèles et scénarios). "
                    "Exemple 2 : sélectionner uniquement 'time' → vous obtenez une seule valeur par combinaison modèle/scénario. "
                    "Laisser vide = tout agréger en une seule valeur globale."
                ),
            )
        elif stat_func == "Moyenne interannuelle mensuelle":
            t_dims_list = [d for d in avail_dims if "time" in d.lower()]
            time_dim_sel = st.selectbox(
                "Dimension temporelle",
                t_dims_list if t_dims_list else avail_dims,
                key="stat_time_dim",
                help="Choisissez la dimension qui représente le temps dans votre dataset (ex: 'time', 'time_Group_1m', etc.)."
            )
        elif stat_func == "Moyenne glissante (rolling)":
            window_val = st.number_input(
                "Taille de la fenêtre (pas de temps)",
                min_value=1, value=7, step=1,
                help="Nombre de pas de temps consécutifs utilisés pour calculer la moyenne glissante. Ex: 7 = moyenne sur 7 jours si les données sont journalières."
            )
        elif stat_func == "Groupement par périodes":
            st.markdown("**Définition des périodes de comparaison**")
            st.caption("💡 Définissez 2 périodes ou plus pour comparer. Ex : P1 = 1950–1980 et P2 = 1980–2010. "
                       "Deux nouvelles variables seront créées : la moyenne par période (idéale pour un diagramme en barres) "
                       "et la série temporelle par période (idéale pour un graphique en ligne).")

            # Manage periods list in session state
            if "stat_periods" not in st.session_state:
                st.session_state["stat_periods"] = [("P1", "", ""), ("P2", "", "")]

            col_add, col_rm = st.columns([1, 1])
            if col_add.button("➕ Ajouter une période", key="add_period"):
                n = len(st.session_state["stat_periods"]) + 1
                st.session_state["stat_periods"].append((f"P{n}", "", ""))
            if col_rm.button("➖ Supprimer la dernière", key="rm_period") and len(st.session_state["stat_periods"]) > 1:
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
                new_name = cc1.text_input(f"Nom P{pi+1}", value=p_name, key=f"pg_name_{pi}")
                try:
                    dflt_s = pd.to_datetime(p_start).date() if p_start else (_t_min or None)
                    dflt_e = pd.to_datetime(p_end).date()   if p_end else (_t_max or None)
                    new_start = cc2.date_input(f"Début P{pi+1}", value=dflt_s, min_value=_t_min, max_value=_t_max, key=f"pg_start_{pi}")
                    new_end   = cc3.date_input(f"Fin P{pi+1}",   value=dflt_e, min_value=_t_min, max_value=_t_max, key=f"pg_end_{pi}")
                except Exception:
                    new_start = cc2.text_input(f"Début P{pi+1} (YYYY-MM-DD)", value=p_start, key=f"pg_start_{pi}")
                    new_end   = cc3.text_input(f"Fin P{pi+1} (YYYY-MM-DD)",   value=p_end,   key=f"pg_end_{pi}")
                updated_periods.append((new_name, str(new_start), str(new_end)))
            st.session_state["stat_periods"] = updated_periods

            t_dims_pg = [d for d in avail_dims if "time" in d.lower()]
            time_dim_pg = st.selectbox(
                "Dimension temporelle à utiliser",
                t_dims_pg if t_dims_pg else avail_dims,
                key="pg_timedim",
                help="Choisissez la dimension temporelle de votre variable source. Habituellement 'time'."
            )

    # Période temporelle
    if stat_func not in ("Moyenne interannuelle mensuelle",):
        t_dims = time_like_dims()
        if t_dims:
            with st.expander("⏳ Filtrage temporel (optionnel)"):
                st.info(
                "💡 **Filtrage temporel** : Sélectionnez la période sur laquelle vous voulez effectuer le calcul. "
                )  
                t_vals_raw = st.session_state["ds"][t_dims[0]].values
                try:
                    t_vals = pd.to_datetime(t_vals_raw)
                    t_min, t_max = t_vals.min().date(), t_vals.max().date()
                    c_s, c_e = st.columns(2)
                    d_start = c_s.date_input("Date de début", value=t_min, min_value=t_min, max_value=t_max, key="stat_dstart")
                    d_end   = c_e.date_input("Date de fin",   value=t_max, min_value=t_min, max_value=t_max, key="stat_dend")
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

    # Percentile spécifique
    if stat_func == "Percentile flexible":
        q_val = st.slider("Percentile (%)", 1, 99, 90, key="stat_q") / 100.0

    # ── Bouton calcul ────────────────────────────────────────────────────────
    if st.button("▶️ Lancer le calcul statistique", key="run_stat"):
        ds_work = st.session_state["ds"]
        try:
            # Sécurité pour éviter name 'dims_sel' is not defined
            _dims_input = dims_sel if 'dims_sel' in locals() else None
            dims_to_reduce = _dims_input if stat_func not in ("Moyenne interannuelle mensuelle", "Moyenne glissante (rolling)", "Groupement par périodes") else None

            if stat_func == "Moyenne flexible":
                ds_work = stats.mean_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Maximum flexible":
                ds_work = stats.maximum_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Minimum flexible":
                ds_work = stats.minimum_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Médiane flexible":
                ds_work = stats.median_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Percentile flexible":
                ds_work = stats.percentile_value_flexible(
                    ds_work,
                    var_name_gui=var_name,
                    q_gui=q_val,
                    dims_to_reduce_gui=dims_to_reduce,
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Moyenne glissante (rolling)":
                ds_work = stats.rolling_mean_value(
                    ds_work,
                    var_name_gui=var_name,
                    window_gui=int(window_val),
                    start_input_gui=start_str,
                    end_input_gui=end_str,
                )

            elif stat_func == "Moyenne interannuelle mensuelle":
                ds_work = stats.monthly_interannual_average_xr(
                    ds_work,
                    var_name_gui=var_name,
                    time_dim_gui=time_dim_sel,
                )

            elif stat_func == "Groupement par périodes":
                ds_work = stats.period_grouping(
                    ds_work,
                    var_name_gui=var_name,
                    periods_gui=st.session_state.get("stat_periods", []),
                    time_dim_gui=time_dim_pg,
                )

            st.session_state["ds"] = ds_work
            new_vars = [v for v in ds_work.data_vars if v not in vars_list]
            log(f"Statistique '{stat_func}' calculée → {new_vars}", "success")
            st.success(f"✅ Calcul terminé. Nouvelles variables : {new_vars}")

            # --- Affichage du résumé statistique ---
            if "last_stat_summary" in ds_work.attrs:
                summary = ds_work.attrs["last_stat_summary"]
                st.markdown("---")
                st.subheader(f"📊 Résultats : {summary.get('method', stat_func)}")
                
                # Selection / Time period
                st.markdown(f"**Variable source:** `{summary.get('var_name', 'N/A')}`")
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

                # Affichage de l'aperçu structuré
                if "preview_data" in summary and summary["preview_data"]:
                    with st.expander("👁️ Aperçu des 5 premières valeurs (avec dimensions)"):
                        st.markdown("**Tableau d'aperçu :**")
                        df_preview = pd.DataFrame(summary["preview_data"])
                        rename_map = {
                            "time": "Date",
                            "model": "Modèle",
                            "scenario": "Scénario",
                            "period": "Période",
                            0: "Valeur"
                        }
                        st.table(df_preview.rename(columns=rename_map))

                # Fallback: moyennes par période pour Groupement par périodes
                elif "mean_per_period" in summary:
                    st.markdown("**Moyennes par période :**")
                    period_df = pd.DataFrame.from_dict(
                        summary["mean_per_period"], orient='index', columns=["Moyenne"]
                    ).rename_axis("Période")
                    st.dataframe(period_df, use_container_width=True)
                    if "periods" in summary:
                        for p, rng in summary["periods"].items():
                            st.caption(f"  {p} : {rng}")
                
                st.markdown("---")

            # Aperçu de la nouvelle variable (existant)
            if new_vars:
                with st.expander("🔍 Détails techniques des nouvelles variables"):
                    for nv in new_vars:
                        da_new = ds_work[nv]
                        st.markdown(f"**{nv}** — dims: `{da_new.dims}`, shape: `{da_new.shape}`")
                        vals_flat = da_new.values.flatten()
                        vals_flat = vals_flat[~np.isnan(vals_flat.astype(float))]
                        if vals_flat.size > 0:
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Min", f"{float(vals_flat.min()):.3f}")
                            c2.metric("Moy", f"{float(vals_flat.mean()):.3f}")
                            c3.metric("Max", f"{float(vals_flat.max()):.3f}")
                            c4.metric("Données (hors NaN)", f"{vals_flat.size:,}", help="Nombre de valeurs réelles non-nulles résultant du calcul stat.")

        except Exception as e:
            log(f"Erreur statistique : {e}", "error")
            st.error(f"Erreur : {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 : INDICATEURS hydrologiques
# ══════════════════════════════════════════════════════════════════════════════
with tab_ind:
    st.markdown('<div class="section-title">Indicateurs Hydrologiques</div>', unsafe_allow_html=True)

    indicator = st.selectbox(
        "Indicateur",
        [
            "Soil_Water_Balance_Index", 
            "Standardised Piezometric Level Indicator", 
            "Qmean", 
            "Q90/95", 
            "Q10/05", 
            "VCN10", 
            "VCX3", 
            "over_threshold"
        ],
        key="ind_select",
        help=(
            "Choisissez l'indicateur à calculer. "
            "Qmean = moyenne sur la période. "
            "Q90/95 = valeur dépassée 90\u202f% ou 95\u202f% du temps (hautes valeurs). "
            "Q10/05 = valeur dépassée seulement 10\u202f% ou 5\u202f% du temps (basses valeurs). "
            "VCN10 = minimum des moyennes glissantes sur 10 pas de temps consécutifs (extrême bas). "
            "VCX3 = maximum des moyennes sur 3 pas de temps (extrême haut). "
            "over_threshold = détecte les dépassements d'un seuil et calcule l'écart à ce seuil."
        )
    )

    vars_list_ind = ds_vars()

    # ── Filtres catégoriels et temporels ────────────────────────────────────
    dict_filters_gui = render_categorical_filters(key_prefix="ind")
    start_gui_ind, end_gui_ind = render_temporal_filters(key_prefix="ind_time")

    # ── Paramètres spécifiques à chaque indicateur ─────────────────────────
    st.markdown("**Paramètres de l'indicateur**")

    # Période temporelle
    t_dims_ind = time_like_dims()
    time_coord_ind = t_dims_ind[0] if t_dims_ind else None
    unite_gui_val = None
    nb_gui_val    = None

    if indicator in ("Qmean", "Q90/95", "Q10/05", "VCN10", "VCX3", "over_threshold"):
        col_tc, col_unit, col_nb = st.columns(3)
        if t_dims_ind:
            time_coord_ind = col_tc.selectbox(
                "Coordonnée temporelle",
                t_dims_ind,
                key="ind_tc",
                help=(
                    "Choisissez la dimension temporelle de votre variable. "
                    "Habituellement appelée 'time'. Si vous avez déjà calculé un indicateur, "
                    "il peut y avoir d'autres dimensions temporelles comme 'time_Group_1m'."
                )
            )
        unite_gui_val = col_unit.selectbox(
            "Unité de la période de calcul",
            ["d", "m", "y"],
            format_func=lambda x: {"d": "Jours", "m": "Mois", "y": "Années"}[x],
            key="ind_unite",
            help=(
                "Unité de temps utilisée pour rééchantillonner vos données avant de calculer l'indicateur. "
                "Ex: 1 mois = calculer l'indicateur chaque mois. 1 an = chaque année. "
                "3 mois = chaque trimestre."
            )
        )
        nb_gui_val = col_nb.number_input(
            "Pas de temps (nombre d'unités)",
            min_value=1, value=1, step=1,
            key="ind_nb",
            help=(
                "Nombre d'unités à regrouper par calcul. "
                "Ex : unité=Mois, pas=3 → l'indicateur est calculé tous les 3 mois (par trimestre). "
                "Unité=Jours, pas=10 → toutes les 10 journées."
            )
        )

    if indicator == "Soil_Water_Balance_Index":
        col_p, col_etr, col_dr = st.columns(3)
        var_p   = col_p.selectbox("Variable P (précipitations)", vars_list_ind, key="ips_p")
        var_etr = col_etr.selectbox("Variable ETR", vars_list_ind, key="ips_etr")
        var_dr  = col_dr.selectbox("Variable ΔR (variation stock)", vars_list_ind, key="ips_dr")
    
    elif indicator == "Standardised Piezometric Level Indicator":
        var_q = st.selectbox("Variable Niveau Piézométrique", vars_list_ind, key="ind_varspli")

    elif indicator in ("Qmean", "Q90/95", "Q10/05", "VCN10", "VCX3"):
        var_q = st.selectbox(
            "Variable à analyser",
            vars_list_ind,
            key="ind_varq",
            help=(
                "Sélectionnez la variable sur laquelle calculer l'indicateur. "
                "Peut être un débit (m³/s), une précipitation (mm/j), un niveau piézométrique (m), etc. "
                "L'indicateur sera calculé sur les valeurs de cette variable."
            )
        )

    elif indicator == "over_threshold":
        var_q = st.selectbox(
            "Variable à analyser",
            vars_list_ind,
            key="ind_varq_ot",
            help=(
                "Sélectionnez la variable dont vous souhaitez détecter les dépassements de seuil. "
                "Ex: un débit journalier, une température, une précipitation, etc."
            )
        )
        c1, c2 = st.columns(2)
        threshold = c1.number_input(
            "Threshold (Seuil)",
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

    # ── Bouton calcul indicateur ─────────────────────────────────────────────
    if st.button("▶️ Calculer l'indicateur", key="run_ind"):
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
            elif indicator == "Qmean":
                ds_work = ind.Qmean(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "Q90/95":
                ds_work = ind.Q90_95(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "Q10/05":
                ds_work = ind.Q10_05(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "VCN10":
                ds_work = ind.VCN10(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "VCX3":
                ds_work = ind.VCX3(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "Standardised Piezometric Level Indicator":
                st.warning("SPLI n'est pas encore implémenté dans le moteur de calcul.")
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
            log(f"Indicateur '{indicator}' calculé → {new_vars}", "success")
            
            # --- Affichage des résultats détaillés (Summary) ---
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

                # Temps et Variables
                if summary.get("new_time_dim"):
                    st.markdown(f"**New Temporal Coordinate added:** `{summary['new_time_dim']}`")

                new_vars = summary.get("new_vars", [summary.get("var_name")] if summary.get("var_name") else [])
                if new_vars and new_vars != [None]:
                    st.markdown(f"**New Variable(s) added:** {', '.join([f'`{v}`' for v in new_vars])}")

                # Dimensions et Shape
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
                    with st.expander("👁️ Aperçu des 5 premières valeurs (avec dimensions)"):
                        st.markdown("**Tableau d'aperçu :**")
                        # preview_data is a dict (orient='list') from a pandas DataFrame
                        df_preview = pd.DataFrame(summary["preview_data"])
                        
                        # Rename columns for better readability
                        rename_map = {
                            "time": "Date",
                            "model": "Modèle",
                            "scenario": "Scénario",
                            0: "Valeur"
                        }
                        df_preview = df_preview.rename(columns=rename_map)
                        
                        # If a column name is not in rename_map, it stays as is
                        st.table(df_preview)

                elif summary.get("first_5_vals"):
                    with st.expander("👁️ Aperçu (Ancien format)"):
                        st.markdown("**Aperçu des 5 premières valeurs :**")
                        preview_dict = {"Valeur": summary["first_5_vals"]}
                        if summary.get("first_5_dates"):
                            preview_dict["Date"] = summary["first_5_dates"]
                        
                        # Set column order nicely if dates are present
                        if "Date" in preview_dict:
                            preview_dict = {"Date": preview_dict["Date"], "Valeur": preview_dict["Valeur"]}
                            
                        st.table(pd.DataFrame(preview_dict))

                st.markdown("---")

            st.success(f"✅ Indicateur calculé. Nouvelles variables : {new_vars}")

            if new_vars:
                with st.expander("🔍 Détails techniques des nouvelles variables"):
                    for nv in new_vars:
                        da_new = ds_work[nv]
                        st.markdown(f"**{nv}** — dims: `{da_new.dims}`, shape: `{da_new.shape}`")
                        try:
                            vals_flat = da_new.values.flatten().astype(float)
                            vals_flat = vals_flat[~np.isnan(vals_flat)]
                            if vals_flat.size:
                                c1, c2, c3 = st.columns(3)
                                c1.metric("Min", f"{vals_flat.min():.3f}")
                                c2.metric("Moy", f"{vals_flat.mean():.3f}")
                                c3.metric("Max", f"{vals_flat.max():.3f}")
                        except Exception:
                            pass

        except Exception as e:
            log(f"Erreur indicateur : {e}", "error")
            st.error(f"Erreur : {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 : VISUALISATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_viz:
    st.markdown('<div class="section-title">Visualisation</div>', unsafe_allow_html=True)

    chart_type = st.selectbox(
        "Type de graphique",
        ["Graphique en ligne", "Graphique en barres", "Nuage de points", "Radar", "Histogramme"],
        key="viz_type",
    )

    vars_viz = ds_vars_and_coords()

    # ── Configuration commune ───────────────────────────────────────────────
    col_v1, col_v2 = st.columns(2)
    
    # Selection of variables based on chart type
    if chart_type == "Radar":
        vars_multi = col_v2.multiselect("Variables (valeurs)", ds_vars(), key="viz_radar")
        var_x = col_v1.selectbox("Variable catégorielle (rayons du radar)", vars_viz, key="viz_radar_x")
        plot_vars_ui = vars_multi
    else:
        # Pour tous les autres types, on peut choisir X et Y
        var_x = col_v1.selectbox("Axe X (abscisse)", vars_viz, key="viz_x")
        
        if chart_type == "Nuage de points":
            var_y = col_v2.selectbox("Axe Y (ordonnée)", vars_viz, key="viz_y")
            plot_vars_ui = [var_x, var_y]
        elif chart_type == "Histogramme":
            var_main = col_v2.selectbox("Variable à analyser", ds_vars(), key="viz_main")
            plot_vars_ui = [var_main]
        else: # Ligne ou Barres
            var_main = col_v2.selectbox("Variable principale (Y)", ds_vars(), key="viz_main")
            vars_extra = st.multiselect("Variables supplémentaires (optionnel)", ds_vars(), key="viz_extra")
            plot_vars_ui = [var_main] + (vars_extra or [])

    # Filtres catégoriels (Spécifiques par variable)
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
                "🔎 Filtres catégoriels (scénarios, modèles…) - Spécifiques par variable",
            ):
                st.info(
                    "💡 **Filtres catégoriels** : Sélectionnez des valeurs spécifiques pour une ou plusieurs catégories. "
                    "Ex: en sélectionnant `model = model1` vous ne tracez que ce modèle. "
                    "Laisser vide = la **moyenne** de toutes les valeurs de cette dimension sera calculée automatiquement. "
                    "Sélectionner plusieurs valeurs = une courbe par valeur."
                )
                
                for i, var_n in enumerate(plot_vars_ui):
                    if var_n not in ds_viz: continue
                    da_viz = ds_viz[var_n]
                    cat_dims = [d for d in list(da_viz.dims) if d not in standard_dims and not str(d).startswith('time_') and ds_viz.dims.get(d, 0) > 1]
                    
                    if not cat_dims: continue
                    
                    st.markdown(f"**Pour `{var_n}` :**")
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

        # Options spécifiques selon le type
        st.markdown("---")

        if chart_type in ["Graphique en ligne", "Nuage de points"]:
            show_envelope = st.checkbox(
                "Afficher l'enveloppe d'incertitude (plage min–max entre modèles/scénarios)",
                value=False,
                help=(
                    "Si votre dataset contient plusieurs modèles ou scénarios, l'enveloppe représente "
                    "la plage de valeurs possibles entre le minimum et le maximum de tous les modèles disponibles. "
                    "La zone ombrée montre la dispersion ; la ligne centrale = la moyenne ou le(s) modèle(s) sélectionné(s)."
                )
            )
            env_type = "average"
            if show_envelope:
                st.info(
                    "**Enveloppe** : La zone ombrée représente l'intervalle "
                    "[min, max] calculé sur tous les modèles ou scénarios pour chaque pas de temps. "
                    "Cela permet de visualiser la dispersion liée aux projections climatiques. "
                    "Mode 'average': La zone ombrée montre la dispersion ; la ligne centrale = la moyenne ou le(s) modèle(s) sélectionné(s) "
                    "Mode 'individual': Toutes les courbes des modèles non selectionnés sont tracées à l'intérieur de l'enveloppe en couleur transparente"
                )
                env_type = st.radio(
                    "Courbe centrale de l'enveloppe",
                    ["average", "individual"],
                    index=0,
                    horizontal=True,
                    help="'average' trace la moyenne de tous les modèles. 'individual' trace une courbe par modèle à l'intérieur de l'enveloppe."
                )
            st.session_state["viz_envelope"] = show_envelope
            st.session_state["viz_env_type"] = env_type
            
        elif chart_type == "Histogramme":
            nb_bins = st.number_input(
                "Nombre de classes (bins)",
                min_value=1, max_value=200, value=10,
                help=(
                    "Détermine la résolution de l'histogramme. "
                    "Peu de classes = vue globale de la distribution. "
                    "Beaucoup de classes = détail fin mais plus bruité. "
                    "Règle pratique : √(nombre de valeurs) est un bon point de départ."
                )
            )
            st.session_state["viz_bins"] = nb_bins

    # Période temporelle
    t_dims_viz = time_like_dims()
    start_viz = None
    end_viz   = None
    if t_dims_viz:
        with st.expander(
            "⏳ Filtrage temporel",
        ):
            st.info(
                "💡 **Filtrage temporel** : Sélectionnez la période à afficher sur le graphique. "
                "La période choisie apparaîtra dans le titre du graphique. "
                "Laisser les dates par défaut (min/max) = afficher toute la chronique disponible."
            )
            t_v = pd.to_datetime(st.session_state["ds"][t_dims_viz[0]].values)
            c1, c2 = st.columns(2)
            d_s = c1.date_input("Début", value=t_v.min().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_ds")
            d_e = c2.date_input("Fin",   value=t_v.max().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_de")
            start_viz = str(d_s)
            end_viz   = str(d_e)

    # ── Options de style et zoom ──────────────────────────────────────────────
    with st.expander("🎨 Options de style & 🔍 Zoom / Curseurs d'axes"):
        col_t, col_xl, col_yl = st.columns(3)
        p_title  = col_t.text_input("Titre du graphique", "", help="Titre principal affiché en haut du graphique.")
        p_xlabel = col_xl.text_input("Label axe X", "", help="Nom de l'axe horizontal (ex: 'Temps', 'Précipitations (mm/j)').")
        p_ylabel = col_yl.text_input("Label axe Y", "", help="Nom de l'axe vertical (ex: 'Débit (m³/s)', 'Température (°C)').")
        
        st.markdown("---")
        st.markdown(
            "**🔍 Zoom manuel — Curseurs d'axes**",
            help=(
                "Définissez les limites d'affichage des axes. "
                "Laissez les curseurs à leurs valeurs min/max pour afficher toutes les données. "
                "Utile pour zoomer sur une plage de valeurs spécifique."
            )
        )
        st.caption("💡 Déplacez les curseurs pour zoomer sur une plage de valeurs. Les données hors plage ne seront pas affichées.")

        # Compute data range dynamically for sliders
        _ds_cur = st.session_state.get("ds")
        _y_min_g, _y_max_g = 0.0, 1.0
        _x_min_g, _x_max_g = 0.0, 1.0

        if _ds_cur is not None and plot_vars_ui:
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
                if var_x in _ds_cur and np.issubdtype(_ds_cur[var_x].dtype, np.number):
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
        _x_step = float(f"{_x_range / 100:.4g}")

        col_sly, col_slx = st.columns(2)

        with col_sly:
            use_y_zoom = st.checkbox("Activer le zoom sur l'axe Y", value=False, key="use_y_zoom")
            if use_y_zoom:
                y_slider = st.slider(
                    "Plage de l'axe Y",
                    min_value=float(_y_min_g),
                    max_value=float(_y_max_g),
                    value=(float(_y_min_g), float(_y_max_g)),
                    step=_y_step,
                    key="y_slider",
                    help=f"Valeurs de la variable Y : de {_y_min_g:.4g} à {_y_max_g:.4g}."
                )
                z_ymin, z_ymax = y_slider
            else:
                z_ymin, z_ymax = None, None

        with col_slx:
            use_x_zoom = st.checkbox("Activer le zoom sur l'axe X (si numérique)", value=False, key="use_x_zoom")
            if use_x_zoom:
                x_slider = st.slider(
                    "Plage de l'axe X",
                    min_value=float(_x_min_g),
                    max_value=float(_x_max_g),
                    value=(float(_x_min_g), float(_x_max_g)),
                    step=_x_step,
                    key="x_slider",
                    help=f"Valeurs de la variable X : de {_x_min_g:.4g} à {_x_max_g:.4g}. Ne fonctionne que si l'axe X est numérique (pas un axe temporel)."
                )
                z_xmin, z_xmax = x_slider
            else:
                z_xmin, z_xmax = None, None

        st.markdown("---")
        st.markdown(
            "📐 **Lignes de seuil (référence sur le graphique)**",
        )
        st.caption(
            "💡 Tracez des lignes horizontales (Y) ou verticales (X) sur le graphique pour indiquer un seuil ou une référence. "
            "Ex: tracer Y=0 pour la ligne zéro, ou X=1980 pour marquer une année clé. Laisser vide = pas de ligne."
        )
        col_thr_y, col_thr_x = st.columns(2)
        th_y_vals_raw = col_thr_y.text_input(
            "Seuil(s) horizontal(aux) Y (valeur de la variable)",
            value="",
            key="thresh_y",
            help=(
                "Entrez une ou plusieurs valeurs numériques séparées par des virgules pour tracer des lignes horizontales. "
                "Ex: '0' trace la ligne zéro. '100, 200' trace deux lignes Y=100 et Y=200. "
                "Utile pour visualiser un seuil de crue, un seuil de sécheresse, une valeur de référence…"
            )
        )
        th_x_vals_raw = col_thr_x.text_input(
            "Seuil(s) vertical(aux) X (valeur de l'axe X)",
            value="",
            key="thresh_x",
            help=(
                "Entrez une ou plusieurs valeurs séparées par des virgules pour tracer des lignes verticales. "
                "Fonctionne si l'axe X est numérique. Pour un axe temporel, entrez une année (ex: '1980'). "
                "Ex: '1980' trace une ligne verticale à l'année 1980."
            )
        )
        col_thr_col, col_thr_sty = st.columns(2)
        thresh_color = col_thr_col.color_picker(
            "Couleur des lignes de seuil", "#FF4B4B", key="thresh_color",
            help="Couleur appliquée à toutes les lignes de seuil."
        )
        thresh_style = col_thr_sty.selectbox(
            "Style de ligne",
            ["--", "-", "-.", ":"],
            key="thresh_style",
            help="Style du trait : -- = tirets, - = plein, -. = tiret-point, : = pointé."
        )

        st.markdown("---")
        col_save, col_fmt = st.columns(2)
        save_fig = col_save.checkbox("Sauvegarder la figure", value=False)
        save_fmt = col_fmt.selectbox("Format", ["png", "pdf", "svg"], key="save_fmt")
        save_path = ""
        if save_fig:
            save_path = st.text_input("Chemin de sauvegarde (ex: output/fig.png)", "output/figure.png", key="save_path")

    x_lim_val = [z_xmin, z_xmax] if (z_xmin is not None or z_xmax is not None) else None
    y_lim_val = [z_ymin, z_ymax] if (z_ymin is not None or z_ymax is not None) else None

    # Parsing des seuils
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

    # ── Bouton tracer ────────────────────────────────────────────────────────
    if st.button("📈 Tracer", key="run_viz"):
        ds_work = st.session_state["ds"]

        # Sous-ensemble temporel si demandé
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

            if chart_type == "Graphique en ligne":
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

            elif chart_type == "Graphique en barres":
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

            elif chart_type == "Nuage de points":
                fig = viz.scatter_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=[var_y],
                    start_gui=start_viz,
                    end_gui=end_viz,
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters,
                    plot_envelope_gui=st.session_state.get("viz_envelope", False),
                    envelope_type_gui=st.session_state.get("viz_env_type", "average")
                )

            elif chart_type == "Radar":
                if not vars_multi:
                    st.warning("Sélectionnez au moins deux variables pour le radar.")
                else:
                    fig = viz.radar_chart(
                        ds_plot, 
                        var_gui=vars_multi,
                        cat_name_gui=var_x,
                        start_gui=start_viz,
                        end_gui=end_viz,
                        plot_config_gui=gui_config,
                        dim_selections_gui=viz_filters,
                        auto_mean_gui=True
                    )

            elif chart_type == "Histogramme":
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
                # ── Lignes de seuil (threshold lines) ─────────────────────
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
                                         label=f"Seuil Y={yv:.4g}", zorder=10)
                        for xv in _th_x_vals:
                            ax_t.axvline(x=xv, color=_tc, linestyle=_ts, linewidth=1.4,
                                         label=f"Seuil X={xv:.4g}", zorder=10)
                        # Refresh legend if new lines were added
                        handles, labels_leg = ax_t.get_legend_handles_labels()
                        if handles:
                            ax_t.legend(handles, labels_leg, loc="upper center",
                                        bbox_to_anchor=(0.5, -0.15), ncol=min(4, len(handles)))
                    fig.tight_layout()

                st.pyplot(fig, use_container_width=True)


                # ── Téléchargement ────────────────────────────────────────
                buf = io.BytesIO()
                fmt = save_fmt if save_fig else "png"
                fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
                buf.seek(0)
                fname = os.path.splitext(os.path.basename(save_path))[0] if (save_fig and save_path) else "figure"
                st.download_button(
                    label=f"⬇️ Télécharger ({fmt.upper()})",
                    data=buf,
                    file_name=f"{fname}.{fmt}",
                    mime=f"image/{fmt}",
                )
                log(f"Graphique '{chart_type}' généré.", "success")

        except Exception as e:
            log(f"Erreur de visualisation : {e}", "error")
            st.error(f"Erreur : {e}")
            import traceback
            st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT CSV DES VARIABLES CRÉÉES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">⬇️ Exporter les variables en CSV</div>', unsafe_allow_html=True)

with st.expander("📊 Télécharger les variables calculées", expanded=False):
    st.info(
        "💡 **Comment utiliser cet export** : Sélectionnez une ou plusieurs variables ci-dessous "
        "(y compris les indicateurs et statistiques que vous venez de calculer) et téléchargez-les en CSV. "
        "Le fichier contiendra toutes les dimensions comme colonnes (date, modèle, scénario…) "
        "suivi des valeurs de chaque variable sélectionnée."
    )
    
    all_vars_export = list(st.session_state["ds"].data_vars)
    export_vars = st.multiselect(
        "Variables à exporter",
        all_vars_export,
        default=[],
        key="export_vars",
        help=(
            "Sélectionnez les variables à inclure dans le fichier CSV. "
            "Vous pouvez exporter toutes vos variables originales ainsi que celles calculées "
            "(indicateurs, statistiques…). Exemple : sélectionner 'Qmean_1m_debit' exportera "
            "la moyenne mensuelle du débit avec les colonnes date et valeur."
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

                st.markdown(f"**Aperçu du CSV ({len(df_final):,} lignes, {len(df_final.columns)} colonnes) :**")
                st.dataframe(df_final.head(10), use_container_width=True)

                csv_buffer = io.StringIO()
                df_final.to_csv(csv_buffer, index=False, float_format="%.6g")
                csv_bytes = csv_buffer.getvalue().encode("utf-8")

                export_filename = "_".join(export_vars[:3]) + "_export.csv"
                st.download_button(
                    label=f"⬇️ Télécharger le CSV ({len(df_final):,} lignes)",
                    data=csv_bytes,
                    file_name=export_filename,
                    mime="text/csv",
                    key="csv_download_btn",
                )
                st.caption(f"📁 Fichier : `{export_filename}` — Colonnes : {', '.join(df_final.columns.tolist())}")
            else:
                st.warning("Impossible de convertir les variables sélectionnées en tableau.")

        except Exception as e:
            st.error(f"Erreur lors de l'export : {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.caption("Sélectionnez au moins une variable pour activer le téléchargement.")


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption("RE_EAU 2025 — Interface Streamlit | Données climatiques & hydrologiques xArray")
