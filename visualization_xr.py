import xarray as xr
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

# ---------------- Bar Chart ---------------- #

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



# ---------------- Line Chart ---------------- #    


def line_chart(ds: xr.Dataset):
    
    if not isinstance(ds, xr.Dataset):
        raise TypeError("Attendu: xarray.Dataset")

    # --- Liste des candidats X et Y ---
    # X peut être une coordonnée (p.ex. 'time') OU une variable 1D.
    coords_list = list(ds.coords)
    data_vars_list = list(ds.data_vars)

    print("\nCoordonnées (candidates pour l'axe X) :")
    for i, c in enumerate(coords_list):
        dims = ", ".join(ds[c].dims)
        print(f"  [C{i}] {c}  (dims: {dims}, size: {ds[c].sizes.get(ds[c].dims[0], 'n/a')})")

    print("\nVariables (candidates pour l'axe X si 1D, et pour l'axe Y) :")
    for i, v in enumerate(data_vars_list):
        da = ds[v]
        dims = ", ".join([f"{d}({da.sizes[d]})" for d in da.dims])
        print(f"  [V{i}] {v:20s} dims: {dims or '—'}  dtype: {da.dtype}")

    # --- Choix X ---
    print("\nChoix de l'axe X :")
    print("  • Pour une coordonnée, tape 'C<index>' (ex: C0).")
    print("  • Pour une variable 1D, tape 'V<index>' (ex: V2).")

    x_key = input("Votre choix pour X (ex: C0 ou V2) : ").strip()

    if len(x_key) < 2 or x_key[0] not in ("C", "V") or not x_key[1:].isdigit():
        raise ValueError("Format invalide pour le choix X. Exemple attendu: C0 ou V2.")

    x_type, x_idx = x_key[0], int(x_key[1:])

    if x_type == "C":
        if x_idx < 0 or x_idx >= len(coords_list):
            raise IndexError("Index de coordonnée X invalide")
        x_name = coords_list[x_idx]
        x_arr = ds[x_name]
    else:  # "V"
        if x_idx < 0 or x_idx >= len(data_vars_list):
            raise IndexError("Index de variable X invalide")
        x_name = data_vars_list[x_idx]
        x_arr = ds[x_name]
        if x_arr.ndim != 1:
            raise ValueError(f"La variable '{x_name}' n'est pas 1D ; impossible de l'utiliser directement comme X.")

    # On impose que X soit 1D
    if x_arr.ndim != 1:
        raise ValueError(f"L'axe X choisi doit être 1D, trouvé dims {x_arr.dims}")

    # Nom de la dimension sous-jacente à X (ex: 'time', 'lon', etc.)
    x_dim = x_arr.dims[0]
    x_values = x_arr.values

    # --- Choix Y ---
    print("\nChoisissez les variables pour l'axe Y parmi la liste des Variables (V#).")
    y_input = input("Indices Y séparés par des virgules (ex: 1,2,5) : ").strip()

    try:
        y_indices = sorted(set(int(tok.strip()) for tok in y_input.split(",")))
    except Exception:
        raise ValueError("Indices Y invalides. Donnez des entiers séparés par des virgules.")

    for yi in y_indices:
        if yi < 0 or yi >= len(data_vars_list):
            raise IndexError(f"Index Y invalide : {yi}")

    y_names = [data_vars_list[i] for i in y_indices]

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = cm.viridis(np.linspace(0, 1, len(y_names)))

    for i, var in enumerate(y_names):
        da = ds[var]

        # Si la variable Y possède la dimension x_dim (par ex. 'time'), on s'aligne dessus.
        if x_dim in da.dims:
            # On souhaite une série 1D alignée sur x_dim ; si da a d'autres dims, on les moyenne.
            other_dims = tuple(d for d in da.dims if d != x_dim)
            if other_dims:
                da1d = da.mean(dim=other_dims, skipna=True)
            else:
                da1d = da

            # S'assurer même taille sur x_dim (parfois X est subset/coordonée indépendante)
            if da1d.sizes.get(x_dim, None) != x_values.shape[0]:
                # Essayer de reindexer si c'est la même coordonnée (nom et valeurs)
                if x_name in ds and np.array_equal(ds[x_name].values, x_values):
                    da1d = da1d.reindex({x_dim: ds[x_name]})
                # Sinon, on tente un alignement par interpolation (optionnel)
                # da1d = da1d.interp({x_dim: x_values})
            y_vals = da1d.values

        else:
            # Si la variable ne possède pas x_dim : on la réduit complètement à un scalaire,
            # puis on "broadcast" ce scalaire sur la longueur de X pour tracer une ligne plate.
            y_scalar = da.mean().item()  # moyenne globale
            y_vals = np.full_like(x_values, fill_value=y_scalar, dtype=float)

        # Conversion en float (si object/str)
        if not np.issubdtype(np.array(y_vals).dtype, np.number):
            # tentative de conversion "européenne" si besoin
            try:
                y_vals = y_vals.astype(str)
                y_vals = np.char.replace(y_vals, ",", ".").astype(float)
            except Exception:
                raise ValueError(f"Impossible de convertir '{var}' en float pour le tracé.")

        ax.plot(x_values, y_vals, marker='o', label=var, color=colors[i])

    ax.set_title(f"Line Chart: {', '.join(y_names)} vs {x_name}")
    ax.set_xlabel(x_name)
    ax.set_ylabel("Values")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()

    return fig

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