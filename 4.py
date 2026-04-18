import pandas as pd
import numpy as np

INPUT_FILE = "model_ready_dataset.tsv"
SPARK_OUTPUT = "spark_ready_dataset.parquet"
FILTERED_OUTPUT = "model_training_dataset.tsv"
GENE_STATS_OUTPUT = "gene_statistics.tsv"
SELECTED_GENES_OUTPUT = "selected_genes.txt"

TOP_GENE_COUNT = 5000   # simple middle ground for ML
VAR_THRESHOLD = 0.0001  # remove only obvious noise

print("Loading dataset...")
df = pd.read_csv(INPUT_FILE, sep="\t", low_memory=False)
print("Original shape:", df.shape)

# Find patient id column
id_col = None
for c in df.columns:
    if "case_id" in c.lower():
        id_col = c
        break

if id_col is None:
    raise ValueError("No case_id column found.")

print("Patient ID column:", id_col)

# Gene and clinical columns
gene_cols = [c for c in df.columns if str(c).startswith("ENSG")]
clinical_cols = [c for c in df.columns if c not in gene_cols and c != id_col]

print("Total gene columns:", len(gene_cols))
print("Total clinical columns:", len(clinical_cols))

# Convert gene block to numeric
gene_df = df[gene_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

# Save Spark-friendly full dataset as Parquet
try:
    print("Saving Spark-ready Parquet file...")
    df.to_parquet(SPARK_OUTPUT, index=False)
    print("Saved:", SPARK_OUTPUT)
except Exception as e:
    print("Parquet save skipped:", e)

# Gene statistics
print("Computing gene statistics...")
gene_stats = pd.DataFrame({
    "gene": gene_cols,
    "mean_expression": gene_df.mean().values,
    "variance": gene_df.var().values,
    "std_dev": gene_df.std().values,
    "min": gene_df.min().values,
    "max": gene_df.max().values
})

gene_stats = gene_stats.sort_values("variance", ascending=False)
gene_stats.to_csv(GENE_STATS_OUTPUT, sep="\t", index=False)
print("Saved:", GENE_STATS_OUTPUT)

# Light filtering: remove near-zero variance genes
print("Applying light variance filter...")
kept_genes = gene_stats.loc[gene_stats["variance"] > VAR_THRESHOLD, "gene"].tolist()

print("Genes after variance filter:", len(kept_genes))

# Keep top N informative genes
selected_genes = kept_genes[:TOP_GENE_COUNT]
print("Selected genes for training:", len(selected_genes))

with open(SELECTED_GENES_OUTPUT, "w", encoding="utf-8") as f:
    for g in selected_genes:
        f.write(g + "\n")

print("Saved:", SELECTED_GENES_OUTPUT)

# Build filtered training dataframe
keep_cols = [id_col] + clinical_cols + selected_genes
filtered_df = df[keep_cols].copy()

print("Filtered dataset shape:", filtered_df.shape)

filtered_df.to_csv(FILTERED_OUTPUT, sep="\t", index=False)
print("Saved:", FILTERED_OUTPUT)

print("Done.")