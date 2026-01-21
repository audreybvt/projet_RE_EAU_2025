class BasePlot:
    """
    Classe de base pour toutes les figures.
    """

    def __init__(self, dataset, title=None):
        self.dataset = dataset
        self.title = title

    def plot(self):
        raise NotImplementedError

    def save(self, filename):
        print(f"Figure sauvegardée dans {filename}")
