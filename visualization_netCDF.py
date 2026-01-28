import xarray as xr
import matplotlib.pyplot as plt

def plot_temp (path, name_var, title = "Put a title"):
    
    # Ouvrir le fichier NetCDF
    ds = xr.open_dataset(path)

    # Sélection de la variable
    var = ds[name_var]

    # Tracé de la série temporelle
    plt.figure(figsize=(10, 4))
    var.plot()

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel(name_var)

    plt.tight_layout()
    return plt.show()

