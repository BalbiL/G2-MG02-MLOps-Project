from download_data import download_and_extract
from clean_data import process_news_data
from load_supabase import load_data_safely

def run_pipeline():
    print("==========================================")
    print("   DÉMARRAGE DU DATA PIPELINE MIND")
    print("==========================================")
    
    # 1. EXTRACT
    print("\n[1/3] EXTRACT")
    try:
        download_and_extract(output_dir="data/raw")
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")
        return

    # 2. TRANSFORM
    print("\n[2/3] TRANSFORM")
    try:
        # Le script s'attend à trouver les données dans data/raw/mind_large
        df_news = process_news_data(input_dir="data/raw/mind_large")
    except Exception as e:
        print(f"Erreur lors du nettoyage : {e}")
        return

    # 3. LOAD
    print("\n[3/3] LOAD")
    try:
        # La fonction contient la sécurité (arrête si count > 100)
        load_data_safely(df_news, table_name="news")
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return

    print("\n==========================================")
    print("   PIPELINE TERMINÉ AVEC SUCCÈS")
    print("==========================================")

if __name__ == "__main__":
    run_pipeline()