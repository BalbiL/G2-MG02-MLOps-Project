import os
import boto3

# Configuration du bucket pour upload
BUCKET_NAME = "s3-g2mg02"  
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
            
            # Calcul du chemin relatif 
            relative_path = os.path.relpath(local_path, ARTIFACTS_DIR)
            s3_key = relative_path.replace("\\", "/") # Compatibilité Windows/Linux
            
            # Si le fichier est dans le dossier 'models', on ajoute le préfixe en double (necessaire pour le chargement dans new_inference)
            if s3_key.startswith("models/"):
                s3_key = f"models/{s3_key}"
            

            print(f"Uploading: {local_path} -> s3://{BUCKET_NAME}/{s3_key}")
            try:
                s3.upload_file(local_path, BUCKET_NAME, s3_key)
                files_count += 1
            except Exception as e:
                print(f"ERREUR sur {s3_key}: {e}")
                raise e 

    print(f">>> Succès khey! {files_count} fichiers uploadés sur {BUCKET_NAME}.")

if __name__ == "__main__":
    upload_artifacts()