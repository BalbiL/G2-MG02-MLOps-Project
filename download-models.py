import os
import urllib.request
import xml.etree.ElementTree as ET

# Configuration
BUCKET_NAME = "s3-g2mg02"
BUCKET_REGION = "eu-west-3"
BUCKET_ROOT_URL = f"https://{BUCKET_NAME}.s3.{BUCKET_REGION}.amazonaws.com"

# --- MAPPING CONFIGURATION ---

SYNC_MAPPING = {
    "embeddings/": "ml",
 
    "models/": "ml"

}

# XML Namespaces for S3 parsing
NS = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}

def list_s3_files(prefix):
    """
    Retrieves the list of files starting with 'prefix' via the S3 XML API.
    """
    url = f"{BUCKET_ROOT_URL}?list-type=2&prefix={prefix}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            xml_content = response.read()
            
        root = ET.fromstring(xml_content)
        
        # Check for pagination
        if root.find('s3:IsTruncated', NS).text == 'true':
            print("Warning: Pagination detected (>1000 files). Some files might be missing.")

        keys = []
        for content in root.findall('s3:Contents', NS):
            key = content.find('s3:Key', NS).text
            if not key.endswith('/'): # Ignore empty folder keys
                keys.append(key)
        return keys

    except Exception as e:
        print(f"Error listing {prefix}: {e}")
        return []

def download_files():
    print(f"Starting synchronization from {BUCKET_NAME}...\n")

    for s3_prefix, local_base_folder in SYNC_MAPPING.items():
        files = list_s3_files(s3_prefix)
        
        if not files:
            print(f"No files found for S3 folder '{s3_prefix}'\n")
            continue
            
        print(f"Processing '{s3_prefix}' -> to local '{local_base_folder}/{s3_prefix}...'")
        
        for s3_key in files:
            # Path construction: local_base + s3 key
            local_path = os.path.join(local_base_folder, s3_key)
            
            # Download URL
            file_url = f"{BUCKET_ROOT_URL}/{s3_key}"
            
            # Create parent directories
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            if not os.path.exists(local_path):
                print(f"   Downloading: {s3_key}")
                try:
                    urllib.request.urlretrieve(file_url, local_path)
                except Exception as e:
                    print(f"   Error on {s3_key}: {e}")
            else:
                pass # File already exists
        print("")

    print("Configuration completed.")
    
    # Final check of the requested structure
    if os.path.exists("ml/models/models/news_index"):
        print("Structure validated: ml/models/models/news_index exists.")
    else:
        print("Warning: The structure ml/models/models/news_index was not found.")

if __name__ == "__main__":
    download_files()