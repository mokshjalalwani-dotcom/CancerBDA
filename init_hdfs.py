import os
import time
from hdfs import InsecureClient
from requests.exceptions import ConnectionError

HDFS_URL = os.environ.get("HDFS_URL", "http://localhost:9870")
CLIENT = InsecureClient(HDFS_URL, user='root')

def wait_for_hdfs(timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # simple command to check if namenode is up
            CLIENT.status("/")
            print("Successfully connected to HDFS Namenode!")
            return True
        except Exception as e:
            print(f"Waiting for HDFS to be ready... ({e})")
            time.sleep(5)
    print("HDFS connection timed out.")
    return False

def init_hdfs():
    if not wait_for_hdfs():
        return

    # Check if we are running in the api dir or the root dir
    tsv_path = "target_ready_dataset.tsv"
    if not os.path.exists(tsv_path):
        # We might be running inside another dir, let's look around
        if os.path.exists("cancerP2/target_ready_dataset.tsv"):
            tsv_path = "cancerP2/target_ready_dataset.tsv"
        elif os.path.exists("../target_ready_dataset.tsv"):
            tsv_path = "../target_ready_dataset.tsv"
        else:
            print(f"Could not find {tsv_path}. Please make sure it exists.")
            return

    hdfs_path = "/cancer_data/target_ready_dataset.tsv"
    
    # Create the cancer_data dir
    try:
        CLIENT.makedirs("/cancer_data")
        print("Created /cancer_data directory on HDFS.")
    except Exception as e:
        print(f"Error creating dir or it already exists: {e}")

    try:
        status = CLIENT.status(hdfs_path, strict=False)
        if status:
            print(f"{hdfs_path} already exists. Skipping upload.")
        else:
            print(f"Uploading {tsv_path} to {hdfs_path}...")
            CLIENT.upload(hdfs_path, tsv_path)
            print("Upload complete!")
    except Exception as e:
        print(f"Failed to upload {tsv_path} to HDFS: {e}")

if __name__ == "__main__":
    init_hdfs()
