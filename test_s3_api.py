# test_s3_api.py
import requests
import tempfile
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_invoice_pdf():
    """Create a simple test invoice PDF"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        # Create a simple PDF with invoice-like content
        c = canvas.Canvas(tmp.name, pagesize=letter)
        c.drawString(100, 750, "INVOICE")
        c.drawString(100, 720, "Invoice #: TEST-123")
        c.drawString(100, 700, "Date: 2025-07-30")
        c.drawString(100, 680, "Bill To: Test Company")
        c.drawString(100, 660, "Amount: $500.00")
        c.drawString(100, 640, "Description: Test Service")
        c.save()
        return tmp.name

def test_api():
    """Test the API with a generated PDF"""
    
    # Test health check first
    print("🔍 Testing health check...")
    try:
        response = requests.get("http://localhost:5001/api/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Create test PDF
    print("\n📄 Creating test invoice PDF...")
    try:
        test_pdf_path = create_test_invoice_pdf()
        print(f"Created test PDF: {test_pdf_path}")
    except Exception as e:
        print(f"❌ Could not create test PDF: {e}")
        print("Install reportlab: pip install reportlab")
        return
    
    # Test API upload
    print("\n🚀 Testing API upload...")
    try:
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test_invoice.pdf', f, 'application/pdf')}
            response = requests.post("http://localhost:5001/api/extract-invoice", files=files)
        
        print(f"Upload status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ SUCCESS!")
                print(f"Filename: {data['filename']}")
                print("Extracted data:")
                print(json.dumps(data['data'], indent=2))
            else:
                print(f"❌ API Error: {data['error']}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
    
    # Clean up
    import os
    try:
        os.unlink(test_pdf_path)
        print(f"\n🧹 Cleaned up test file")
    except:
        pass

if __name__ == "__main__":
    test_api()
