import re

with open('api/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

pattern = re.compile(r'    # Calculate Gene-Specific Recovery Rates\n    genomic_recovery = \[\]\n    if dominant_genes:\n        for gene_id in dominant_genes:.*?# Generate Logical Diagnostic Summary', re.DOTALL)

new_logic = '''    # Calculate Gene-Specific Recovery Rates
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

    # Generate Logical Diagnostic Summary'''

new_code = pattern.sub(new_logic, code)

if new_code != code:
    with open('api/main.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("Replaced successfully")
else:
    print("Pattern not found")
