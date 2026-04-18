import re

with open('api/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Find the start of the function and the end (the first print("PDF GENERATION ERROR...))
start_def = "@app.post(\"/generate-report-pdf\")\nasync def generate_report_pdf(data: dict):\n"
func_start_idx = code.find(start_def)

if func_start_idx == -1:
    print("Could not find function")
    exit(1)

# we want to replace everything inside the `try:` block.
# Let's use a regex to capture everything from `try:` to the first `except Exception as e:` inside generate_report_pdf.

# It might be easier to just find the indices and slice.

try_idx = code.find("    try:\n", func_start_idx)
except_idx = code.find("    except Exception as e:\n        print(f\"PDF GENERATION ERROR", try_idx)

if try_idx == -1 or except_idx == -1:
    print("Could not find try or except blocks")
    exit(1)

new_try_block = """    try:
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
        elements.append(Paragraph(f"Case ID: {str(data.get('case_id', 'N/A'))} | Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        
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
        
        profile_table = Table(profile_data, colWidths=[1.1*inch, 2.15*inch, 1.25*inch, 2*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#140e1e")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TEXTCOLOR', (0,1), (0,-1), colors.HexColor("#C41E4A")), 
            ('TEXTCOLOR', (2,1), (2,-1), colors.HexColor("#C41E4A")),
            ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,1), (2,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#fdf2f8")])
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
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#140e1e")),
            ('TEXTCOLOR', (0,0), (0,-1), colors.white),
            ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor("#E56B8A")),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('LINEBELOW', (0,0), (-1,-2), 1, colors.HexColor("#5c4d6b"))
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
"""

final_code = code[:try_idx] + new_try_block + code[except_idx:]

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.write(final_code)

print("PDF generation logic updated successfully using Platypus!")
