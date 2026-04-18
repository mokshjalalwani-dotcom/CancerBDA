import pandas as pd
import numpy as np

INPUT_FILE = "model_training_dataset.tsv"
OUTPUT_FILE = "target_ready_dataset.tsv"

print("Loading training dataset...")
df = pd.read_csv(INPUT_FILE, sep="\t", low_memory=False)
print("Original shape:", df.shape)

# find patient id column
id_col = None
for c in df.columns:
    if "case_id" in c.lower():
        id_col = c
        break

if id_col is None:
    raise ValueError("No case_id column found.")

print("Patient ID column:", id_col)

# helper to find first matching column
def find_col(options, columns):
    for col in options:
        if col in columns:
            return col
    return None

cols = df.columns

# survival label
survival_col = find_col(
    ["demographic.vital_status", "cases.vital_status", "vital_status"],
    cols
)

if survival_col:
    print("Using survival column:", survival_col)
    df["survival_label"] = (
        df[survival_col]
        .astype(str)
        .str.lower()
        .map({"alive": 1, "dead": 0})
    )
else:
    print("No survival status column found.")
    df["survival_label"] = np.nan

# survival time
death_col = find_col(
    ["diagnoses.days_to_death", "cases.days_to_death"],
    cols
)
follow_col = find_col(
    ["diagnoses.days_to_last_follow_up", "cases.days_to_last_follow_up"],
    cols
)

if death_col and follow_col:
    print("Using survival time columns:", death_col, follow_col)
    df["survival_time"] = pd.to_numeric(df[death_col], errors="coerce").fillna(
        pd.to_numeric(df[follow_col], errors="coerce")
    )
else:
    print("No survival time columns found.")
    df["survival_time"] = np.nan

# recurrence label
recurrence_col = find_col(
    [
        "diagnoses.progression_or_recurrence",
        "follow_ups.progression_or_recurrence",
        "recurrence_label"
    ],
    cols
)

if recurrence_col:
    print("Using recurrence column:", recurrence_col)
    df["recurrence_label"] = (
        df[recurrence_col]
        .astype(str)
        .str.lower()
        .map({"yes": 1, "present": 1, "true": 1, "no": 0, "absent": 0, "false": 0})
    )
else:
    print("No recurrence column found.")
    df["recurrence_label"] = np.nan

# stage / aggressiveness proxy
stage_col = find_col(
    [
        "diagnoses.ajcc_pathologic_stage",
        "diagnoses.ajcc_clinical_stage",
        "diagnoses.uicc_pathologic_stage",
        "diagnoses.uicc_clinical_stage",
        "diagnoses.tumor_stage"
    ],
    cols
)

if stage_col:
    print("Using stage column:", stage_col)
    stage_text = df[stage_col].astype(str).str.lower()

    # simple aggressiveness score proxy
    # low stage -> low score, advanced stage -> high score
    def stage_to_score(x):
        if "stage i" in x or "stage 1" in x:
            return 1
        if "stage ii" in x or "stage 2" in x:
            return 2
        if "stage iii" in x or "stage 3" in x:
            return 3
        if "stage iv" in x or "stage 4" in x:
            return 4
        return np.nan

    df["aggressiveness_label"] = stage_text.apply(stage_to_score)

    # boost aggressiveness if recurrence exists
    if "recurrence_label" in df.columns:
        df["aggressiveness_label"] = df["aggressiveness_label"] + df["recurrence_label"].fillna(0) * 0.5
else:
    print("No stage column found.")
    df["aggressiveness_label"] = np.nan

# create an easy binary high-risk flag
# high-risk = stage 3/4 or recurrence yes or survival dead
df["high_risk_flag"] = np.where(
    (df["aggressiveness_label"] >= 3) | (df["recurrence_label"] == 1) | (df["survival_label"] == 0),
    1,
    0
)

# clean duplicate patients if any
df = df.drop_duplicates(subset=id_col, keep="first")
print("After dropping duplicates:", df.shape)

# save
df.to_csv(OUTPUT_FILE, sep="\t", index=False)
print("Saved:", OUTPUT_FILE)

print("\nAvailable target columns:")
for c in ["survival_label", "survival_time", "recurrence_label", "aggressiveness_label", "high_risk_flag"]:
    if c in df.columns:
        print("-", c)