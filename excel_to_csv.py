import pandas as pd
#pip install openpyxl
'''
df = pd.read_excel("input/CSV/donnees_sandra_feuille2_test.xlsx")

# Enregistrer en CSV
df.to_csv(
    "input/CSV/donnees_sandra_feuille2_test.csv",
    sep=";",
    index=False
)
'''

'''
df = pd.read_excel(
    "input/CSV/donnees_sandra_feuille2_test.xlsx",
    header=[2, 3]   # lignes des en-têtes visibles sur ton image
)
df.columns = [
    f"{model}_{var}".strip("_")
    for model, var in df.columns
]

df = df.rename(columns={df.columns[0]: "Date"})
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

df.to_csv(
    "input/CSV/donnees_propres.csv",
    sep=";",
    index=False
)
'''
import pandas as pd

# Lecture Excel avec double en-tête
df = pd.read_excel(
    "input/excel/donnees_sandra_feuille2_test.xlsx",
    header=[2, 3]
)

# 🔹 Correction colonne Date issue du MultiIndex Excel
new_cols = list(df.columns)
# Si la première colonne contient "Date" ou est vide, on la renomme proprement
if "Date" in str(new_cols[0]) or "Unnamed" in str(new_cols[0]):
    new_cols[0] = ("Date", "")
df.columns = pd.MultiIndex.from_tuples(new_cols)

# Conversion en datetime
df[("Date", "")] = pd.to_datetime(
    df[("Date", "")],
    dayfirst=True,
    errors="coerce"
)

# 🔥 Passage en format long (empile les modèles)
df_long = (
    df
    .set_index(("Date", ""))
    .stack(level=0)        # empile les modèles
    .reset_index()
    .rename(columns={"level_1": "model"})
)

# Supprime le nom MultiIndex des colonnes
df_long.columns.name = None

# 🔹 Optionnel : renommer les colonnes pour plus de clarté
df_long = df_long.rename(columns={("Date", ""): "Date"})

# Sauvegarde CSV propre
df_long.to_csv(
    "input/CSV/donnees_longues.csv",
    sep=";",
    index=False
)

print("✅ CSV long généré : input/CSV/donnees_longues.csv")
print(df_long.head())