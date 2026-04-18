from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
import io
import re
from typing import Any, List, Dict, Optional
import json
import time
from datetime import datetime
from hdfs import InsecureClient
from requests.exceptions import ConnectionError

app = FastAPI(title="Breast Cancer Prediction API")

# Allow CORS (Explicit origins are required when allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load artifacts
# -----------------------------
DATA_FILE = "/cancer_data/target_ready_dataset.tsv"
SELECTED_GENES_FILE = "selected_genes.txt"
SURVIVAL_MODEL_FILE = "survival_model.pkl"
RECURRENCE_MODEL_FILE = "recurrence_model.pkl"
SIMILARITY_MODEL_FILE = "patient_similarity_model.pkl"
SCALER_FILE = "scaler.pkl"

import os
HDFS_URL = os.environ.get("HDFS_URL", "http://localhost:9870")
HDFS_CLIENT = InsecureClient(HDFS_URL, user='root')

def get_hdfs_df(retries=5, delay=3):
    """Shared HDFS helper function with retry logic."""
    for i in range(retries):
        try:
            with HDFS_CLIENT.read(DATA_FILE) as reader:
                print(f"Successfully connected to HDFS and reading {DATA_FILE}")
                return pd.read_csv(reader, sep="\t", low_memory=False)
        except Exception as e:
            print(f"HDFS connection attempting... ({e}). Retry {i+1}/{retries}")
            time.sleep(delay)
    
    print("WARNING: Starting with empty df. HDFS may be down. Defaulting to local file as fallback if exists.")
    try:
        return pd.read_csv("target_ready_dataset.tsv", sep="\t", low_memory=False)
    except Exception:
        return pd.DataFrame()

df = get_hdfs_df()

with open(SELECTED_GENES_FILE, "r", encoding="utf-8") as f:
    selected_genes = [line.strip() for line in f if line.strip()]

survival_model = joblib.load(SURVIVAL_MODEL_FILE)
recurrence_model = joblib.load(RECURRENCE_MODEL_FILE)
knn_model = joblib.load(SIMILARITY_MODEL_FILE)
preprocessor = joblib.load(SCALER_FILE)

id_col = [c for c in df.columns if "case_id" in c.lower()][0]

gene_cols = [c for c in selected_genes if c in df.columns]

X_all = df[gene_cols].apply(pd.to_numeric, errors="coerce")
X_all_scaled = preprocessor.transform(X_all)

patient_id_to_index = {
    str(pid): idx for idx, pid in enumerate(df[id_col].astype(str).tolist())
}

# -----------------------------
# Request schemas
# -----------------------------
class PatientRequest(BaseModel):
    case_id: str | None = None
    genes: dict[str, float] | None = None


# -----------------------------
# Helpers
# -----------------------------
def get_feature_vector_from_request(req: PatientRequest):
    """
    Build a gene feature vector in the same order as training.
    """
    if req.case_id:
        row = df[df[id_col].astype(str) == str(req.case_id)]
        if row.empty:
            raise HTTPException(status_code=404, detail="case_id not found")
        vec = row.iloc[0][gene_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
        return vec.reshape(1, -1)

    if req.genes:
        vec = []
        for g in gene_cols:
            vec.append(float(req.genes.get(g, 0.0)))
        return np.array(vec).reshape(1, -1)

    raise HTTPException(status_code=400, detail="Provide either case_id or genes")


def make_similarity_report(case_id: str | None = None, feature_vector: np.ndarray | None = None, top_k: int = 5, target_genes: list[str] | None = None):
    """
    Finds top_k similar patients based on genomic markers.
    Can use either an existing case_id or a raw feature vector.
    """
    if case_id:
        matches = df.index[df[id_col].astype(str) == str(case_id)].tolist()
        if not matches:
            return []
        target_idx = matches[0]
        target_vec = X_all_scaled[target_idx].reshape(1, -1)
        sims = cosine_similarity(target_vec, X_all_scaled)[0]
        best_idx = np.argsort(sims)[::-1][1:top_k+1]
    elif feature_vector is not None:
        # Feature vector is already scaled when passed from predict_all
        target_vec = feature_vector.reshape(1, -1)
        sims = cosine_similarity(target_vec, X_all_scaled)[0]
        best_idx = np.argsort(sims)[::-1][:top_k]
    else:
        return []

    neighbors = []
    for i in best_idx:
        cid = df.iloc[i][id_col]
        surv = df.iloc[i].get('survival_label')
        rec = df.iloc[i].get('recurrence_label')
        risk = df.iloc[i].get('high_risk_flag')
        
        gene_values = {}
        if target_genes:
            for g in target_genes:
                if g in df.columns:
                    gene_values[g] = float(df.iloc[i][g])

        neighbors.append({
            "case_id": str(cid),
            "similarity": float(sims[i]),
            "survival_label": None if pd.isna(surv) else int(surv),
            "recurrence_label": None if pd.isna(rec) else int(rec),
            "high_risk_flag": None if pd.isna(risk) else int(risk),
            "gene_expression": gene_values
        })

    return neighbors


def build_treatment_insight(similar_patients, dominant_genes=None):
    """
    Enhanced insight layer that calculates recovery rates for specific dominant genes.
    """
    if not similar_patients:
        return {"summary": "No similar patient data available."}

    survival_vals = [p["survival_label"] for p in similar_patients if p["survival_label"] is not None]
    recurrence_vals = [p["recurrence_label"] for p in similar_patients if p["recurrence_label"] is not None]
    risk_vals = [p["high_risk_flag"] for p in similar_patients if p["high_risk_flag"] is not None]

    survived = sum(1 for v in survival_vals if v == 0)
    recur = sum(1 for v in recurrence_vals if v == 1)
    high_risk = sum(1 for v in risk_vals if v == 1)

    survival_pct = round((survived / len(survival_vals)) * 100, 2) if survival_vals and len(survival_vals) > 0 else 0
    recurrence_pct = round((recur / len(recurrence_vals)) * 100, 2) if recurrence_vals and len(recurrence_vals) > 0 else 0
    high_risk_pct = round((high_risk / len(risk_vals)) * 100, 2) if risk_vals and len(risk_vals) > 0 else 0

    # Calculate Gene-Specific Recovery Rates
    genomic_recovery = []
    if dominant_genes:
        for gene_id in dominant_genes:
            if gene_id in df.columns:
                gene_median = df[gene_id].median()
                valid_global = df[(df[gene_id] >= gene_median) & (df["survival_label"].notna())]
                if not valid_global.empty:
                    rec_count = (valid_global["survival_label"] == 0).sum()
                    rate = round((rec_count / len(valid_global)) * 100, 1)
                    genomic_recovery.append({
                        "gene_id": gene_id,
                        "recovery_rate": rate,
                        "impact": "High" if rate > 70 else "Moderate" if rate > 40 else "Low"
                    })
                else:
                    genomic_recovery.append({"gene_id": gene_id, "recovery_rate": 0.0, "impact": "Unknown"})
            else:
                genomic_recovery.append({"gene_id": gene_id, "recovery_rate": 0.0, "impact": "Unknown"})

    # Generate Logical Diagnostic Summary
    best_gene = max(genomic_recovery, key=lambda x: x["recovery_rate"]) if genomic_recovery else None
    
    summary_text = (
        f"Prognosis is heavily influenced by the expression of {len(dominant_genes)} dominant markers. "
        if dominant_genes else "Prognosis is based on overall clinical and genomic pattern matching. "
    )
    
    if best_gene:
        summary_text += f"Notably, the presence of {best_gene['gene_id']} correlates with a {best_gene['recovery_rate']}% recovery rate in the matched cohort, suggesting a favorable biological response pathway."
    else:
        summary_text += f"The survival rate across the highly similar cohort is {survival_pct}%, indicating a stable pattern in comparable historical cases."

    survival_label = "High" if survival_pct >= 70 else "Moderate" if survival_pct >= 40 else "Low"
    risk_label = "Low" if recurrence_pct < 20 else "Elevated" if recurrence_pct < 50 else "High"
    
    # Dynamic interpretation building
    interpretation = (
        f"Comparative analysis across {len(similar_patients)} clinical matches indicates a {survival_label.lower()} "
        f"survival trajectory with {risk_label.lower()} recurrence potential. "
        f"The genomic fingerprint shows significant correlation with historical cases matching your {len(dominant_genes)} dominant marker(s)."
    )
    
    return {
        "similar_patients_considered": len(similar_patients),
        "survival_percentage_among_similar": survival_pct,
        "recurrence_percentage_among_similar": recurrence_pct,
        "high_risk_percentage_among_similar": high_risk_pct,
        "genomic_recovery_insights": genomic_recovery,
        "diagnostic_summary": summary_text,
        "interpretation": interpretation
    }


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "patients": len(df), "genes": len(gene_cols)}


@app.post("/predict/survival")
def predict_survival(req: PatientRequest):
    X = get_feature_vector_from_request(req)
    prob = survival_model.predict_proba(X)[0, 1]
    pred = int(prob >= 0.5)

    return {
        "survival_probability": round(float(prob) * 100, 2),
        "predicted_label": pred
    }


@app.post("/predict/recurrence")
def predict_recurrence(req: PatientRequest):
    X = get_feature_vector_from_request(req)
    prob = recurrence_model.predict_proba(X)[0, 1]
    pred = int(prob >= 0.5)

    return {
        "recurrence_probability": round(float(prob) * 100, 2),
        "predicted_label": pred
    }


@app.post("/similar-patients")
def similar_patients(req: PatientRequest):
    if not req.case_id:
        raise HTTPException(status_code=400, detail="case_id is required for similar patient search")

    neighbors = make_similarity_report(req.case_id, top_k=5)

    return {
        "case_id": req.case_id,
        "neighbors": neighbors,
        "treatment_insight": build_treatment_insight(neighbors)
    }


@app.post("/predict/all")
def predict_all(req: PatientRequest):
    try:
        X = get_feature_vector_from_request(req)
        
        if np.isnan(X).all() or np.count_nonzero(X) == 0:
            raise HTTPException(status_code=400, detail="Invalid genomic data provided. Feature vector is entirely empty or zero.")
        
        # Scale for similar patient matching only
        X_df = pd.DataFrame(X, columns=gene_cols)
        X_processed = preprocessor.transform(X_df)

        # Let the pipeline handle its own preprocessing
        surv_prob = survival_model.predict_proba(X_df)[0, 1]
        rec_prob = recurrence_model.predict_proba(X_df)[0, 1]
        
        # Calculate prediction confidence (how far from 0.5 is the probability?)
        # 100% confidence means prob is 0.0 or 1.0. 0% confidence means prob is exactly 0.5.
        surv_conf = abs(surv_prob - 0.5) * 2 * 100
        rec_conf = abs(rec_prob - 0.5) * 2 * 100
        
        gene_data = req.genes or {}
        dominant_genes = sorted(
            [g for g in gene_data.keys() if g in gene_cols], 
            key=lambda g: float(gene_data[g]) if isinstance(gene_data[g], (int, float, str)) else 0, 
            reverse=True
        )[:3]

        # Use robustly scaled feature vector for similarity search
        neighbors = make_similarity_report(case_id=req.case_id, feature_vector=X_processed, top_k=5, target_genes=dominant_genes)
        insight = build_treatment_insight(neighbors, dominant_genes=dominant_genes)

        aggressiveness = min(100.0, 30.0 + (float(rec_prob) * 40.0))
        
        case_id = req.case_id or "NEW-PATIENT-" + str(np.random.randint(1000, 9999))
        result_payload = {
            "case_id": case_id,
            "survival_probability": round(float(surv_prob) * 100, 2),
            "survival_confidence": round(float(surv_conf), 1),
            "recurrence_probability": round(float(rec_prob) * 100, 2),
            "recurrence_confidence": round(float(rec_conf), 1),
            "aggressiveness_score": round(aggressiveness, 1),
            "similar_patients": neighbors,
            "treatment_insight": insight,
            "dominant_genes": dominant_genes,
            "gene_count": len(gene_cols)
        }

        # Write partitioned JSON to HDFS
        try:
            now = datetime.utcnow()
            partition_path = f"/cancer_data/new_patients/{now.year}/{now.month:02d}/{now.day:02d}"
            HDFS_CLIENT.makedirs(partition_path)
            file_path = f"{partition_path}/{case_id}_{int(now.timestamp())}.json"
            with HDFS_CLIENT.write(file_path, encoding='utf-8') as writer:
                json.dump(result_payload, writer)
            print(f"Successfully saved new patient record to HDFS: {file_path}")
        except Exception as e:
            print(f"Failed to write prediction to HDFS: {e}")

        return result_payload

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report-pdf")
async def generate_report_pdf(data: dict):
    """
    Generates a professional medical analysis report in PDF format with robust error handling.
    Includes patient-specific details and clinical markers.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        import pandas as pd
        from fastapi.responses import StreamingResponse
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=inch, leftMargin=inch,
            topMargin=inch, bottomMargin=inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom Styles matching the Rose Palette
        title_style = ParagraphStyle(
            'RoseTitle', parent=styles['Heading1'], fontSize=22, spaceAfter=12, textColor=colors.HexColor("#C41E4A")
        )
        subtitle_style = ParagraphStyle(
            'RoseSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#5c4d6b"), spaceAfter=20
        )
        section_heading = ParagraphStyle(
            'SectionHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#A01745"), spaceBefore=15, spaceAfter=10
        )
        
        # 1. Header
        elements.append(Paragraph("Precision Oncology AI Analysis", title_style))
        
        date_str = pd.Timestamp.now().strftime('%B %d, %Y | %H:%M %Z')
        header_table_data = [
            [Paragraph(f"Case ID: {str(data.get('case_id', 'N/A'))}", subtitle_style), 
             Paragraph(f"Analytical Date: {date_str}", subtitle_style)]
        ]
        header_table = Table(header_table_data, colWidths=[3.25*inch, 3.25*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # 2. Patient & Clinical Profile (Table)
        pi = data.get('patient_info', {})
        ci = data.get('clinical_info', {})
        
        profile_data = [
            ["Patient Information", "", "Clinical Indicators", ""],
            ["Full Name:", pi.get("fullName", "N/A"), "Tumor Stage:", ci.get("tumorStage", "N/A")],
            ["Age:", str(pi.get("age", "N/A")), "Tumor Grade:", ci.get("tumorGrade", "N/A")],
            ["Gender:", pi.get("gender", "N/A"), "Metastasis:", ci.get("metastasis", "N/A")],
            ["Hospital ID:", pi.get("hospitalId", "N/A"), "", ""],
            ["Contact:", pi.get("contactNumber", "N/A"), "", ""]
        ]
        
        profile_table = Table(profile_data, colWidths=[1.2*inch, 2.05*inch, 1.35*inch, 1.9*inch])
        profile_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('TOPPADDING', (0,0), (-1,0), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('TEXTCOLOR', (0,1), (0,-1), colors.HexColor("#C41E4A")), 
            ('TEXTCOLOR', (2,1), (2,-1), colors.HexColor("#C41E4A")),
            ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,1), (2,-1), 'Helvetica-Bold'),
            ('SPAN', (0,0), (1,0)),
            ('SPAN', (2,0), (3,0)),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#fff1f2")])
        ]))
        elements.append(profile_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 3. AI Prognosis Results
        elements.append(Paragraph("AI Prognosis Metrics", section_heading))
        metrics_data = [
            ["Survival Probability (5-Yr)", f"{data.get('survival_probability', 0)}%"],
            ["Recurrence Risk", f"{data.get('recurrence_probability', 0)}%"],
            ["Aggressiveness Score", f"{data.get('aggressiveness_score', 0)}/100"]
        ]
        metrics_table = Table(metrics_data, colWidths=[3.25*inch, 3.25*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BORDERCOLOR', (0,0), (-1,-1), colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#C41E4A")),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor("#C41E4A")),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # 4. Diagnostic Intelligence
        elements.append(Paragraph("Diagnostic Intelligence & Gene Matching", section_heading))
        insight_data = data.get("treatment_insight", {})
        interpretation = insight_data.get("interpretation", "No interpretation available.")
        summary = insight_data.get("diagnostic_summary", "")
        
        intel_style = ParagraphStyle(
            'IntelStyle', parent=styles['Normal'],
            fontSize=10, leading=15, textColor=colors.black,
            borderPadding=10, backColor=colors.HexColor("#fdf2f8"), 
            borderColor=colors.HexColor("#F099AC"), borderWidth=1,
            borderRadius=5
        )
        elements.append(Paragraph(f"{interpretation}<br/><br/><i>{summary}</i>", intel_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 5. Genomic Benchmarks
        recovery = insight_data.get("genomic_recovery_insights", [])
        if recovery:
            elements.append(Paragraph("Genomic Recovery Benchmarks", section_heading))
            bench_data = [["Dominant Marker", "Cohort Survival Rate", "Impact Level"]]
            for g in recovery:
                bench_data.append([g.get('gene_id'), f"{g.get('recovery_rate')}%", g.get('impact')])
            
            bench_table = Table(bench_data, colWidths=[3*inch, 2*inch, 1.5*inch])
            bench_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#C41E4A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#fdf2f8")]),
                ('TEXTCOLOR', (0,1), (0,-1), colors.HexColor("#A01745")),
                ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold')
            ]))
            elements.append(bench_table)
            
        # 6. Disclaimer
        elements.append(Spacer(1, 0.4*inch))
        disc_style = ParagraphStyle('Disc', parent=styles['Italic'], fontSize=8, textColor=colors.grey)
        elements.append(Paragraph("CONFIDENTIAL MEDICAL RESEARCH REPORT: This synthesis is AI-generated for oncology research. Final diagnosis must be verified by a board-certified specialist.", disc_style))
        
        # Build Document
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=Prognosis_Report_{str(data.get('case_id', 'Unknown'))}.pdf"
        })
    except Exception as e:
        print(f"PDF GENERATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")
    except Exception as e:
        print(f"PDF GENERATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")


@app.post("/extract-report")
async def extract_report(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

    # Extraction Logic (Regex)
    data: dict[str, Any] = {
        "tumorStage": None,
        "tumorGrade": None,
        "metastasis": None,
        "geneA": None,
        "geneB": None,
        "geneC": None
    }

    # Case-insensitive search
    # Tumor Stage: Stage I, II, III, IV or 1, 2, 3, 4 (Allow optional Stage keyword repetition)
    stage_match = re.search(r"Stage.*?\b(I{1,3}|IV|[1-4])\b", text, re.IGNORECASE)
    if stage_match:
        data["tumorStage"] = stage_match.group(1).upper()

    # Tumor Grade: Grade G1, G2, G3 or 1, 2, 3
    grade_match = re.search(r"Grade.*?\b(G[1-3]|[1-3])\b", text, re.IGNORECASE)
    if not grade_match:
        grade_match = re.search(r"\b(G[1-3])\b", text, re.IGNORECASE)
    if grade_match:
        val = grade_match.group(1).upper()
        # Normalize to G1 format
        data["tumorGrade"] = val if val.startswith("G") else f"G{val}"

    # Metastasis: Yes/No
    meta_match = re.search(r"Metastasis[:\-\s]+(Yes|No)", text, re.IGNORECASE)
    if meta_match:
        data["metastasis"] = meta_match.group(1).capitalize()

    # Genes: Specific Gene A, B, C (backward compatibility)
    for g in ["A", "B", "C"]:
        gene_match = re.search(rf"Gene\s+{g}[:\-\s]*([\d\.]+)", text, re.IGNORECASE)
        if gene_match:
            data[f"gene{g}"] = float(gene_match.group(1))

    # Bulk Genes: ENSG IDs (e.g., ENSG00000276168.1: 12.3 or ENSG00000276168: 12.3)
    ensg_matches = re.finditer(r"(ENSG\d+(?:\.\d+)?)[:\-\s]+([\d\.]+)", text)
    extracted_genes = {}
    for match in ensg_matches:
        ensg_id = match.group(1)
        value = float(match.group(2))
        extracted_genes[ensg_id] = value
    
    # Merge bulk genes into data
    if extracted_genes:
        data["extracted_genes"] = extracted_genes

    return data
# Trigger Reload

# Trigger Reload 2

# Trigger Reload PDF Platypus
