"""
generate_gene_data_hdfs.py
==========================
Generates ~1 GB of synthetic patient gene-expression records and uploads
them in batch chunks directly into HDFS under /cancer_data/genes/

Each chunk is a TSV file:
  /cancer_data/genes/batch_0001.tsv
  /cancer_data/genes/batch_0002.tsv
  …

Run inside the docker network:
    docker-compose exec api python generate_gene_data_hdfs.py

Or on your host machine (HDFS_URL defaults to localhost:9870):
    python generate_gene_data_hdfs.py
"""

import os
import io
import time
import numpy as np
import pandas as pd
from hdfs import InsecureClient

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
HDFS_URL        = os.environ.get("HDFS_URL", "http://localhost:9870")
GENES_HDFS_DIR  = "/cancer_data/genes"
TARGET_BYTES    = 1 * 1024 * 1024 * 1024      # 1 GB hard cap
CHUNK_ROWS      = 500                          # rows per batch file
N_GENES         = 200                          # gene expression columns per patient

CLIENT = InsecureClient(HDFS_URL, user="root")


# ─────────────────────────────────────────────
# Gene ID list (ENSG-style identifiers)
# ─────────────────────────────────────────────
def gene_ids(n: int):
    """Generate n synthetic ENSG gene IDs."""
    rng = np.random.default_rng(seed=42)
    ids = [f"ENSG{rng.integers(10_000_000, 99_999_999):08d}.{rng.integers(1,9)}" for _ in range(n)]
    return ids


GENE_COLUMNS = gene_ids(N_GENES)


# ─────────────────────────────────────────────
# Synthetic row generation
# ─────────────────────────────────────────────
def generate_batch(n_rows: int, batch_index: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Produce n_rows of synthetic patient gene-expression data.
    Mimics realistic log-normalised RNA-seq values (mostly 0-15 range).
    """
    # Case IDs in the form TCGA-XX-XXXX-01
    hex_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    case_ids = [
        f"TCGA-{''.join(rng.choice(list(hex_chars), 2))}-"
        f"{''.join(rng.choice(list(hex_chars), 4))}-"
        f"0{rng.integers(1, 3)}"
        for _ in range(n_rows)
    ]

    # Gene expression matrix: log-normal distribution (typical for RNA-seq)
    expr_matrix = rng.lognormal(mean=2.0, sigma=1.5, size=(n_rows, N_GENES)).round(4)

    # Sparse dropout – real RNA-seq data has ~25% zero reads
    dropout_mask = rng.random((n_rows, N_GENES)) < 0.25
    expr_matrix[dropout_mask] = 0.0

    # Clinical labels
    survival_label   = rng.integers(0, 2, size=n_rows)          # 0=alive, 1=deceased
    recurrence_label = rng.integers(0, 2, size=n_rows)          # 0=no, 1=yes
    high_risk_flag   = ((survival_label + recurrence_label) > 1).astype(int)
    tumor_stage      = rng.choice(["I", "II", "III", "IV"], size=n_rows, p=[0.2, 0.35, 0.3, 0.15])
    age              = rng.integers(25, 85, size=n_rows)
    batch_id         = np.full(n_rows, batch_index, dtype=int)

    df = pd.DataFrame(expr_matrix, columns=GENE_COLUMNS)
    df.insert(0, "case_id",          case_ids)
    df.insert(1, "batch_id",         batch_id)
    df.insert(2, "age",              age)
    df.insert(3, "tumor_stage",      tumor_stage)
    df.insert(4, "survival_label",   survival_label)
    df.insert(5, "recurrence_label", recurrence_label)
    df.insert(6, "high_risk_flag",   high_risk_flag)

    return df


# ─────────────────────────────────────────────
# HDFS helpers
# ─────────────────────────────────────────────
def wait_for_hdfs(timeout: int = 120) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            CLIENT.status("/")
            print("✅  HDFS NameNode is ready.")
            return True
        except Exception as exc:
            print(f"⏳  Waiting for HDFS... ({exc})")
            time.sleep(5)
    print("❌  HDFS connection timed out.")
    return False


def hdfs_used_bytes(path: str) -> int:
    """Return the total bytes used under an HDFS path (content summary)."""
    try:
        summary = CLIENT.content(path)
        return summary.get("length", 0)
    except Exception:
        return 0


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main() -> None:
    if not wait_for_hdfs():
        return

    # Ensure directory exists
    try:
        CLIENT.makedirs(GENES_HDFS_DIR)
    except Exception:
        pass

    rng            = np.random.default_rng(seed=1337)
    batch_index    = 1
    total_uploaded = hdfs_used_bytes(GENES_HDFS_DIR)

    print(f"\n🧬  Starting gene data generation → {GENES_HDFS_DIR}")
    print(f"    Target size : {TARGET_BYTES // (1024*1024)} MB (1 GB)")
    print(f"    Rows/batch  : {CHUNK_ROWS}")
    print(f"    Gene columns: {N_GENES}")
    print(f"    Already in HDFS: {total_uploaded / (1024*1024):.1f} MB\n")

    while total_uploaded < TARGET_BYTES:
        df      = generate_batch(CHUNK_ROWS, batch_index, rng)
        buf     = io.BytesIO()
        df.to_csv(buf, sep="\t", index=False)
        buf.seek(0)
        chunk_bytes = len(buf.getvalue())

        hdfs_path = f"{GENES_HDFS_DIR}/batch_{batch_index:04d}.tsv"

        # Skip if this batch already uploaded (resume support)
        if CLIENT.status(hdfs_path, strict=False):
            print(f"  ⏭️  Skipping existing batch: {hdfs_path}")
            batch_index += 1
            continue

        # Check if adding this chunk would exceed the quota
        if total_uploaded + chunk_bytes > TARGET_BYTES:
            # Write a partial final batch to fill exactly to quota
            remaining = TARGET_BYTES - total_uploaded
            rows_fit  = max(1, int(CHUNK_ROWS * remaining / chunk_bytes))
            df = df.head(rows_fit)
            buf = io.BytesIO()
            df.to_csv(buf, sep="\t", index=False)
            buf.seek(0)
            chunk_bytes = len(buf.getvalue())

        try:
            with CLIENT.write(hdfs_path, overwrite=False) as writer:
                writer.write(buf.read())
        except Exception as exc:
            print(f"  ❌  Failed to write {hdfs_path}: {exc}")
            break

        total_uploaded += chunk_bytes
        pct = total_uploaded / TARGET_BYTES * 100
        print(f"  ✅  Batch {batch_index:04d} → {hdfs_path}  "
              f"| {chunk_bytes / 1024:.0f} KB  "
              f"| Total: {total_uploaded / (1024*1024):.1f} MB / 1024 MB ({pct:.1f}%)")

        if total_uploaded >= TARGET_BYTES:
            print("\n🎯  Reached 1 GB storage quota!")
            break

        batch_index += 1

    print(f"\n✅  Gene data generation complete.")
    print(f"    Total uploaded : {total_uploaded / (1024*1024):.2f} MB")
    print(f"    Total batches  : {batch_index}")
    print(f"    HDFS location  : {GENES_HDFS_DIR}/")


if __name__ == "__main__":
    main()
