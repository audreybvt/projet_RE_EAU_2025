class HydroDataset:
    """
    Représente un jeu de données hydrologiques
    issu d'un modèle prédictif.
    """

    def __init__(self, data, indicator, site, unit=None):
        self.data = data
        self.indicator = indicator
        self.site = site
        self.unit = unit
