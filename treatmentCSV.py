import xarray as xr

ds = xr.open_dataset("C:/Users/User/OneDrive - CentraleSupelec/Documents/Etudes/CS/3A/Mention/Projet/Travail/projet_RE_EAU_2025/niveau_PiezoFrance_CNRM-CERFACS-CNRM-CM5_rcp26_r1i1p1_CNRM-ALADIN63_v2_ADAMONT-France_BRGM-AquiFR_day_20050801-21000731.nc")

print(ds.data_vars, ":")  # variables disponibles
print(ds.dims, ":")       # dimensions
print(ds.coords, ":")     # coordonnées
print(ds.attrs, ":")      # attributs globaux

piezo = ds["niveau"]
print(piezo.dims, ";")
print(piezo.shape, ";")
print(piezo.attrs, ";")