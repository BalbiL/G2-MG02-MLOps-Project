import os
import zipfile
import urllib.request

def download_and_extract(output_dir="data/raw"):
    # Création du dossier cible
    os.makedirs(output_dir, exist_ok=True)
    
    # Configuration S3 Public
    bucket_name = "s3-g2mg02"
    region = "eu-west-3"  # Vérifiez que c'est la bonne région
    file_key = "data/mind_large.zip" # Chemin dans le bucket
    
    # Construction de l'URL publique S3
    url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"
    output_zip = os.path.join(output_dir, "mind_large.zip")

    # Téléchargement
    if not os.path.exists(output_zip):
        print(f"Téléchargement depuis : {url}")
        try:
            urllib.request.urlretrieve(url, output_zip)
            print("Téléchargement terminé.")
        except Exception as e:
            print(f"ERREUR : Impossible de télécharger le fichier. Vérifiez l'URL ou les droits publics.\n{e}")
            return
    else:
        print("mind_large.zip déjà présent.")

    # Extraction
    extract_path = os.path.join(output_dir, "mind_large")
    if not os.path.exists(extract_path):
        print("Extraction en cours...")
        try:
            with zipfile.ZipFile(output_zip, 'r') as z:
                z.extractall(output_dir)
            print("Extraction terminée.")
        except zipfile.BadZipFile:
            print("ERREUR : Le fichier zip semble corrompu.")
    else:
        print("Dossier mind_large déjà extrait.")

if __name__ == "__main__":
    download_and_extract()