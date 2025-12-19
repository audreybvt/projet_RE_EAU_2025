# ==========================
# Script complet NetCDF piézo
# ==========================

from netCDF4 import Dataset, num2date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# --------------------------
# 1️⃣ Ouvrir le fichier NetCDF
# --------------------------
nc_file = "niveau_PiezoFrance_CNRM-CERFACS-CNRM-CM5_rcp26_r1i1p1_CNRM-ALADIN63_v2_ADAMONT-France_BRGM-AquiFR_day_20050801-21000731.nc"
nc = Dataset(nc_file, "r")

# Variables
niveau = nc.variables["niveau"]      # niveaux piézométriques
time = nc.variables["time"]          # temps
lat = nc.variables["Lat"][:]         # latitude stations
lon = nc.variables["Lon"][:]         # longitude stations

# --------------------------
# 2️⃣ Convertir le temps en datetime
# --------------------------
dates = num2date(time[:], units=time.units, calendar=getattr(time, "calendar", "standard"))
dates_dt = [datetime.datetime(d.year, d.month, d.day) for d in dates]

# --------------------------
# 3️⃣ Tracer une station (ex. station 0)
# --------------------------
serie_station0 = niveau[:, 0]  # temps × station 0

plt.figure(figsize=(12,5))
plt.plot(dates_dt, serie_station0)
plt.xlabel("Date")
plt.ylabel("Niveau piézométrique (m)")
plt.title("Station 0 – Projection RCP2.6")
plt.grid()
plt.show()

# --------------------------
# 4️⃣ Moyenne sur toutes les stations
# --------------------------
moyenne_stations = np.mean(niveau[:], axis=1)

plt.figure(figsize=(12,5))
plt.plot(dates_dt, moyenne_stations)
plt.xlabel("Date")
plt.ylabel("Niveau piézométrique moyen (m)")
plt.title("Moyenne piézométrique – RCP2.6")
plt.grid()
plt.show()

# --------------------------
# 5️⃣ Exemple : carte des stations à un instant donné
# --------------------------
instant = 0  # premier pas de temps
plt.figure(figsize=(8,6))
sc = plt.scatter(lon, lat, c=niveau[instant,:], cmap="viridis")
plt.colorbar(sc, label="Niveau piézométrique (m)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title(f"Niveau piézométrique – {dates_dt[instant].date()}")
plt.show()

# --------------------------
# 6️⃣ Fermer le fichier
# --------------------------
nc.close()
