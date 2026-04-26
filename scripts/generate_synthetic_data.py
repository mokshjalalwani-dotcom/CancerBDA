import pandas as pd
import numpy as np
import uuid
import os

input_file = r"b:\desktop\Projects\cancerP2\clinical_master.tsv"
output_file = r"b:\desktop\Projects\cancerP2\data\synthetic_clinical_master.tsv"

def generate_synthetic_data(input_path, output_path, duplicate_count=1):
    print("Loading data...")
    # Load all strings initially to safely replace missing markers
    df = pd.read_csv(input_path, sep='\t', low_memory=False, dtype=str)
    
    # Store original column names
    cols = df.columns.tolist()
    
    # Replace known null equivalents with actual NaNs temporarily
    # Looking at the sample, missing data is primarily represented as "'--"
    # but we additionally handle common forms
    df.replace(["'--", "--", "Not Reported", "Unknown", "unknown"], np.nan, inplace=True)
    
    numeric_cols = []
    categorical_cols = []
    
    for c in cols:
        # Avoid perturbing IDs structurally
        if c.endswith('_id'):
            continue
            
        # Try to convert non-null to float
        non_nulls = df[c].dropna()
        if len(non_nulls) == 0:
            categorical_cols.append(c)
            continue
            
        try:
            pd.to_numeric(non_nulls)
            numeric_cols.append(c)
        except ValueError:
            categorical_cols.append(c)
            
    # Sample rows with replacement (bootstrapping)
    print(f"Sampling {len(df) * duplicate_count} synthetic rows based on {len(df)} original rows...")
    synthetic_df = df.sample(n=len(df) * duplicate_count, replace=True).reset_index(drop=True)
    
    print("Perturbing categorical columns...")
    for c in categorical_cols:
        non_null_vals = df[c].dropna().unique()
        if len(non_null_vals) > 1:
            # 5% mutation
            mask = np.random.rand(len(synthetic_df)) < 0.05
            # We don't overwrite NaNs to keep data sparsity similar
            valid_mask = synthetic_df[c].notna() & mask
            # For the intersection, apply mutation
            indices_to_mutate = synthetic_df[valid_mask].index
            if len(indices_to_mutate) > 0:
                synthetic_df.loc[indices_to_mutate, c] = np.random.choice(non_null_vals, size=len(indices_to_mutate))

    print("Perturbing numeric columns...")
    for c in numeric_cols:
        # Convert synthetic_df column to numeric to apply math
        numeric_series = pd.to_numeric(synthetic_df[c], errors='coerce')
        std = numeric_series.std()
        if pd.notna(std) and std > 0:
            noise = np.random.normal(0, 0.05 * std, size=len(numeric_series))
            # Apply Noise to non-nans only
            non_nan_mask = numeric_series.notna()
            
            # Use original df to see if it is pure integer form
            is_int = df[c].dropna().str.match(r'^-?\d+$').all()
            new_series = numeric_series.copy()
            new_series[non_nan_mask] += noise[non_nan_mask]
            
            if is_int:
                new_series = np.round(new_series)
            
            # Avoid negative bounds if origin never had negatives
            orig_min = pd.to_numeric(df[c].dropna(), errors='coerce').min()
            if pd.notna(orig_min) and orig_min >= 0:
                new_series = new_series.clip(lower=0)
                
            synthetic_df[c] = new_series.astype(str)
            # Revert what was nan
            synthetic_df.loc[~non_nan_mask, c] = np.nan
        else:
            # if standard deviation is 0 or NaN, keep as is
            pass

    print("Generating fresh UUIDs for ID fields...")
    for c in cols:
        if c.endswith('_id'):
            synthetic_df[c] = [str(uuid.uuid4()) for _ in range(len(synthetic_df))]
            
    # Put back the original missing value marker for NaNs and literal "nan"s
    synthetic_df.replace('nan', np.nan, inplace=True)
    synthetic_df.fillna("'--", inplace=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Writing synthetic data to {output_path}...")
    synthetic_df.to_csv(output_path, sep='\t', index=False)
    
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    synthetic_size = os.path.getsize(output_path) / (1024 * 1024)
    
    print("Done!")
    print(f"Original File Size: {original_size:.2f} MB")
    print(f"Synthetic File Size: {synthetic_size:.2f} MB")

if __name__ == "__main__":
    generate_synthetic_data(input_file, output_file)
