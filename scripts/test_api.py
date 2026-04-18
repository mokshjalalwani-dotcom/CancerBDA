import requests
import os

def test_extraction():
    url = "http://localhost:8001/extract-report"
    pdf_path = r"c:\Users\moksh\Desktop\Projects\cancerP\test_report.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    print(f"Testing with: {pdf_path}")
    files = {'file': open(pdf_path, 'rb')}
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extraction()
