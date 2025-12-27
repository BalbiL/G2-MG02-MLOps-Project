import os
import boto3

# Configuration
BUCKET_NAME = "s3-g2mg02"  # Remplacez par votre vrai nom de bucket S3 !
ARTIFACTS_DIR = "artifacts"

def upload_artifacts():
    print(f">>> Démarrage de l'upload depuis '{ARTIFACTS_DIR}' vers S3...")
    
    if not os.path.exists(ARTIFACTS_DIR):
        raise FileNotFoundError(f"Le dossier {ARTIFACTS_DIR} n'existe pas. L'entraînement a échoué ?")

    s3 = boto3.client('s3')
    
    files_count = 0
    for root, dirs, files in os.walk(ARTIFACTS_DIR):
        for file in files:
            local_path = os.path.join(root, file)
            # On calcule le chemin relatif pour S3 (ex: models/news_index/saved_model.pb)
            relative_path = os.path.relpath(local_path, ARTIFACTS_DIR)
            s3_key = relative_path.replace("\\", "/") # Compatibilité Windows/Linux
            
            print(f"Uploading: {s3_key}")
            try:
                s3.upload_file(local_path, BUCKET_NAME, s3_key)
                files_count += 1
            except Exception as e:
                print(f"ERREUR sur {s3_key}: {e}")
                raise e 

    print(f">>> Succès ! {files_count} fichiers uploadés sur {BUCKET_NAME}.")

if __name__ == "__main__":
    upload_artifacts()