import pandas as pd
import numpy as np

INPUT_FILE = "data/final_cancer_dataset.tsv"
OUTPUT_FILE = "model_ready_dataset.tsv"

print("Loading final dataset...")
df = pd.read_csv(INPUT_FILE, sep="\t", low_memory=False)

print("Original shape:", df.shape)

# Identify patient id column
id_col = None
for c in df.columns:
    if "case_id" in c.lower():
        id_col = c
        break

if id_col is None:
    raise ValueError("No case_id column found in dataset.")

print("Patient ID column:", id_col)

# Keep only one row per patient if duplicates exist
df = df.drop_duplicates(subset=id_col, keep="first")
print("After dropping duplicate patients:", df.shape)

# Identify gene columns
gene_cols = [c for c in df.columns if str(c).startswith("ENSG")]
print("Total gene columns:", len(gene_cols))

# Identify likely clinical columns
clinical_cols = [c for c in df.columns if c not in gene_cols and c != id_col]
print("Total clinical columns:", len(clinical_cols))

# Basic cleanup: drop columns that are completely empty
empty_cols = [c for c in df.columns if df[c].isna().all()]
if empty_cols:
    print("Dropping fully empty columns:", len(empty_cols))
    df = df.drop(columns=empty_cols)

# Fill missing values in gene columns with 0
for c in gene_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# Make a survival target if possible
target_cols = [
    "demographic.vital_status",
    "cases.days_to_death",
    "diagnoses.days_to_death",
    "diagnoses.days_to_last_follow_up",
    "cases.days_to_last_follow_up"
]

for c in target_cols:
    if c in df.columns:
        print("Found target-related column:", c)

# Create binary survivability label if vital status exists
if "demographic.vital_status" in df.columns:
    df["survival_label"] = df["demographic.vital_status"].astype(str).str.lower().map({
        "alive": 1,
        "dead": 0
    })
elif "cases.vital_status" in df.columns:
    df["survival_label"] = df["cases.vital_status"].astype(str).str.lower().map({
        "alive": 1,
        "dead": 0
    })
else:
    df["survival_label"] = np.nan

# Create a survival time column if available
if "diagnoses.days_to_death" in df.columns and "diagnoses.days_to_last_follow_up" in df.columns:
    df["survival_time"] = df["diagnoses.days_to_death"].fillna(df["diagnoses.days_to_last_follow_up"])
elif "cases.days_to_death" in df.columns and "cases.days_to_last_follow_up" in df.columns:
    df["survival_time"] = df["cases.days_to_death"].fillna(df["cases.days_to_last_follow_up"])
else:
    df["survival_time"] = np.nan

# Recurrence target
recurrence_candidates = [
    "diagnoses.progression_or_recurrence",
    "follow_ups.progression_or_recurrence",
    "diagnoses.recurrence_or_progression"
]

found_recurrence = None
for c in recurrence_candidates:
    if c in df.columns:
        found_recurrence = c
        break

if found_recurrence:
    print("Using recurrence column:", found_recurrence)
    df["recurrence_label"] = df[found_recurrence].astype(str).str.lower().map({
        "yes": 1,
        "present": 1,
        "true": 1,
        "no": 0,
        "absent": 0,
        "false": 0
    })
else:
    df["recurrence_label"] = np.nan

# Save processed dataset
df.to_csv(OUTPUT_FILE, sep="\t", index=False)

print("Saved:", OUTPUT_FILE)
print("Final shape:", df.shape)
print("Done.")