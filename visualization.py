import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import matplotlib.dates as mdates


def ask_date_visualization(message):
    while True:
        user_input = input(message).strip()
        if user_input == "":
            return None
        try:
            return pd.to_datetime(user_input, dayfirst=True) # à voir si on garde dayfirst
        except Exception:
            print("Format invalide ❌ Utilisez YYYY-MM-DD ou DD/MM/YYYY")


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

# ---------------- Bar Chart ---------------- a été modifié pour correspondre à nouvelle structure

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



# ---------------- Line Chart ---------------- a été modifiée

def line_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix X ---
    try:
        x_idx = int(input("\nIndex de la colonne pour l'axe X : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne X")
    
    if x_idx < 0 or x_idx >= len(df.columns):
        raise IndexError("Index de colonne X invalide")

    # --- Choix Y ---
    y_idx_input = input("Index des colonnes pour l'axe Y (séparés par une virgule, ex: 1,2) : ")
    
    try:
        y_idx = sorted(set(int(i.strip()) for i in y_idx_input.split(",")))
    except ValueError:
        raise ValueError("Les index doivent être des nombres entiers")
    
    if x_idx in y_idx:
        raise ValueError("La colonne X ne peut pas être dans les colonnes Y")
    
    for i in y_idx:
        if i < 0 or i >= len(df.columns):
            raise IndexError(f"Index Y invalide : {i}")
    
    x_col = df.columns[x_idx]
    y_cols = [df.columns[i] for i in y_idx]

    # --- Colonne temporelle (supposée être la première) ---
    date_col = df.columns[0]

    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception:
        raise ValueError("La première colonne doit contenir des dates valides")

    # --- Affichage période disponible ---
    df_valid = df[df[date_col].notna()]
    if df_valid.empty:
        raise ValueError("Aucune date valide trouvée")

    min_date = df_valid[date_col].min()
    max_date = df_valid[date_col].max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période (laisser vide pour tout afficher)")

    start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date_visualization("Date de fin   (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]

    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée disponible sur la période sélectionnée")

    # Optionnel : trier par date pour éviter des lignes cassées
    #df_period = df_period.sort_values(by=date_col)

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(10,6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    for i, col in enumerate(y_cols):
        y = df_period[col].astype(float)
        x = df_period[x_col]

        ax.plot(x, y, marker='o', label=col, color=colors[i])

    ax.set_title(f"Line Chart: {', '.join(y_cols)} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Values")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()

    return fig

'''
Vieux line chart qui est faux
def line_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne X ---
    try:
        x_idx = int(input("\nIndex de la colonne pour l'axe X : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne X")
    
    if x_idx < 0 or x_idx >= len(df.columns):
        raise IndexError("Index de colonne X invalide")
    
    # --- Choix des colonnes Y ---
    y_idx_input = input("Index des colonnes pour l'axe Y (séparés par une virgule, ex: 1,2) : ")
    
    try:
        y_idx = sorted(set(int(i.strip()) for i in y_idx_input.split(",")))
    except ValueError:
        raise ValueError("Les index doivent être des nombres entiers")
    
    if x_idx in y_idx:
        raise ValueError("La colonne X ne peut pas être dans les colonnes Y")
    
    for i in y_idx:
        if i < 0 or i >= len(df.columns):
            raise IndexError(f"Index Y invalide : {i}")
    
    x_col = df.columns[x_idx]
    y_cols = [df.columns[i] for i in y_idx]

    

    mask = pd.Series(True, index=df.index)

    date_col = df.columns[0]

    #try:
        #date_series = pd.to_datetime(df[date_col])
        #is_datetime = True
    #except Exception:
        #is_datetime = False

    

    
    choice = input("Voulez-vous filtrer par période ? (o/n) : ").strip().lower()

    if choice == "o":

        min_date = date_col.min()
        max_date = date_col.max()

        print(f"Période disponible : {min_date.date()} → {max_date.date()}, attention, il peut y avoir des NaN")


        start_date = ask_date_visualization("Date de début : ")
        end_date   = ask_date_visualization("Date de fin   : ")

        if start_date and end_date and end_date < start_date:
            raise ValueError("La date de fin doit être postérieure à la date de début")

        if start_date:
            mask &= (date_series >= start_date)
        if end_date:
            mask &= (date_series <= end_date)

        if not mask.any():
            raise ValueError("Aucune donnée disponible sur cette période")

    else:
        print("\nLa première colonne n'est pas une date → filtrage ignoré.")


    # --- Création du graphique ---

    fig, ax = plt.subplots(figsize=(10,6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    for i, col in enumerate(y_cols):
        y = df[col].astype(float)
        ax.plot(df[x_col][mask], y[mask], marker='o', label=col, color=colors[i])


    ax.set_title(f"Line Chart: {', '.join(y_cols)} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Values")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()
    
    return fig  # retourne la figure pour pouvoir sauvegarder
'''

##-------------- Scatter Plot --------------- a été modifié, il faut reprendre nonobstant pour que ce soit plus beau
def scatter_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne X ---
    try:
        x_idx = int(input("\nIndex de la colonne pour l'axe X : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne X")
    
    if x_idx < 0 or x_idx >= len(df.columns):
        raise IndexError("Index de colonne X invalide")
    
    # --- Choix des colonnes Y ---
    y_idx_input = input("Index des colonnes pour l'axe Y (séparés par une virgule, ex: 1,2) : ")
    
    try:
        y_idx = sorted(set(int(i.strip()) for i in y_idx_input.split(",")))
    except ValueError:
        raise ValueError("Les index doivent être des nombres entiers")
    
    if x_idx in y_idx:
        raise ValueError("La colonne X ne peut pas être dans les colonnes Y")
    
    for i in y_idx:
        if i < 0 or i >= len(df.columns):
            raise IndexError(f"Index Y invalide : {i}")
    
    x_col = df.columns[x_idx]
    y_cols = [df.columns[i] for i in y_idx]

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(10,6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    for i, col in enumerate(y_cols):
        y = df[col].astype(float)
        ax.scatter(df[x_col], y, label=col, color=colors[i], s=50)

    ax.set_title(f"Scatter Plot: {', '.join(y_cols)} vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Values")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()

    return fig  # retourne la figure pour pouvoir sauvegarder


# ---------------- Radar Chart ---------------- a été modifié pour correspondre à nouvelle structure

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


# ---------------- Histogram Chart ---------------- a été modifié pour correspondre à nouvelle structure

def histogram_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choix de la colonne ---
    try:
        col_idx = int(input("\nIndex de la colonne à afficher en histogramme : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour la colonne")
    
    if col_idx < 0 or col_idx >= len(df.columns):
        raise IndexError("Index de colonne invalide")
    
    col_name = df.columns[col_idx]

    # --- Choix du nombre de bins ---
    try:
        bins = int(input("Nombre de bins pour l'histogramme : "))
    except ValueError:
        raise ValueError("Veuillez entrer un nombre entier pour le nombre de bins")
    
    if bins <= 0:
        raise ValueError("Le nombre de bins doit être supérieur à 0")

    # --- Création de l'histogramme ---
    fig, ax = plt.subplots(figsize=(8,5))
    values = df[col_name].astype(float)
    
    ax.hist(values, bins=bins, color='skyblue', edgecolor='black')
    ax.set_title(f"Histogram of {col_name}")
    ax.set_xlabel(col_name)
    ax.set_ylabel("Count")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)

    return fig  # retourne la figure pour sauvegarder



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