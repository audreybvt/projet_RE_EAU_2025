
from netCDF4 import Dataset, num2date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import xarray as xr

# --------------------------
# 1️⃣ Ouvrir le fichier NetCDF
# --------------------------
nc_file = "C:/Users/User/OneDrive - CentraleSupelec/Documents/Etudes/CS/3A/Mention/Projet/Travail/projet_RE_EAU_2025/input/netCDF/niveau_PiezoFrance_CNRM-CERFACS-CNRM-CM5_rcp26_r1i1p1_CNRM-ALADIN63_v2_ADAMONT-France_BRGM-AquiFR_day_20050801-21000731.nc"
nc_file_2 = "C:/Users/User/OneDrive - CentraleSupelec/Documents/Etudes/CS/3A/Mention/Projet/Travail/projet_RE_EAU_2025/input/netCDF/niveau_PiezoFrance_CNRM-CERFACS-CNRM-CM5_rcp45_r1i1p1_CNRM-ALADIN63_v2_ADAMONT-France_BRGM-AquiFR_day_20050801-21000731.nc"
ds = xr.open_dataset(nc_file, decode_cf=False)
ds2 = xr.open_dataset(nc_file_2, decode_cf=False)

ds            # résumé complet
print(ds.data_vars)  # variables disponibles
ds.dims       # dimensions
ds.coords     # coordonnées
print(ds.attrs)      # attributs globaux

da = ds["niveau"]
da.dims
da.shape
da.attrs

for ds in [ds, ds2]:
    gcm = ds.attrs.get("driving_model_id", "unknown")
    rcm = ds.attrs.get("model_id", "unknown")
    bc = ds.attrs.get("bc_method_id", "unknown")
    hy_model = ds.attrs.get("hy_model_id", "unknown")
    scenario = ds.attrs.get("experiment_id", "unknown")

    ds = ds.expand_dims({
        "scenario": [scenario],
        "gcm": [gcm],
        "rcm": [rcm],
        "hy_model": [hy_model],
    })

combined = xr.combine_by_coords([ds,ds2], combine_attrs="drop_conflicts")


