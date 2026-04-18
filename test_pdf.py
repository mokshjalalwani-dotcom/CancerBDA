import requests
import json
import time

data = {
    "case_id": "88aa1634-d51b-4b0e-89bb-086709b24e2b",
    "patient_info": {"fullName": "Jane Doe", "age": 45, "gender": "Female", "hospitalId": "H1234", "contactNumber": "555-0199"},
    "clinical_info": {"tumorStage": "STAGE II", "tumorGrade": "G2", "metastasis": "No"},
    "survival_probability": 85.0,
    "recurrence_probability": 12.5,
    "aggressiveness_score": 30,
    "treatment_insight": {
        "interpretation": "High survival expected.",
        "diagnostic_summary": "No metastasis.",
        "genomic_recovery_insights": [{"gene_id": "ENSG123", "recovery_rate": 85.0, "impact": "High"}]
    }
}

try:
    r = requests.post("http://127.0.0.1:8001/generate-report-pdf", json=data)
    print("Status:", r.status_code)
    if r.status_code == 200:
        with open("test_report.pdf", "wb") as f:
            f.write(r.content)
        print("Saved test_report.pdf successfully")
    else:
        print(r.text)
except Exception as e:
    print(e)
