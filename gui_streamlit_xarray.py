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
    cat_dims = [d for d in list(ds.dims.keys()) if d not in standard_dims and ds.dims[d] > 1]
    
    dict_filters = {}
    if cat_dims:
        with st.expander("🔎 Filtres catégoriels (scénarios, modèles…)"):
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
    file_format = st.radio("Format du fichier", ["NetCDF (.nc)", "CSV (.csv)"], horizontal=True)

    # ── Uploader ─────────────────────────────────────────────────────────────
    if file_format.startswith("NetCDF"):
        uploaded_files = st.file_uploader(
            "Glissez-déposez un ou plusieurs fichiers NetCDF",
            type=["nc"],
            accept_multiple_files=True,
            key="nc_uploader",
        )
    else:
        uploaded_files = st.file_uploader(
            "Glissez-déposez un fichier CSV",
            type=["csv"],
            accept_multiple_files=False,
            key="csv_uploader",
        )
        skip_n = st.number_input("Lignes de métadonnées à ignorer", min_value=0, value=0, step=1)

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

                    else:
                        # CSV
                        f = uploaded_files
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                        tmp.write(f.read())
                        tmp.flush()
                        ds_loaded = df_mod.csv_to_xarray(tmp.name, skip_n_gui=int(skip_n))
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
            st.markdown("**Dimensions**")
            dim_df = pd.DataFrame({"Dimension": list(ds.dims.keys()), "Taille": list(ds.dims.values())})
            st.dataframe(dim_df, hide_index=True, use_container_width=True)
        with col_b:
            st.markdown("**Variables**")
            rows = []
            for v in ds.data_vars:
                da = ds[v]
                rows.append({"Variable": v, "Dims": str(da.dims), "Type": str(da.dtype)})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

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
        ],
    )

    vars_list = ds_vars()
    all_dims  = ds_dims()

    col1, col2 = st.columns(2)

    with col1:
        var_name = st.selectbox("Variable source", vars_list, key="stat_var")

    if var_name:
        avail_dims = list(st.session_state["ds"][var_name].dims)
    else:
        avail_dims = all_dims

    with col2:
        if stat_func not in ("Moyenne interannuelle mensuelle", "Moyenne glissante (rolling)"):
            dims_sel = st.multiselect(
                "Dimensions à réduire (laisser vide = toutes)",
                avail_dims,
                default=avail_dims,
                key="stat_dims",
            )
        elif stat_func == "Moyenne interannuelle mensuelle":
            t_dims_list = [d for d in avail_dims if "time" in d.lower()]
            time_dim_sel = st.selectbox("Dimension temporelle", t_dims_list if t_dims_list else avail_dims, key="stat_time_dim")
        elif stat_func == "Moyenne glissante (rolling)":
            window_val = st.number_input("Taille de la fenêtre (pas de temps)", min_value=1, value=7, step=1)

    # Période temporelle
    if stat_func not in ("Moyenne interannuelle mensuelle",):
        t_dims = time_like_dims()
        if t_dims:
            with st.expander("⏳ Filtrage temporel (optionnel)"):
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
            dims_to_reduce = dims_sel if stat_func not in ("Moyenne interannuelle mensuelle", "Moyenne glissante (rolling)") else None

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

            st.session_state["ds"] = ds_work
            new_vars = [v for v in ds_work.data_vars if v not in vars_list]
            log(f"Statistique '{stat_func}' calculée → {new_vars}", "success")
            st.success(f"✅ Calcul terminé. Nouvelles variables : {new_vars}")

            # Aperçu de la nouvelle variable
            if new_vars:
                with st.expander("👁️ Aperçu de la variable calculée"):
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
                            c4.metric("N valides", f"{vals_flat.size:,}")

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
        ["IPS", "Qmean", "Q90/Q95", "Q10/Q05", "VCN10", "VCX3", "Over threshold"],
        key="ind_select",
    )

    vars_list_ind = ds_vars()

    # ── Filtres catégoriels ──────────────────────────────────────────────────
    dict_filters_gui = render_categorical_filters(key_prefix="ind")

    # ── Paramètres spécifiques à chaque indicateur ─────────────────────────
    st.markdown("**Paramètres de l'indicateur**")

    # Période temporelle
    t_dims_ind = time_like_dims()
    time_coord_ind = t_dims_ind[0] if t_dims_ind else None
    unite_gui_val = None
    nb_gui_val    = None

    if indicator in ("Qmean", "Q90/Q95", "Q10/Q05", "VCN10", "VCX3", "Over threshold"):
        col_tc, col_unit, col_nb = st.columns(3)
        if t_dims_ind:
            time_coord_ind = col_tc.selectbox("Coordonnée temporelle", t_dims_ind, key="ind_tc")
        unite_gui_val = col_unit.selectbox("Unité de temps", ["d", "m", "y"],
                                            format_func=lambda x: {"d": "Jours", "m": "Mois", "y": "Années"}[x], key="ind_unite")
        nb_gui_val = col_nb.number_input("Pas de temps", min_value=1, value=1, step=1, key="ind_nb")

    if indicator == "IPS":
        col_p, col_etr, col_dr = st.columns(3)
        var_p   = col_p.selectbox("Variable P (précipitations)", vars_list_ind, key="ips_p")
        var_etr = col_etr.selectbox("Variable ETR", vars_list_ind, key="ips_etr")
        var_dr  = col_dr.selectbox("Variable ΔR (variation stock)", vars_list_ind, key="ips_dr")

    elif indicator in ("Qmean", "Q90/Q95", "Q10/Q05", "VCN10", "VCX3"):
        var_q = st.selectbox("Variable débit (Q)", vars_list_ind, key="ind_varq")

    elif indicator == "Over threshold":
        var_q    = st.selectbox("Variable débit (Q)", vars_list_ind, key="ind_varq_ot")
        c1, c2 = st.columns(2)
        threshold = c1.number_input("Seuil", value=0.0, format="%.4f", key="ind_thresh")
        tolerance = c2.number_input("Tolérance (%)", value=0.0, format="%.1f", key="ind_tol")

    # ── Bouton calcul indicateur ─────────────────────────────────────────────
    if st.button("▶️ Calculer l'indicateur", key="run_ind"):
        ds_work = st.session_state["ds"]
        prev_vars = set(ds_work.data_vars)
        try:
            if indicator == "IPS":
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
            elif indicator == "Q90/Q95":
                ds_work = ind.Q90_95(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )
            elif indicator == "Q10/Q05":
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
            elif indicator == "Over threshold":
                ds_work = ind.over_threshold(
                    ds_work,
                    dict_filters_gui=dict_filters_gui,
                    time_coord_gui=time_coord_ind,
                    var_q_gui=var_q,
                    threshold_gui=float(threshold),
                    tolerance_gui=float(tolerance),
                    unite_gui=unite_gui_val,
                    nb_gui=int(nb_gui_val),
                )

            st.session_state["ds"] = ds_work
            new_vars = [v for v in ds_work.data_vars if v not in prev_vars]
            log(f"Indicateur '{indicator}' calculé → {new_vars}", "success")
            st.success(f"✅ Indicateur calculé. Nouvelles variables : {new_vars}")

            if new_vars:
                with st.expander("👁️ Aperçu"):
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
    
    if chart_type == "Radar":
        vars_multi = st.multiselect("Variables (axes du radar)", vars_viz, key="viz_radar")
        var_x = None # Non utilisé pour le radar
    else:
        # Pour tous les autres types, on peut choisir X et Y
        var_x = col_v1.selectbox("Axe X (abscisse)", vars_viz, key="viz_x")
        
        if chart_type == "Nuage de points":
            var_y = col_v2.selectbox("Axe Y (ordonnée)", vars_viz, key="viz_y")
        elif chart_type == "Histogramme":
            var_main = col_v2.selectbox("Variable à analyser", ds_vars(), key="viz_main")
        else: # Ligne ou Barres
            var_main = col_v2.selectbox("Variable principale (Y)", ds_vars(), key="viz_main")
            vars_extra = st.multiselect("Variables supplémentaires (optionnel)", ds_vars(), key="viz_extra")

        # Options spécifiques selon le type
        st.markdown("---")
        
        # Filtres catégoriels (Multi-select)
        viz_filters = render_categorical_filters(key_prefix="viz")

        if chart_type == "Graphique en ligne":
            show_envelope = st.checkbox("Afficher les enveloppes (min-max)", value=False, help="Si une dimension 'model' est présente")
            env_type = "average"
            if show_envelope:
                env_type = st.radio("Type d'enveloppe", ["average", "individual"], index=0, horizontal=True)
            st.session_state["viz_envelope"] = show_envelope
            st.session_state["viz_env_type"] = env_type
            
        elif chart_type == "Histogramme":
            nb_bins = st.number_input("Nombre de classes (bins)", min_value=1, max_value=100, value=10)
            st.session_state["viz_bins"] = nb_bins

    # Période temporelle
    t_dims_viz = time_like_dims()
    start_viz = None
    end_viz   = None
    if t_dims_viz:
        with st.expander("⏳ Filtrage temporel"):
            t_v = pd.to_datetime(st.session_state["ds"][t_dims_viz[0]].values)
            c1, c2 = st.columns(2)
            d_s = c1.date_input("Début", value=t_v.min().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_ds")
            d_e = c2.date_input("Fin",   value=t_v.max().date(), min_value=t_v.min().date(), max_value=t_v.max().date(), key="viz_de")
            start_viz = str(d_s)
            end_viz   = str(d_e)

    # Options de style
    with st.expander("🎨 Options de style"):
        col_t, col_xl, col_yl = st.columns(3)
        p_title  = col_t.text_input("Titre", "")
        p_xlabel = col_xl.text_input("Axe X", "")
        p_ylabel = col_yl.text_input("Axe Y", "")
        col_save, col_fmt = st.columns(2)
        save_fig = col_save.checkbox("Sauvegarder la figure", value=False)
        save_fmt = col_fmt.selectbox("Format", ["png", "pdf", "svg"], key="save_fmt")
        save_path = ""
        if save_fig:
            save_path = st.text_input("Chemin de sauvegarde (ex: output/fig.png)", "output/figure.png", key="save_path")

    plot_config_gui = {
        "title":    p_title  or None,
        "xlabel":   p_xlabel or None,
        "ylabel":   p_ylabel or None,
        "save_path": save_path if save_fig else None,
    }

    # ── Bouton tracer ────────────────────────────────────────────────────────
    if st.button("📈 Tracer", key="run_viz"):
        ds_work = st.session_state["ds"]

        # Sous-ensemble temporel si demandé
        if t_dims_viz and start_viz and end_viz:
            try:
                ds_plot = df_mod.handle_spatial_dimensions.__module__ and ds_work  # just alias
                ds_plot = ds_work.sel({t_dims_viz[0]: slice(start_viz, end_viz)})
            except Exception:
                ds_plot = ds_work
        else:
            ds_plot = ds_work

        try:
            fig = None

            # Always pass auto_mean_gui=True and dim_selections_gui={} so that
            # handle_xarray_dimensions never prompts the terminal.
            # The plot_config_gui dict provides labels from the Streamlit sidebar.
            gui_config = {
                "xlabel": plot_config_gui.get("xlabel") or "",
                "ylabel": plot_config_gui.get("ylabel") or "",
                "title": plot_config_gui.get("title") or "",
            }

            if chart_type == "Graphique en ligne":
                plot_vars = [var_main] + (vars_extra or [])
                fig = viz.line_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=plot_vars,
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
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters
                )

            elif chart_type == "Nuage de points":
                fig = viz.scatter_chart(
                    ds_plot,
                    x_name_gui=var_x,
                    y_names_gui=[var_y],
                    plot_config_gui=gui_config,
                    auto_mean_gui=True,
                    dim_selections_gui=viz_filters
                )

            elif chart_type == "Radar":
                if not vars_multi:
                    st.warning("Sélectionnez au moins deux variables pour le radar.")
                else:
                    fig = viz.radar_chart(
                        ds_plot, 
                        var_gui=vars_multi, 
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
                    plot_config_gui=gui_config,
                    dim_selections_gui=viz_filters,
                    auto_mean_gui=True
                )

            if fig is not None:
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
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption("RE_EAU 2025 — Interface Streamlit | Données climatiques & hydrologiques xArray")
