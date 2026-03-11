import xarray as xr
import calendar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import matplotlib.dates as mdates


### UTILITIES ###
def subset_time(ds, start, end):

    if start is not None:
        ds = ds.sel(time=slice(start, None))

    if end is not None:
        ds = ds.sel(time=slice(None, end))

    return ds

def ask_variable(ds: xr.Dataset, multiple: bool = False, prompt: str = None) -> list | str:
    """
    Permet de choisir une ou plusieurs variables/coords dans un Dataset xarray.
    
    Parameters:
        ds       : xarray.Dataset
        multiple : True pour choisir plusieurs variables
        prompt   : message d'invite personnalisé
    
    Returns:
        str si single choice, list[str] si multiple
    """
    # Liste de toutes les variables et coordonnées
    choices = list(ds.data_vars) + list(ds.coords)
    
    # Message par défaut
    message = prompt or ("Choisir la variable (ou les variables séparées par une virgule) :" if multiple 
                        else "Choisir la variable :")
    
    # Affichage des options
    print("\nVariables et coordonnées disponibles :")
    for i, var in enumerate(choices):
        print(f" [{i}] {var}")
    
    while True:
        user_input = input(f"{message} ").strip()
        try:
            if multiple:
                idx_list = sorted(set(int(i.strip()) for i in user_input.split(",")))
                selected = [choices[i] for i in idx_list]
            else:
                idx = int(user_input)
                selected = choices[idx]
            
            return selected
        except (ValueError, IndexError):
            print("Entrée invalide. Veuillez entrer les indices correspondants aux variables disponibles.")

def ask_time_period(ds):
    """
    Ask the user for a start and end date within the dataset time range.
    Returns (start_date, end_date) as pandas Timestamp or None.
    """

    time_values = pd.to_datetime(ds["time"].values)

    min_date = time_values.min()
    max_date = time_values.max()

    print("\nPériode disponible :")
    print(f" Du {min_date.date()} au {max_date.date()}")

    print("\nDéfinition de la période (laisser vide pour tout afficher)")

    while True:

        start_input = input("Date de début (YYYY-MM-DD) : ").strip()
        end_input = input("Date de fin (YYYY-MM-DD) : ").strip()

        start_date = pd.to_datetime(start_input) if start_input else None
        end_date = pd.to_datetime(end_input) if end_input else None

        # --- vérifier cohérence ---
        if start_date and end_date and start_date > end_date:
            print("La date de début doit être antérieure à la date de fin.")
            continue

        # --- vérifier dans le domaine ---
        if start_date and start_date < min_date:
            print("La date de début est avant la période disponible.")
            continue

        if end_date and end_date > max_date:
            print("La date de fin est après la période disponible.")
            continue

        break

    return start_date, end_date

def dataset_to_dataframe(ds):

    return ds.to_dataframe().reset_index()

def format_period_text(start_date, end_date):
    """
    Return a readable string describing the selected period.
    """

    if start_date and end_date:
        return f" ({start_date.date()} → {end_date.date()})"

    elif start_date:
        return f" (from {start_date.date()})"

    elif end_date:
        return f" (until {end_date.date()})"

    else:
        return ""

def configure_plot_labels_and_title(x_default: str, y_defaults: list[str] | str, multiple_y: bool = False):
    """
    Demande à l'utilisateur de personnaliser :
    - titre du graphique
    - labels axes X/Y avec unités
    - légende si multiple Y

    Args:
        x_default: nom par défaut de la variable X
        y_defaults: nom(s) par défaut des variables Y
        multiple_y: True si plusieurs Y pour gérer la légende

    Returns:
        dict avec clés :
        - x_label
        - y_label
        - legend_labels (liste)
        - title
    """
    # --- Labels axes ---
    x_label = input(f"Label for X-axis (leave empty for '{x_default}'): ").strip()
    x_label = x_label if x_label != "" else x_default
    x_unit = input("Unit for X-axis (leave empty for none): ").strip()
    x_label = build_axis_label(x_label, x_unit)

    if multiple_y:
        y_label_input = input(f"Label for Y-axis (leave empty for 'Values'): ").strip()
        y_unit = input("Unit for Y-axis (leave empty for none): ").strip()
        y_label = build_axis_label(y_label_input if y_label_input != "" else "Values", y_unit)
        legend_input = input(f"Legend names for each Y (comma-separated, leave empty for defaults: {', '.join(y_defaults)}): ").strip()
        if legend_input == "":
            legend_labels = y_defaults
        else:
            legend_labels = [l.strip() for l in legend_input.split(",")]
            if len(legend_labels) != len(y_defaults):
                raise ValueError("Number of legend labels must match number of Y variables")
    else:
        y_label_input = input(f"Label for Y-axis (leave empty for '{y_defaults}'): ").strip()
        y_unit = input("Unit for Y-axis (leave empty for none): ").strip()
        y_label = build_axis_label(y_label_input if y_label_input != "" else y_defaults, y_unit)
        legend_labels = []

    # --- Titre global ---
    custom_title = input("Chart title (leave empty for automatic): ").strip()

    return {
        "x_label": x_label,
        "y_label": y_label,
        "legend_labels": legend_labels,
        "title": custom_title
    }

def build_axis_label(label, unit):
    """
    Construit le label d'axe avec unité si elle existe.
    Exemple :
    label="Temperature", unit="°C" -> "Temperature (°C)"
    """
    unit = unit.strip()
    if unit == "":
        return label
    return f"{label} ({unit})"


# ---------------- Bar Chart ---------------- 

def bar_chart(df):
    print("\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    # --- Choice of X column ---
    while True:
        try:
            # Correction : Utilisation de int() au lieu de str() pour l'index
            x_idx = int(input("\nIndex for X-axis column: "))
            if x_idx < 0 or x_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Please enter a valid integer.")
        except IndexError:
            print("Invalid column index for X.")

    # --- Choice of Y column ---
    while True:
        try:
            y_idx = int(input("Index for Y-axis column: "))
            if y_idx < 0 or y_idx >= len(df.columns):
                raise IndexError
            if y_idx == x_idx:
                raise ValueError
            break
        except ValueError:
            print("Y column must be different from X column.")
        except IndexError:
            print("Invalid column index for Y.")

    x_col = df.columns[x_idx]
    y_col = df.columns[y_idx]

    # --- Date handling ---
    # On suppose que la colonne 0 est la date pour le filtrage temporel
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df_valid = df[df[date_col].notna()]
    if df_valid.empty:
        # Si aucune date n'est trouvée (ex: on travaille sur un résumé de 12 lignes),
        # on utilise le dataframe tel quel pour éviter l'erreur.
        df_valid = df.copy()
        print("\nNote: No valid dates found for filtering, using raw data.")
    else:
        print("\nAvailable period:")
        print(f" From {df_valid[date_col].min().date()} to {df_valid[date_col].max().date()}")

    print("\nDefine the display period (leave empty to show all)")
       
    while True:
        # Hypothèse: les fonctions ask_date_visualization et format_period_text existent ailleurs
        start_date = ask_date_visualization("Start date (YYYY-MM-DD or DD/MM/YYYY): ")
        end_date   = ask_date_visualization("End date (YYYY-MM-DD or DD/MM/YYYY): ")

        if start_date and end_date and start_date > end_date:
            print("Start date must be before end date.")
            continue

        df_period = df_valid.copy()

        # On ne filtre par date que si des dates valides existent
        if not df_valid[date_col].isna().all():
            if start_date is not None:
                df_period = df_period[df_period[date_col] >= start_date]
            if end_date is not None:
                df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("No data for this period. Please enter other dates.")
        else:
            break

    period_text = format_period_text(start_date, end_date)

    # --- Custom Axis Labels ---
    x_label = input(f"Label for X-axis (leave empty for '{x_col}'): ").strip()
    y_label = input(f"Label for Y-axis (leave empty for '{y_col}'): ").strip()

    x_label = x_label if x_label != "" else x_col
    y_label = y_label if y_label != "" else y_col


    # --- Units ---
    x_unit = input("Unit for X-axis (leave empty for none): ").strip()
    y_unit = input("Unit for Y-axis (leave empty for none): ").strip()

    # Build final labels
    x_label = build_axis_label(x_label, x_unit)
    y_label = build_axis_label(y_label, y_unit)



    # --- Global Title ---
    custom_title = input("Chart title (leave empty for automatic title): ").strip()
    
    if custom_title == "":
        custom_title = f"Bar chart: {y_label} vs {x_label}{period_text}"

    # Sorting month and season 
    
    month_order = [calendar.month_name[i] for i in range(1, 13)] # from january to december
    season_order = ['Spring', 'Summer', 'Autumn', 'Winter'] # to adjust if different season name (wet season, dry season eventually)
    df_plot = df_period.copy()
    sample_val = str(df_plot[x_col].iloc[0]) if not df_plot.empty else ""
    
    sort_key = None
    if any(m in df_plot[x_col].values for m in month_order):
        sort_key = month_order
    elif any(s in df_plot[x_col].values for s in season_order):
        sort_key = season_order

    if sort_key:
        df_plot[x_col] = pd.Categorical(df_plot[x_col], categories=sort_key, ordered=True)
        df_plot = df_plot.sort_values(x_col)

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(8,5))
    
    # On utilise maintenant df_plot qui est trié
    x_data = df_plot[x_col].astype(str)
    y_data = df_plot[y_col]

    colors = cm.viridis(np.linspace(0, 1, len(df_plot)))
    ax.bar(x_data, y_data, color=colors)
    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(8,5))
    
    # X est traité comme des chaînes de caractères 
    x_data = df_period[x_col].astype(str)
    y_data = df_period[y_col]

    colors = cm.viridis(np.linspace(0, 1, len(df_period)))

    ax.bar(x_data, y_data, color=colors)

    ax.set_title(custom_title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    
    # Rotation des labels X si ce sont des noms longs (mois, saisons)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return fig

# ---------------- Line Chart ---------------- 
'''
def line_chart(ds: xr.Dataset):
    """
    Trace une série temporelle depuis un xarray.Dataset
    avec gestion automatique des dimensions.
    """

    if not isinstance(ds, xr.Dataset):
        raise TypeError("Attendu: xarray.Dataset")

    # --- Choix des variables ---
    x_col = ask_variable(ds, prompt="Choisir la variable pour l'axe X : ")
    y_cols = ask_variable(
        ds,
        multiple=True,
        prompt="Choisir une ou plusieurs variables pour l'axe Y (séparées par ',') : "
    )

    # --- Sélection période ---
    start_date, end_date = ask_time_period(ds)
    ds_period = subset_time(ds, start_date, end_date)

    period_text = format_period_text(start_date, end_date)

    # --- Préparation X ---
    if x_col in ds_period.coords:
        x_arr = ds_period.coords[x_col]
    else:
        x_arr = ds_period[x_col]

    if x_arr.ndim != 1:
        raise ValueError(f"La variable X '{x_col}' doit être 1D")

    x_dim = x_arr.dims[0]
    x_values = x_arr.values

    # --- Configuration titres / labels ---
    labels = configure_plot_labels_and_title(
        x_default=x_col,
        y_defaults=y_cols,
        multiple_y=True
    )

    x_label = labels["x_label"]
    y_label = labels["y_label"]
    legend_labels = labels["legend_labels"]
    title = labels["title"] or f"Line chart: {', '.join(y_cols)} vs {x_label}{period_text}"

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    for i, var in enumerate(y_cols):

        da = ds_period[var]

        # --- Cas 1 : la variable dépend de X ---
        if x_dim in da.dims:

            other_dims = tuple(d for d in da.dims if d != x_dim)

            if other_dims:
                da1d = da.mean(dim=other_dims, skipna=True)
            else:
                da1d = da

            # Alignement éventuel
            if da1d.sizes.get(x_dim, None) != len(x_values):

                if x_col in ds_period and np.array_equal(ds_period[x_col].values, x_values):
                    da1d = da1d.reindex({x_dim: ds_period[x_col]})

            y_vals = da1d.values

        # --- Cas 2 : la variable ne dépend pas de X ---
        else:

            y_scalar = da.mean().item()
            y_vals = np.full_like(x_values, fill_value=y_scalar, dtype=float)

        # --- Conversion numérique si nécessaire ---
        if not np.issubdtype(np.array(y_vals).dtype, np.number):
            try:
                y_vals = y_vals.astype(str)
                y_vals = np.char.replace(y_vals, ",", ".").astype(float)
            except Exception:
                raise ValueError(f"Impossible de convertir '{var}' en float pour le tracé.")

        ax.plot(
            x_values,
            y_vals,
            marker='o',
            markersize=3,
            linewidth=1,
            label=legend_labels[i],
            color=colors[i]
        )

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()

    return fig
'''

def line_chart(ds: xr.Dataset):

    if not isinstance(ds, xr.Dataset):
        raise TypeError("Attendu : xarray.Dataset")

    # ----------------------
    # Choix variables
    # ----------------------

    x_name = ask_variable(ds, prompt="Variable pour X : ")

    y_names = ask_variable(
        ds,
        multiple=True,
        prompt="Variables pour Y (séparées par ,) : "
    )

    # ----------------------
    # période
    # ----------------------

    start_date, end_date = ask_time_period(ds)
    ds = subset_time(ds, start_date, end_date)

    # ----------------------
    # X
    # ----------------------

    x_arr = ds[x_name] if x_name in ds else ds.coords[x_name]

    if x_arr.ndim != 1:
        raise ValueError("X doit être 1D")

    x_dim = x_arr.dims[0]
    x_vals = x_arr.values

    # ----------------------
    # figure
    # ----------------------

    fig, ax = plt.subplots(figsize=(10,6))

    # ----------------------
    # boucle Y
    # ----------------------

    for y_name in y_names:

        da = ds[y_name]

        if x_dim not in da.dims:
            print(f"{y_name} ignoré (pas de dimension {x_dim})")
            continue

        # dimensions restantes
        dims = [d for d in da.dims if d != x_dim]

        selections = {}

        for dim in dims:

            coords = da.coords[dim].values

            if len(coords) == 1:
                selections[dim] = coords
                continue

            print(f"\nDimension '{dim}' :")

            for i,v in enumerate(coords):
                print(f"[{i}] {v}")

            choice = input(
                f"indices pour {dim} (ex 0,1 ou all) : "
            ).strip()

            if choice == "all":
                selections[dim] = coords
            else:
                idx = [int(i) for i in choice.split(",")]
                selections[dim] = coords[idx]

        # ----------------------
        # combinaisons
        # ----------------------

        import itertools

        combos = list(
            itertools.product(*selections.values())
        )

        dims_names = list(selections.keys())

        colors = cm.viridis(
            np.linspace(0,1,len(combos))
        )

        for i,combo in enumerate(combos):

            sel = dict(zip(dims_names,combo))

            da_sel = da.sel(**sel)

            y_vals = da_sel.values

            label = y_name

            if sel:
                label += " | " + ", ".join(
                    f"{k}={v}" for k,v in sel.items()
                )

            ax.plot(
                x_vals,
                y_vals,
                label=label,
                linewidth=1,
                color=colors[i]
            )

    # ----------------------
    # style
    # ----------------------

    ax.set_xlabel(x_name)
    ax.set_ylabel("Value")
    ax.set_title("Line chart")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    return fig

# -------------- Scatter Plot ---------------

def scatter_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")


    # --- Choix de la colonne X ---
    while True:
        try:
            x_idx = int(input("\nIndex de la colonne pour l'axe X : "))
            if x_idx < 0 or x_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne X invalide.")

    # --- Choix des colonnes Y ---
    while True:
        try:
            y_idx_input = input("Index des colonnes pour l'axe Y (ex: 1,2) : ")
            y_idx = sorted(set(int(i.strip()) for i in y_idx_input.split(",")))

            if x_idx in y_idx:
                raise ValueError

            for i in y_idx:
                if i < 0 or i >= len(df.columns):
                    raise IndexError

            break

        except ValueError:
            print("Les colonnes Y doivent être des entiers et différentes de X.")
        except IndexError:
            print("Un index Y est invalide.")

    
    x_col = df.columns[x_idx]
    y_cols = [df.columns[i] for i in y_idx]

    

    # --- Période d'affichage ---
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df_valid = df[df[date_col].notna()]
    if df_valid.empty:
        raise ValueError("Aucune date valide trouvée")
    
    print("\nPériode disponible :")
    print(f" Du {df_valid[date_col].min().date()} au {df_valid[date_col].max().date()}")

    print("\nDéfinition de la période d'affichage des données (laisser vide pour tout afficher)")
    while True:

        start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date_visualization("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

        if start_date and end_date and start_date > end_date:
            print("La date de début doit être antérieure à la date de fin.")
            continue

        df_period = df_valid.copy()

        if start_date is not None:
            df_period = df_period[df_period[date_col] >= start_date]
        if end_date is not None:
            df_period = df_period[df_period[date_col] <= end_date]

        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break

    
    period_text = format_period_text(start_date, end_date)
    

    # --- Titres des axes ---

    x_label = input(f"Label for X-axis (leave empty for '{x_col}'): ").strip()
    y_label = input(f"Label for Y-axis (leave empty for 'Values'): ").strip()

    x_label = x_label if x_label != "" else x_col
    y_label = y_label if y_label != "" else "Values"

    # --- Units ---
    x_unit = input("Unit for X-axis (leave empty for none): ").strip()
    y_unit = input("Unit for Y-axis (leave empty for none): ").strip()

    # Build final labels
    x_label = build_axis_label(x_label, x_unit)
    y_label = build_axis_label(y_label, y_unit)


    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Scatter chart: {', '.join(y_cols)} en fonction de {x_label}{period_text}"

    # --- Légende personnalisée ---
    legend_input = input("Noms pour la légende (séparés par une virgule (ex: Variable A,Variable B), laisser vide pour noms par défaut) : ").strip()

    if legend_input == "":
        legend_labels = y_cols
    else:
        legend_labels = [name.strip() for name in legend_input.split(",")]

        if len(legend_labels) != len(y_cols):
            raise ValueError("Le nombre de noms de légende doit correspondre au nombre de colonnes Y")

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(10,6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    #for i, col in enumerate(y_cols):
        #ax.scatter(df_period[x_col],df_period[col],label=legend_labels[i],color=colors[i],s=50)

    for i, col in enumerate(y_cols):

        x = pd.to_numeric(df_period[x_col], errors="coerce")
        y = pd.to_numeric(df_period[col], errors="coerce")

        data = pd.DataFrame({x_col: x, col: y}).dropna()

        ax.scatter(data[x_col],data[col],label=legend_labels[i],color=colors[i],s=50)

    ax.set_title(custom_title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    return fig

# ---------------- Radar Chart ----------------

def radar_chart(df):

    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")


    # --- Choix de la colonne catégorie ---
    while True:
        try:
            cat_idx = int(input("\nIndex de la colonne catégories (axes du radar) : "))
            if cat_idx < 0 or cat_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    category_col = df.columns[cat_idx]



    # --- Choix des colonnes de valeurs ---
    while True:
        try:
            value_idx_input = input("Index des colonnes de valeurs (séparés par une virgule, ex: 1,2) : ")
            value_idx = sorted(set(int(i.strip()) for i in value_idx_input.split(",")))

            if cat_idx in value_idx:
                raise ValueError

            for i in value_idx:
                if i < 0 or i >= len(df.columns):
                    raise IndexError

            break

        except ValueError:
            print("Les colonnes doivent être des entiers et différentes de la colonne catégorie.")
        except IndexError:
            print("Un index est invalide.")

  
    value_cols = [df.columns[i] for i in value_idx]
    

            
    # --- Date ---
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df_valid = df[df[date_col].notna()]
    if df_valid.empty:
        raise ValueError("Aucune date valide trouvée")

    print("\nPériode disponible :")
    print(f" Du {df_valid[date_col].min().date()} au {df_valid[date_col].max().date()}")

    print("\nDéfinition de la période d'affichage des données (laisser vide pour tout afficher)")


    while True:

        start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
        end_date   = ask_date_visualization("Date de fin  (YYYY-MM-DD ou DD/MM/YYYY) : ")

        if start_date and end_date and start_date > end_date:
            print("La date de début doit être antérieure à la date de fin.")
            continue

        df_period = df_valid.copy()

        df_period = df_period[df_period[date_col] >= start_date] if start_date is not None else df_period
        df_period = df_period[df_period[date_col] <= end_date]   if end_date   is not None else df_period
    
        if df_period.empty:
            print("Aucune donnée sur cette période. Veuillez entrer d'autres dates.")
        else:
            break
    
    
    period_text = format_period_text(start_date, end_date)

    # Supprimer les lignes sans valeurs pour le radar
    df_period = df_period.dropna(subset=value_cols, how="all")

    if df_period.empty:
        raise ValueError("Aucune valeur disponible pour les colonnes sélectionnées sur cette période")
    
    period_text = format_period_text(start_date, end_date)
    
    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    # --- Units for radar values ---
    units_input = input("Unités des variables radar (ex: kW, %, ms) - laisser vide si aucune : ").strip()

    if units_input != "":
        units_text = f" ({units_input})"
    else:
        units_text = ""

    if custom_title == "":
        custom_title = f"Radar chart: {', '.join(value_cols)}{units_text}{period_text}"
    else:
        custom_title = f"{custom_title}{units_text}"


    # --- Légende personnalisée ---
    legend_input = input("Noms pour la légende (séparés par une virgule, laisser vide pour noms par défaut) : ").strip()

    if legend_input == "":
        legend_labels = value_cols
    else:
        legend_labels = [name.strip() for name in legend_input.split(",")]

        if len(legend_labels) != len(value_cols):
            raise ValueError("Le nombre de noms doit correspondre au nombre de colonnes de valeurs")

    # --- Radar ---
    #categories = df_period[category_col].astype(str).values
    categories = df_period[category_col].dropna().astype(str).values
    #categories = df_period[date_col].dt.strftime('%Y-%m-%d').values
    N = len(categories)
    if N < 3:
        raise ValueError("Un radar nécessite au moins 3 catégories")

    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))

    # Sens horaire
    ax.set_theta_direction(-1)          # Inverse le sens de rotation
    ax.set_theta_offset(np.pi / 2)      # Commence en haut (12h)

    colors = cm.viridis(np.linspace(0, 1, len(value_cols)))

    # --- Ajustement de l'échelle radiale ---
    val_min = df_period[value_cols].min().min()
    val_max = df_period[value_cols].max().max()
    margin = 0.05 * (val_max - val_min)  # 5% de marge
    ax.set_ylim(val_min - margin, val_max + margin)

    for i, col in enumerate(value_cols):
        values = df_period[col].astype(float).values.tolist()
        values += values[:1]

        ax.plot(angles, values, label=legend_labels[i], color=colors[i])
        #ax.fill(angles, values, alpha=0.25, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    ax.set_title(custom_title)
    ax.legend(loc="upper right", bbox_to_anchor=(1.6, 1))

    return fig

# ---------------- Histogram Chart ----------------

def histogram_chart(ds: xr.Dataset):
    """
    Trace un histogramme depuis un xarray.Dataset.
    """
    col_name = ask_variable(ds, prompt="Choisir la variable à représenter : ")
    bins = int(input("Nombre de bins pour l'histogramme : ").strip())

    # --- Sélection période ---
    start_date, end_date = ask_time_period(ds)
    ds_period = subset_time(ds, start_date, end_date)
    period_text = format_period_text(start_date, end_date)

    # --- Configuration titres / labels ---
    labels = configure_plot_labels_and_title(x_default=col_name, y_defaults=col_name, multiple_y=False)
    x_label = labels["x_label"]
    y_label = labels["y_label"]
    title = labels["title"] or f"Histogramme de {x_label}{period_text}"

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(8, 5))
    data = ds_period[col_name].values.astype(float)
    ax.hist(data, bins=bins, color='skyblue', edgecolor='black')

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle='--', alpha=0.5)
    return fig

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