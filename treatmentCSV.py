import xarray as xr

ds = xr.open_dataset("C:/Users/User/OneDrive - CentraleSupelec/Documents/Etudes/CS/3A/Mention/Projet/Travail/projet_RE_EAU_2025/niveau_PiezoFrance_CNRM-CERFACS-CNRM-CM5_rcp26_r1i1p1_CNRM-ALADIN63_v2_ADAMONT-France_BRGM-AquiFR_day_20050801-21000731.nc")

print(ds.data_vars["long_name"], ":")  # variables disponibles
print("Dimensions :",ds.dims, ":")       # dimensions
print(ds.coords, ":")     # coordonnées
#print("attributs globaux :",ds.attrs, ":")      # attributs globaux

#print(ds.time.dtype, ds.time.values[:3])
#print(ds.time.encoding)  # pour voir units/calendar originaux

piezo = ds["niveau"]
time = ds["time"]

print(piezo.attrs, ";")
print(piezo.attrs.get("long_name"), ", unit :", piezo.attrs.get("units"))
print(time.attrs)

print(piezo.dims, ";")
print(piezo.shape, ";")
print(type(piezo))

#print(ds["code"].values)
#print(piezo.piezometre.values)