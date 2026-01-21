from hydro_plot.datasets.hydro_dataset import HydroDataset
from hydro_plot.plots.timeseries_plot import TimeSeriesPlot

# Données factices : 10 points
data = [1, 2, 3, 2, 4, 5, 3, 4, 6, 5]

dataset = HydroDataset(
    data=data,
    indicator="Débit",
    site="Loire",
    unit="m³/s"
)

fig = TimeSeriesPlot(dataset, title="Test série temporelle")
fig.plot()
fig.save("results/figures/test.png")
