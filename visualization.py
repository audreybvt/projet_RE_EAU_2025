import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os


# ---------------- Create test DataFrame ----------------
'''
np.random.seed(42)

columns = ["col1", "col2", "col3", "col4"]

# Create col1 explicitly
col1 = np.arange(1, 21)  # 1, 2, ..., 20

# Create DataFrame for the remaining columns (col2, col3, col4)
df_test = pd.DataFrame(
    np.random.rand(20, 3) * 20 + 10,  # values between 10 and 30
    columns=columns[1:]
)

# Insert col1 as the first column
df_test.insert(0, "col1", col1)

print("Test DataFrame:")
print(df_test.head())
'''

# ---------------- Bar Chart ----------------

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def bar_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne X ---
    try:
        x_idx = int(input("\nIndex de la colonne pour l'axe X (catégories) : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne X")
    
    if x_idx < 0 or x_idx >= len(df.columns):
        raise IndexError("Index de colonne X invalide")
    
    # --- Choix de la colonne Y ---
    try:
        y_idx = int(input("Index de la colonne pour l'axe Y (valeurs) : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne Y")
    
    if y_idx < 0 or y_idx >= len(df.columns):
        raise IndexError("Index de colonne Y invalide")
    
    if y_idx == x_idx:
        raise ValueError("La colonne Y ne peut pas être la même que la colonne X")
    
    x_col = df.columns[x_idx]
    y_col = df.columns[y_idx]

    # --- Création du graphique ---
    x = df[x_col]
    y = df[y_col]

    colors = cm.viridis(np.linspace(0, 1, len(x)))

    fig, ax = plt.subplots(figsize=(8,5))
    ax.bar(x, y, color=colors)

    ax.set_title(f"Bar Chart: {y_col} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # Affichage des valeurs au-dessus des barres
    for i, v in enumerate(y):
        ax.text(i, v + 0.05*np.max(y), f"{v:.2f}", ha='center', va='bottom')
    
    if len(y) < 30:
        for i, v in enumerate(y):
            ax.text(i, v + 0.01 * np.max(y), f"{v:.2f}", ha='center', va='bottom', fontsize=8)
    else:
        print(f"Trop de données ({len(y)} lignes) : les étiquettes de texte ont été désactivées pour la lisibilité.")

    return fig  # retourne la figure pour pouvoir faire plt.savefig()



# ---------------- Line Chart ----------------

def line_chart(df, col1, columns, title="Line Chart", xlabel=None, ylabel=None, step=None):
    """
    Displays a line chart using one column for the x-axis and one or several columns for y-axis lines.

    Parameters:
    df      : pandas DataFrame containing the data
    col1    : str, column name for x-axis
    columns : list of str, column names to plot as lines
    title   : str, optional, title of the chart
    xlabel  : str, optional, label for x-axis (defaults to col1)
    ylabel  : str, optional, label for y-axis (defaults to "Values")
    step    : float, optional, step size for the grid on x and y axes
     
    Example:
    line_chart(df, "Time", ["Temperature1", "Temperature2"], title="Mean Temperature vs Time", step=2)
    """
    colors = cm.viridis(np.linspace(0, 1, len(columns)))  # generate different colors per line
    plt.figure(figsize=(10,6))
    
    # Plot each line
    for i, col in enumerate(columns):
        plt.plot(df[col1], df[col].astype(float), marker='o', color=colors[i], label=col)

    plt.title(title)
    plt.xlabel(xlabel if xlabel else col1)
    plt.ylabel(ylabel if ylabel else "Values")
    plt.ylim(bottom=0)  # start y-axis at 0
    
    # Optional: grid with step
    if step and step > 0:
        x_min, x_max = df[col1].min(), df[col1].max()
        y_min, y_max = 0, df[columns].max().max()
        plt.xticks(np.arange(x_min, x_max + step, step))
        plt.yticks(np.arange(y_min, y_max + step, step))
    
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    plt.legend()
    plt.show()


##-------------- Scatter Plot ---------------

def scatter_chart(df, col1, columns, title="Scatter Plot", xlabel=None, ylabel=None, step=None):
    """
    Displays a scatter plot using one column for the x-axis and one or several columns for y-axis points.

    Parameters:
    df      : pandas DataFrame containing the data
    col1    : str, column name for x-axis
    columns : list of str, column names to plot as scatter points
    title   : str, optional, title of the chart
    xlabel  : str, optional, label for x-axis (defaults to col1)
    ylabel  : str, optional, label for y-axis (defaults to "Values")
    step    : float, optional, step size for the grid on x and y axes
     
    Example:
    scatter_chart(df, "Precipitation", ["fluid_flow1", "fluid_flow2"], title="Mean fluid flow vs precipitation", step=2)
    """
    colors = cm.viridis(np.linspace(0, 1, len(columns)))  # different color per column
    plt.figure(figsize=(10,6))
    
    # Plot each column as scatter points
    for i, col in enumerate(columns):
        plt.scatter(df[col1], df[col].astype(float), color=colors[i], label=col, s=50)

    plt.title(title)
    plt.xlabel(xlabel if xlabel else col1)
    plt.ylabel(ylabel if ylabel else "Values") 
    plt.ylim(bottom=0)
    plt.xlim(left=0)
    
    
    if step and step > 0: # Grid with optional step
        x_min, x_max = df[col1].min(), df[col1].max()
        y_min, y_max = 0, df[columns].max().max()
        plt.xticks(np.arange(x_min, x_max + step, step))
        plt.yticks(np.arange(y_min, y_max + step, step))
    
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    plt.legend()
    plt.show()


def radar_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne catégorie ---
    try:
        cat_idx = int(input("\nIndex de la colonne catégories (axes du radar) : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier")

    if cat_idx < 0 or cat_idx >= len(df.columns):
        raise IndexError("Index de colonne catégorie invalide")

    category_col = df.columns[cat_idx]

    # --- Choix des colonnes de valeurs ---
    value_idx_input = input(
        "Index des colonnes de valeurs (séparés par une virgule, ex: 1,2) : "
    )

    try:
        value_idx = sorted(
            set(int(i.strip()) for i in value_idx_input.split(","))
        )
    except ValueError:
        raise ValueError("Les index doivent être des nombres entiers")

    if cat_idx in value_idx:
        raise ValueError("La colonne catégorie ne peut pas être une colonne de valeurs")

    for i in value_idx:
        if i < 0 or i >= len(df.columns):
            raise IndexError(f"Index invalide : {i}")

    value_cols = [df.columns[i] for i in value_idx]

    # --- Préparation du radar ---
    categories = df[category_col].astype(str).values
    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))
    colors = cm.viridis(np.linspace(0, 1, len(value_cols)))

    for i, col in enumerate(value_cols):
        values = df[col].astype(float).values.tolist()
        values += values[:1]

        ax.plot(angles, values, linewidth=2, label=col, color=colors[i])
        ax.fill(angles, values, alpha=0.25, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title("Radar Chart", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)

    plt.show()# a voir si on laisse cette ligne




# ----------------- Test -----------------

'''
# créer le dossier AVANT
os.makedirs("output", exist_ok=True)

# Bar chart 
bar_chart(df_test, "col1", "col2", title="Bar Chart")

# sauvegarde de la figure courante
plt.savefig("output/bar_chart.png")
plt.close()

# radar chart

radar_chart(df_test)

plt.savefig("output/radar_chart.png", bbox_inches="tight")
plt.close()

# Line chart
line_chart(df_test, "col1", columns=[ "col2", "col3", "col4"], title="Line Chart Test")


# scatter plot
#scatter_chart(df_test, "col1", columns=[ "col2", "col3", "col4"])
'''