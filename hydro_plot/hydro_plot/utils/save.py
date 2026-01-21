import os
import matplotlib.pyplot as plt

def save_figure(fig, filename, dpi=300, overwrite=True):
    """
    Sauvegarde une figure matplotlib dans un fichier.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        La figure à sauvegarder.
    filename : str
        Chemin complet du fichier (ex : "results/figures/figure.png").
    dpi : int, optional
        Résolution de la figure (par défaut 300).
    overwrite : bool, optional
        Si True, écrase le fichier existant.
    """

    # Crée le dossier si nécessaire
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)

    # Vérifie si le fichier existe
    if not overwrite and os.path.exists(filename):
        raise FileExistsError(f"Le fichier {filename} existe déjà.")

    # Sauvegarde
    fig.savefig(filename, dpi=dpi, bbox_inches='tight')
    print(f"Figure sauvegardée dans {filename}")
