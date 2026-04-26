# BDA Project Report - Distributed Cancer Prediction Platform (CancerP2)

## 1. Introduction
This project scales a precision oncology prediction system using Big Data Analytics (BDA) principles. By migrating to a distributed Hadoop Distributed File System (HDFS) architecture within a Dockerized environment, the system effectively handles large-scale genomic datasets. It integrates PySpark distributed machine learning pipelines with a modern React.js frontend and a FastAPI backend to deliver real-time insights, patient similarity matching, and system storage monitoring.

## 2. Architecture & Tech Stack
- **Distributed Storage Layer (HDFS):** Managed by Hadoop 3.2.1, running one NameNode and three DataNodes orchestrated via Docker Compose (`docker-compose.yml`).
- **Backend API (FastAPI):** Exposes scalable asynchronous RESTful endpoints. Interfaces with HDFS via the `hdfs` python client (WebHDFS) and utilizes Apache Spark for data processing.
- **Machine Learning Layer (PySpark):** Distributed PySpark ML pipelines (`recurrence_model_spark`, `survival_model_spark`) calculate patient survival and recurrence probabilities. It also implements an in-memory vector database using NumPy to enable millisecond real-time patient similarity searches across historical profiles.
- **Frontend (React.js):** A Vite-powered React Single Page Application (SPA) providing an intuitive patient diagnostic workflow (Step 1, Step 2, Results) and generating dynamic PDF prognosis reports.

## 3. Key BDA Implementations
### 3.1. Distributed Data Storage and Quota Management
- Leveraged a multinode Hadoop cluster within Docker for robust data distribution and replication across three DataNodes (`datanode1`, `datanode2`, `datanode3`).
- Programmatically enforced a strict 1 GB (1,073,741,824 bytes) storage quota on the `/cancer_data` HDFS path using native HDFS quota allocation commands (`hdfs dfs -setSpaceQuota`) through the `init_hdfs.py` utility script.
- Dynamically structured the HDFS filesystem with logical directories: baseline datasets (`/cancer_data/target_ready_dataset.tsv`), raw gene uploads (`/cancer_data/genes`), and time-partitioned patient outputs (`/cancer_data/new_patients/YYYY/MM/DD/`).

### 3.2. PySpark Distributed Data Processing
- Evaluated patient genomic arrays via robust Spark distributed modeling, enabling the system to evaluate datasets that scale beyond single-machine constraints.
- Optimized PySpark `SparkSession` allocations to utilize Arrow (`spark.sql.execution.arrow.pyspark.enabled`) for extreme high-speed Spark-to-Pandas DataFrame conversions.

### 3.3. Similarity Engine and Storage Dashboard
- Executed Cosine Similarity across gene expression vectors to fetch highly correlated historical cases, returning granular "Genomic Recovery Insights".
- Developed a storage-awareness pipeline where the API polls HDFS dynamically (`/hdfs/storage` endpoint) to capture real-time usage bytes, driving a React dashboard that warns end-users when approaching the enforced 1 GB threshold.

## 4. Setup Instructions & How to Run
1. **Initialize Cluster:** Launch the distributed environment by running `docker-compose up -d --build` in the root folder.
2. **Setup HDFS Quotas and Baseline Data:** Execute `docker-compose exec api python init_hdfs.py` to provision HDFS folder structures, apply the strict 1GB space quota, and upload the base genomic dataset.
3. **Frontend Access:** Navigate to `http://localhost:5173` to explore the precision oncology interface.
4. **Backend/API Access:** Access the FastAPI Swagger UI at `http://localhost:8000/docs` to test prediction logic and PySpark integrations.

## 5. Conclusion
By introducing Apache Hadoop and Apache Spark to the core application, this project successfully bridges the gap between isolated machine learning models and enterprise-grade Big Data scalability. The architecture is fully equipped to ingest, distribute, process, and analyze substantial genomic datasets, returning optimized real-time prognosis securely and reliably.
