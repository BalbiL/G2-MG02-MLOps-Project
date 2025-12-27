import os
import gdown
import zipfile

def download_and_extract(output_dir="data/raw"):
    # Création du dossier cible
    os.makedirs(output_dir, exist_ok=True)
    
    # Lien de téléchargement du dataset MIND
    file_id = "1GffOYmcAMP17oi2BwC7Dp4l5F7rEjHRr"
    url = f"https://drive.google.com/uc?id={file_id}"
    output_zip = os.path.join(output_dir, "mind_large.zip")

    # Téléchargement
    if not os.path.exists(output_zip):
        print(f"Téléchargement de mind_large.zip...")
        gdown.download(url, output_zip, quiet=False)
    else:
        print("mind_large.zip déjà présent.")

    # Extraction
    # On vérifie si le dossier extrait existe déjà
    extract_path = os.path.join(output_dir, "mind_large")
    if not os.path.exists(extract_path):
        print("Extraction en cours...")
        with zipfile.ZipFile(output_zip, 'r') as z:
            z.extractall(output_dir)
        print("Extraction terminée.")
    else:
        print("Dossier mind_large déjà extrait.")

if __name__ == "__main__":
    download_and_extract()