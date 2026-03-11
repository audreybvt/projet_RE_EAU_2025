
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
ds.data_vars  # variables disponibles
ds.dims       # dimensions
ds.coords     # coordonnées
ds.attrs      # attributs globaux

print(ds["niveau"])
print(ds["niveau"].values)
data = ds["niveau"].values.ravel()
data = data[np.isfinite(data)]
print(data)

'''
print(ds["time"])



da = ds["niveau"]
da.dims
da.shape
da.attrs

for dataset in [ds, ds2]:
    gcm = dataset.attrs.get("driving_model_id", "unknown")
    rcm = dataset.attrs.get("model_id", "unknown")
    bc = dataset.attrs.get("bc_method_id", "unknown")
    hy_model = dataset.attrs.get("hy_model_id", "unknown")
    scenario = dataset.attrs.get("experiment_id", "unknown")

    # Créer une seule dimension "model_chain"
    model_chain = f"{gcm}-{rcm}-{bc}-{hy_model}"

    # Étendre le dataset avec les deux nouvelles dimensions
    dataset = dataset.expand_dims({
        "scenario": [scenario],
        "model_chain": [model_chain]
    })

print(ds)
combined = xr.combine_by_coords([ds,ds2], combine_attrs="drop")

'''
