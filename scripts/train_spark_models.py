import os
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.sql.functions import col

def main():
    print("INITIALIZING SPARK CLUSTER ML CONNECTION...")
    spark = SparkSession.builder \
        .appName("Cancer_Distributed_ML_Training") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
        
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_FILE = "hdfs://namenode:9000/cancer_data/target_ready_dataset.tsv"
    
    try:
        print(f"Loading 1TB scale dataset from {DATA_FILE}")
        df = spark.read.csv(DATA_FILE, sep="\t", header=True, inferSchema=True)
        # Fix dots in column names (Spark Catalyst fails on `.`)
        safe_cols = [c.replace(".", "_") for c in df.columns]
        df = df.toDF(*safe_cols)
        # Attempt to trigger connection
        df.head(1)
    except Exception as e:
        print(f"HDFS mapping failed. Falling back locally: {e}")
        local_file = os.path.join(base_dir, "target_ready_dataset.tsv")
        df = spark.read.csv(local_file, sep="\t", header=True, inferSchema=True)
        safe_cols = [c.replace(".", "_") for c in df.columns]
        df = df.toDF(*safe_cols)
    
    # Read gene names
    genes_file = os.path.join(base_dir, "selected_genes.txt")
    with open(genes_file, "r", encoding="utf-8") as f:
        selected_genes = [line.strip().replace(".", "_") for line in f if line.strip()]
        
    gene_cols = [c for c in selected_genes if c in df.columns]
    
    print(f"Dataset active with {len(gene_cols)} genomic targets.")
    
    # Prepare imputation list (output col names)
    imputed_cols = [c + "_imputed" for c in gene_cols]
    
    # -----------------------------
    # Build Common Pre-processing Pipeline
    # 1. Imputer (Median)
    # 2. VectorAssembler
    # 3. StandardScaler
    # -----------------------------
    imputer = Imputer(inputCols=gene_cols, outputCols=imputed_cols).setStrategy("median")
    assembler = VectorAssembler(inputCols=imputed_cols, outputCol="raw_features", handleInvalid="keep")
    scaler = StandardScaler(inputCol="raw_features", outputCol="features", withStd=True, withMean=True)
    
    
    # -----------------------------
    # SURVIVAL MODEL
    # -----------------------------
    if "survival_label" in df.columns:
        print("Training Survival Model Pipeline across DataNodes...")
        # Clean nulls
        df_surv = df.na.fill({"survival_label": 0.0})
        df_surv = df_surv.withColumn("label", col("survival_label").cast("double"))
        
        # Parallel Multi-Node RF
        rf_surv = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=100, maxDepth=10, seed=42)
        
        pipeline_surv = Pipeline(stages=[imputer, assembler, scaler, rf_surv])
        
        model_surv = pipeline_surv.fit(df_surv)
        
        save_path = os.path.join(base_dir, "survival_model_spark")
        model_surv.write().overwrite().save(save_path)
        print(f"Vast Distributed Survival Model saved successfully to {save_path}")


    # RECURRENCE MODEL
    if "recurrence_label" in df.columns:
        print("Training Recurrence Model Pipeline across DataNodes...")
        df_rec = df.na.fill({"recurrence_label": 0.0})
        df_rec = df_rec.withColumn("label", col("recurrence_label").cast("double"))
        
        rf_rec = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=100, maxDepth=10, seed=42)
        
        pipeline_rec = Pipeline(stages=[imputer, assembler, scaler, rf_rec])
        
        model_rec = pipeline_rec.fit(df_rec)
        
        save_path = os.path.join(base_dir, "recurrence_model_spark")
        model_rec.write().overwrite().save(save_path)
        print(f"Vast Distributed Recurrence Model saved successfully to {save_path}")

    print("ALL MODELS HAVE BEEN INTEGRATED INTO SPARK INFRASTRUCTURE!")
    
if __name__ == "__main__":
    main()
