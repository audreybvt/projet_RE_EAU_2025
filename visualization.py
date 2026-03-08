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
            print("Format invalide ; utilisez YYYY-MM-DD ou DD/MM/YYYY")




# ---------------- Bar Chart ---------------- 


def bar_chart(df):
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

    # --- Choix de la colonne Y ---
    while True:
        try:
            y_idx = int(input("Index de la colonne pour l'axe Y : "))
            if y_idx < 0 or y_idx >= len(df.columns):
                raise IndexError
            if y_idx == x_idx:
                raise ValueError
            break
        except ValueError:
            print("La colonne Y doit être différente de la colonne X.")
        except IndexError:
            print("Index de colonne Y invalide.")

      
    x_col = df.columns[x_idx]
    y_col = df.columns[y_idx]

    
    # --- Gestion date ---
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df_valid = df[df[date_col].notna()]
    if df_valid.empty:
        raise ValueError("Aucune date valide trouvée")

    print("\nPériode disponible :")
    print(f" Du {df_valid[date_col].min().date()} au {df_valid[date_col].max().date()}")

    print("\nDéfinition de la période d'affichage des données (laisser vide pour tout afficher)")
    start_date = ask_date_visualization("Date de début : ")
    end_date   = ask_date_visualization("Date de fin   : ")

    df_period = df_valid.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]
    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée sur la période sélectionnée")

    # --- Titres personnalisés des axes ---
    x_label = input(f"Titre pour l'axe X (laisser vide pour '{x_col}') : ").strip()
    y_label = input(f"Titre pour l'axe Y (laisser vide pour '{y_col}') : ").strip()

    if x_label == "":
        x_label = x_col

    if y_label == "":
        y_label = y_col

    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Bar chart: {y_label} en fonction de {x_label}"
        

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(8,5))
    colors = cm.viridis(np.linspace(0, 1, len(df_period)))

    ax.bar(df_period[x_col], df_period[y_col], color=colors)

    ax.set_title(custom_title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    return fig


# ---------------- Line Chart ---------------- 

def line_chart(df):
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")

    
    # --- Choix X ---
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

    # --- Choix Y ---
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

    print("\nDéfinition de la période d'affichage des données (laisser vide pour tout afficher)")

    start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date_visualization("Date de fin (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]

    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée disponible sur la période sélectionnée")

    # Optionnel : trier par date pour éviter des lignes cassées
    #df_period = df_period.sort_values(by=date_col)

    # --- Titres personnalisés des axes ---
    x_label = input(f"Titre pour l'axe X (laisser vide pour '{x_col}') : ").strip()
    if x_label == "":
        x_label = x_col

    y_label = input("Titre pour l'axe Y (laisser vide pour 'Values') : ").strip()
    if y_label == "":
        y_label = "Values"

    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Line chart: {', '.join(y_cols)} en fonction de {x_label}"

    
    # --- Légende personnalisée ---
    legend_input = input("Noms pour la légende (séparés par une virgule (ex: Modèle A,Modèle B), laisser vide pour noms par défaut) : ").strip()

    if legend_input == "":
        legend_labels = y_cols
    else:
        legend_labels = [name.strip() for name in legend_input.split(",")]

        if len(legend_labels) != len(y_cols):
            raise ValueError("Le nombre de noms de légende doit correspondre au nombre de colonnes Y")

    # --- Création du graphique ---
    fig, ax = plt.subplots(figsize=(10,6))
    colors = cm.viridis(np.linspace(0, 1, len(y_cols)))

    for i, col in enumerate(y_cols):
        y = df_period[col].astype(float)
        x = df_period[x_col]

        ax.plot(x, y, marker='o', markersize=3, linewidth=1, label=legend_labels[i], color=colors[i])

    ax.set_title(custom_title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()

    return fig



##-------------- Scatter Plot ---------------

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
    start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date_visualization("Date de fin  (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df_valid.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]
    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée sur la période sélectionnée")
    

    # --- Titres des axes ---
    x_label = input(f"Titre pour l'axe X (laisser vide pour '{x_col}') : ").strip()
    if x_label == "":
        x_label = x_col

    y_label = input("Titre pour l'axe Y (laisser vide pour 'Values') : ").strip()
    if y_label == "":
        y_label = "Values"

    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Scatter chart: {', '.join(y_cols)} en fonction de {x_label}"

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
    start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date_visualization("Date de fin  (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df_valid.copy()


    ###
# Filtrer df_period selon la colonne de dates choisie pour le radar
    df_period = df_period[df_period[category_col] >= start_date] if start_date is not None else df_period
    df_period = df_period[df_period[category_col] <= end_date]   if end_date   is not None else df_period
    ###

    #if start_date is not None:
        #df_period = df_period[df_period[date_col] >= start_date]
    #if end_date is not None:
        #df_period = df_period[df_period[date_col] <= end_date]



    if df_period.empty:
        raise ValueError("Aucune donnée sur la période sélectionnée")

    # Supprimer les lignes sans valeurs pour le radar
    df_period = df_period.dropna(subset=value_cols, how="all")

    if df_period.empty:
        raise ValueError("Aucune valeur disponible pour les colonnes sélectionnées sur cette période")
    
    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Radar chart: {', '.join(value_cols)}"


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

def histogram_chart(df):
    #version choix période
    print("\nColonnes disponibles :")
    for i, col in enumerate(df.columns):
        print(f" [{i}] {col}")



    # --- Choix de la colonne ---
    while True:
        try:
            col_idx = int(input("\nIndex de la colonne à représenter : "))
            if col_idx < 0 or col_idx >= len(df.columns):
                raise IndexError
            break
        except ValueError:
            print("Veuillez entrer un nombre entier.")
        except IndexError:
            print("Index de colonne invalide.")

    col_name = df.columns[col_idx]


    # --- Choix du nombre de bins ---
    while True:
        try:
            bins = int(input("Nombre de bins pour l'histogramme : "))
            if bins <= 0:
                raise ValueError
            break
        except ValueError:
            print("Le nombre de bins doit être un entier strictement positif.")
    
 

    # --- Période d'affichage ---
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df_valid = df[df[date_col].notna()]

    print("\nPériode disponible :")
    print(f" Du {df_valid[date_col].min().date()} au {df_valid[date_col].max().date()}")

    print("\nDéfinition de la période d'affichage des données (laisser vide pour tout afficher)")
    start_date = ask_date_visualization("Date de début (YYYY-MM-DD ou DD/MM/YYYY) : ")
    end_date   = ask_date_visualization("Date de fin  (YYYY-MM-DD ou DD/MM/YYYY) : ")

    df_period = df_valid.copy()

    if start_date is not None:
        df_period = df_period[df_period[date_col] >= start_date]
    if end_date is not None:
        df_period = df_period[df_period[date_col] <= end_date]

    if df_period.empty:
        raise ValueError("Aucune donnée sur la période sélectionnée")
    
    # --- Titres des axes ---
    x_label = input(f"Titre pour l'axe X (laisser vide pour '{col_name}') : ").strip()
    if x_label == "":
        x_label = col_name

    y_label = input("Titre pour l'axe Y (laisser vide pour 'Count') : ").strip()
    if y_label == "":
        y_label = "Count"

    # --- Titre global ---
    custom_title = input("Titre du graphique (laisser vide pour titre automatique) : ").strip()

    if custom_title == "":
        custom_title = f"Histogramme de {x_label}"

    # --- Graphique ---
    fig, ax = plt.subplots(figsize=(8,5))
    ax.hist(df_period[col_name].astype(float), bins=bins, 
            color='skyblue', edgecolor='black')

    ax.set_title(custom_title)
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