from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 50, "CANCER PROGNOSIS SYSTEM - SAMPLE MEDICAL REPORT")

    # Patient info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, "Patient Information:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 120, "Full Name: Johnathan Smith")
    c.drawString(70, height - 135, "Hospital ID: HOSP-99231")
    c.drawString(70, height - 150, "Age: 58")
    c.drawString(70, height - 165, "Gender: Male")

    # Clinical findings
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 200, "Clinical Findings:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 220, "Tumor Stage: Stage III")
    c.drawString(70, height - 235, "Tumor Grade: G2")
    c.drawString(70, height - 250, "Metastasis: No")

    # Genomic Profile
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 300, "Genomic Profile:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 320, "The following genetic markers were identified and quantified:")

    genes = [
        ("ENSG00000276168.1", "14.522"),
        ("ENSG00000198712.1", "8.910"),
        ("ENSG00000198938.2", "2.345"),
        ("ENSG00000198804.2", "1.102"),
        ("ENSG00000210082.2", "4.567"),
        ("ENSG00000211592.8", "0.892"),
        ("ENSG00000198886.2", "12.110"),
        ("ENSG00000198899.2", "5.670"),
        ("ENSG00000277437.1", "0.123"),
        ("ENSG00000198840.2", "7.890"),
        ("Gene A", "15.20"),
        ("Gene B", "3.45"),
        ("Gene C", "0.92")
    ]

    y = height - 340
    for gene, value in genes:
        c.drawString(70, y, f"{gene}: {value}")
        y -= 15

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This report is generated for testing purposes for the Cancer Prognosis API.")
    
    c.save()
    print(f"PDF generated: {filename}")

if __name__ == "__main__":
    generate_pdf("sample_report.pdf")
