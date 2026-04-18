import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Summarizer

# Configuration
INPUT_FILE = "model_ready_dataset.tsv"
OUTPUT_PARQUET = "spark_ready_dataset.parquet"
OUTPUT_TRAIN_TSV = "model_training_dataset_spark.tsv"
VARIANCE_THRESHOLD = 0.01  # Example threshold for filtering genes
SAMPLE_FRACTION = 0.2     # Fraction for smaller training set

def main():
    # 1. Initialize Spark Session
    spark = SparkSession.builder \
        .appName("CancerPrognosisPreprocessing") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()

    print(f"Loading data from {INPUT_FILE}...")
    
    # 2. Load TSV Data
    # Assuming tab-separated and contains header
    df = spark.read.options(header='True', inferSchema='True', delimiter='\t').csv(INPUT_FILE)
    
    # Identify gene columns (usually start with ENSG)
    all_cols = df.columns
    gene_cols = [c for c in all_cols if c.startswith("ENSG")]
    clinical_cols = [c for c in all_cols if not c.startswith("ENSG")]
    
    print(f"Total columns: {len(all_cols)}")
    print(f"Gene columns identified: {len(gene_cols)}")
    print(f"Clinical columns identified: {len(clinical_cols)}")

    # 3. Clean and Transform
    # Fill NAs for gene columns with 0.0
    df = df.fillna(0.0, subset=gene_cols)
    
    # 4. Compute Gene Variance/Statistics
    print("Computing gene statistics and filtering low-variance features...")
    
    # We use VectorAssembler to group genes for efficient computation
    assembler = VectorAssembler(inputCols=gene_cols, outputCol="gene_features", handleInvalid="keep")
    gene_df = assembler.transform(df)
    
    # Compute variance using Summarizer
    stats = gene_df.select(Summarizer.metrics("variance").summary(F.col("gene_features")).alias("summary")).collect()[0].summary
    variances = stats.variance.toArray()
    
    # Identify high-variance genes
    selected_genes = [gene_cols[i] for i, var in enumerate(variances) if var > VARIANCE_THRESHOLD]
    
    print(f"Genes remaining after variance filtering (> {VARIANCE_THRESHOLD}): {len(selected_genes)}")
    
    # 5. Filter the Dataset
    final_cols = clinical_cols + selected_genes
    df_filtered = df.select(*final_cols)
    
    # 6. Save Parquet (Full processed data)
    print(f"Saving full processed data to {OUTPUT_PARQUET}...")
    df_filtered.write.mode("overwrite").parquet(OUTPUT_PARQUET)
    
    # 7. Create a smaller training dataset for scikit-learn
    # We take a sample of rows and the filtered columns
    print(f"Creating smaller training dataset (sampling {SAMPLE_FRACTION*100}% of rows)...")
    df_train = df_filtered.sample(withReplacement=False, fraction=SAMPLE_FRACTION, seed=42)
    
    # Save as TSV
    # Note: Spark's csv output creates a folder. We might want to coalesce to 1 partition for a single file.
    df_train.coalesce(1).write.mode("overwrite") \
        .options(header='True', delimiter='\t') \
        .csv("temp_spark_output")
    
    # Move the part file to the desired location (optional, but cleaner)
    # For simplicity in this script, we just notify where it is
    print(f"Sample training data saved in directory: temp_spark_output")
    print(f"Process complete.")

    spark.stop()

if __name__ == "__main__":
    main()
