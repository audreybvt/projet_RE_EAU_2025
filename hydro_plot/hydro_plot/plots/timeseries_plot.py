import matplotlib.pyplot as plt
from .base_plot import BasePlot
from ..styles.colors import RCP_COLORS  # tes couleurs définies


class TimeSeriesPlot(BasePlot):
    """
    Figure de type série temporelle.
    """

    def plot(self):
        # Vérifier que les données existent
        if not hasattr(self.dataset, 'data'):
            raise ValueError("Pas de données dans le dataset")

        plt.figure(figsize=(10, 5))
        plt.plot(
            self.dataset.data,
            label=f"{self.dataset.indicator} - {self.dataset.site}",
            color='blue'  # plus tard on utilisera RCP_COLORS
        )
        plt.title(self.title or f"Série temporelle {self.dataset.indicator}")
        plt.xlabel("Temps")
        plt.ylabel(self.dataset.unit or "")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()  # affiche la figure à l'écran
        

