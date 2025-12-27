import pandas as pd
import os

def process_news_data(input_dir="data/raw/mind_large"):
    print("Début du nettoyage des données (logique notebook)...")
    
    # Définition des sets et headers
    sets = ["train", "dev", "test"]
    news_header = ["id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]
    
    dfs = []
    
    # Chargement et concaténation 
    for _set in sets:
        file_path = os.path.join(input_dir, f"news_{_set}.tsv")
        if os.path.exists(file_path):
            print(f"Chargement de {file_path}...")
            df_set = pd.read_csv(file_path, names=news_header, sep="\t")
            dfs.append(df_set)
        else:
            print(f"Attention: Fichier {file_path} introuvable.")
    
    if not dfs:
        raise FileNotFoundError("Aucun fichier de données trouvé.")

    all_news_df = pd.concat(dfs, ignore_index=True)
    print(f"Total brut : {len(all_news_df)} lignes.")

    # --- Nettoyage ---

    # Suppression des colonnes inutiles
    cols_to_drop = ["url", "title_entities", "abstract_entities"]
    all_news_df = all_news_df.drop(columns=cols_to_drop, errors="ignore")

    # Gestion des valeurs nulles
    # "abstract" prend la valeur de "title" si vide
    all_news_df["abstract"] = all_news_df["abstract"].fillna(all_news_df["title"])
    # Fallback si title ou abstract sont encore vides
    all_news_df["title"] = all_news_df["title"].fillna("No Title")
    all_news_df["abstract"] = all_news_df["abstract"].fillna("No Abstract")

    # Fonction de nettoyage texte
    def clean_text(t):
        if isinstance(t, str):
            return t.strip().replace("\t", " ").replace("\n", " ")
        return t

    all_news_df["title"] = all_news_df["title"].apply(clean_text)
    all_news_df["abstract"] = all_news_df["abstract"].apply(clean_text)

    # Standardisation catégories
    all_news_df["category"] = all_news_df["category"].str.lower().str.strip()
    all_news_df["subcategory"] = all_news_df["subcategory"].str.lower().str.strip()

    # Dédoublonnage sur l'ID
    all_news_df = all_news_df.drop_duplicates(subset=["id"], keep="first")

    print(f"Données nettoyées : {len(all_news_df)} articles uniques.")
    return all_news_df

if __name__ == "__main__":
    # Pour tester isolément
    process_news_data()