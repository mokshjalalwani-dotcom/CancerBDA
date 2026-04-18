import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import joblib

INPUT_FILE = "target_ready_dataset.tsv"

print("Loading dataset...")
df = pd.read_csv(INPUT_FILE, sep="\t", low_memory=False)
print("Shape:", df.shape)

# find patient id
id_col = [c for c in df.columns if "case_id" in c.lower()][0]

# gene columns
gene_cols = [c for c in df.columns if c.startswith("ENSG")]

print("Total genes:", len(gene_cols))

# Keep raw X for pipeline; don't fillna(0) globally
X = df[gene_cols].apply(pd.to_numeric, errors="coerce")

print("Feature matrix:", X.shape)

# Define robust preprocessing steps
# 1. Impute missing values with median (better for biological data than mean/0)
# 2. Scale using RobustScaler (resilient to extreme gene expression outliers)
preprocessor = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', RobustScaler())
])

# Define grid for RF optimization to maintain/improve accuracy
param_grid = {
    'classifier__n_estimators': [100, 200],
    'classifier__max_depth': [10, 20, None],
    'classifier__min_samples_leaf': [1, 2, 4]
}

if "survival_label" in df.columns:
    
    # Fill missing survival labels with 0 to maintain binary classification
    y_surv = df["survival_label"].fillna(0)
    X_surv = X.copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X_surv, y_surv, test_size=0.2, random_state=42, stratify=y_surv
    )

    print("\nTraining Survival Model (with CV Tuning)...")
    
    surv_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_jobs=-1, random_state=42))
    ])

    surv_search = GridSearchCV(surv_pipeline, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    surv_search.fit(X_train, y_train)

    best_surv_model = surv_search.best_estimator_
    acc = best_surv_model.score(X_test, y_test)

    print("Survival Model Best Params:", surv_search.best_params_)
    print("Survival Model Accuracy:", acc)

    joblib.dump(best_surv_model, "survival_model.pkl")

# ==========================
# RECURRENCE MODEL
# ==========================

if "recurrence_label" in df.columns:

    # Fill missing recurrence labels with 0 to maintain binary classification
    y_rec = df["recurrence_label"].fillna(0)
    X_rec = X.copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X_rec, y_rec, test_size=0.2, random_state=42, stratify=y_rec
    )

    print("\nTraining Recurrence Model (with CV Tuning)...")

    rec_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_jobs=-1, random_state=42))
    ])

    rec_search = GridSearchCV(rec_pipeline, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    rec_search.fit(X_train, y_train)

    best_rec_model = rec_search.best_estimator_
    acc = best_rec_model.score(X_test, y_test)

    print("Recurrence Model Best Params:", rec_search.best_params_)
    print("Recurrence Model Accuracy:", acc)

    joblib.dump(best_rec_model, "recurrence_model.pkl")

# ==========================
# PATIENT SIMILARITY ENGINE
# ==========================

print("\nBuilding Similarity Engine...")

# Refit preprocessor on the entire dataset for similarity search
preprocessor.fit(X)
X_scaled = preprocessor.transform(X)

knn = NearestNeighbors(
    n_neighbors=5,
    metric="cosine"
)

knn.fit(X_scaled)

joblib.dump(knn, "patient_similarity_model.pkl")
# Instead of just the scaler, we dump the whole preprocessor pipeline
joblib.dump(preprocessor, "scaler.pkl") 

# save patient ids for lookup
df[[id_col]].to_csv("patient_ids.tsv", sep="\t", index=False)

print("\nModels saved successfully.")
print("- survival_model.pkl (Pipeline: Imputer + Scaler + RF)")
print("- recurrence_model.pkl (Pipeline: Imputer + Scaler + RF)")
print("- patient_similarity_model.pkl")
print("- scaler.pkl (Now contains the full preprocessing Pipeline)")