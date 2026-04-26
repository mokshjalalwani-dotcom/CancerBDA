"""
init_hdfs.py — HDFS Initialization Script
==========================================
- Waits for the HDFS NameNode to be ready.
- Creates /cancer_data with a hard 1 GB space quota enforced by HDFS.
- Uploads the baseline target_ready_dataset.tsv if not already present.

Run once after `docker-compose up -d`:
    docker-compose exec api python init_hdfs.py
"""

import os
import time
import subprocess
from hdfs import InsecureClient

HDFS_URL = os.environ.get("HDFS_URL", "http://localhost:9870")
CLIENT = InsecureClient(HDFS_URL, user="root")

CANCER_DATA_DIR   = "/cancer_data"
NEW_PATIENTS_DIR  = "/cancer_data/new_patients"
GENES_DIR         = "/cancer_data/genes"

# 1 GB expressed in bytes
QUOTA_BYTES = 1 * 1024 * 1024 * 1024  # 1,073,741,824 bytes


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def wait_for_hdfs(timeout: int = 120) -> bool:
    """Poll until HDFS NameNode is reachable or timeout expires."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            CLIENT.status("/")
            print(" HDFS NameNode is ready.")
            return True
        except Exception as exc:
            print(f" Waiting for HDFS... ({exc})")
            time.sleep(5)
    print(" HDFS connection timed out.")
    return False


def ensure_dir(path: str) -> None:
    """Create an HDFS directory if it does not already exist."""
    try:
        CLIENT.makedirs(path)
        print(f" Created HDFS directory: {path}")
    except Exception as exc:
        print(f"ℹ  Directory may already exist ({path}): {exc}")


def set_space_quota(hdfs_path: str, quota_bytes: int) -> None:
    """
    Apply an HDFS space quota via the hdfs dfs -setSpaceQuota command
    executed inside the namenode container.  WebHDFS does not expose
    quota management, so we shell out to the native HDFS CLI.
    """
    quota_mb = quota_bytes // (1024 * 1024)
    print(f"🔒  Setting HDFS space quota on {hdfs_path}: {quota_mb} MB ({quota_bytes:,} bytes)")
    try:
        # Works when running inside the docker network (api container)
        result = subprocess.run(
            [
                "hdfs", "dfs",
                "-setSpaceQuota",
                str(quota_bytes),
                hdfs_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f" Quota set successfully on {hdfs_path}")
        else:
            # Fallback: attempt via docker exec namenode
            print(f"   Direct hdfs command failed, trying docker exec fallback...")
            result2 = subprocess.run(
                [
                    "docker", "exec", "namenode",
                    "hdfs", "dfs",
                    "-setSpaceQuota", str(quota_bytes), hdfs_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result2.returncode == 0:
                print(f" Quota set via docker exec: {hdfs_path}")
            else:
                print(f"  Could not set quota automatically.\n"
                      f"    Run manually:\n"
                      f"    docker exec namenode hdfs dfs -setSpaceQuota {quota_bytes} {hdfs_path}\n"
                      f"    docker exec namenode hdfs dfs -count -q {hdfs_path}")
    except FileNotFoundError:
        # 'hdfs' binary not on PATH (running on Windows host) — use docker exec
        print("ℹ  'hdfs' binary not found locally. Trying docker exec...")
        try:
            subprocess.run(
                [
                    "docker", "exec", "namenode",
                    "hdfs", "dfs",
                    "-setSpaceQuota", str(quota_bytes), hdfs_path,
                ],
                check=True,
                timeout=30,
            )
            print(f" Quota set via docker exec on {hdfs_path}")
        except Exception as e:
            print(f" docker exec quota set failed: {e}\n"
                  f"    Manual command:\n"
                  f"    docker exec namenode hdfs dfs -setSpaceQuota {quota_bytes} {hdfs_path}")


def show_quota(hdfs_path: str) -> None:
    """Print quota and usage info for the given HDFS path."""
    try:
        subprocess.run(
            ["docker", "exec", "namenode", "hdfs", "dfs", "-count", "-q", hdfs_path],
            timeout=15,
        )
    except Exception as e:
        print(f"ℹ Could not display quota info: {e}")


def upload_if_missing(local_path: str, hdfs_path: str) -> None:
    """Upload a local file to HDFS only if it does not already exist."""
    if not os.path.exists(local_path):
        print(f"⚠️   Local file not found, skipping upload: {local_path}")
        return

    try:
        status = CLIENT.status(hdfs_path, strict=False)
        if status:
            size_mb = status["length"] / (1024 * 1024)
            print(f"ℹ  File already on HDFS ({size_mb:.1f} MB): {hdfs_path}")
            return
    except Exception:
        pass  # file does not exist yet — proceed with upload

    local_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"⬆  Uploading {local_path} ({local_mb:.1f} MB) → {hdfs_path} …")
    try:
        CLIENT.upload(hdfs_path, local_path)
        print(f"Upload complete: {hdfs_path}")
    except Exception as exc:
        print(f" Upload failed: {exc}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def init_hdfs() -> None:
    if not wait_for_hdfs():
        return

    # 1. Create directory structure
    ensure_dir(CANCER_DATA_DIR)
    ensure_dir(NEW_PATIENTS_DIR)
    ensure_dir(GENES_DIR)

    # 2. Enforce 1 GB space quota on the cancer_data root
    set_space_quota(CANCER_DATA_DIR, QUOTA_BYTES)

    # 3. Upload baseline dataset
    tsv_candidates = [
        "target_ready_dataset.tsv",
        "../target_ready_dataset.tsv",
        "/app/target_ready_dataset.tsv",
    ]
    for candidate in tsv_candidates:
        if os.path.exists(candidate):
            upload_if_missing(candidate, f"{CANCER_DATA_DIR}/target_ready_dataset.tsv")
            break
    else:
        print("  target_ready_dataset.tsv not found in any expected location.")

    # 4. Show current quota status
    print("\n  Current HDFS quota status for /cancer_data:")
    show_quota(CANCER_DATA_DIR)
    print("\n  HDFS initialization complete.")
    print(f"    Space quota enforced: {QUOTA_BYTES // (1024*1024)} MB (1 GB)")
    print("    Data directories:")
    print(f"      {CANCER_DATA_DIR}/target_ready_dataset.tsv  ← baseline dataset")
    print(f"      {GENES_DIR}/                                 ← patient gene uploads")
    print(f"      {NEW_PATIENTS_DIR}/YYYY/MM/DD/               ← prediction records")


if __name__ == "__main__":
    init_hdfs()
