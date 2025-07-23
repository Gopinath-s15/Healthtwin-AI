#!/usr/bin/env python3
"""
Create a simple test PDF with prescription-like content for testing
"""

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def create_test_prescription_pdf():
    """Create a simple test PDF with prescription content"""
    
    if not REPORTLAB_AVAILABLE:
        print("❌ ReportLab not available. Install with: pip install reportlab")
        return False
    
    filename = "test_prescription.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add prescription content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Dr. Smith Medical Clinic")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, "123 Medical Street, Health City")
    c.drawString(100, height - 150, "Phone: (555) 123-4567")
    
    c.line(100, height - 170, 500, height - 170)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 200, "PRESCRIPTION")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 230, "Patient: John Doe")
    c.drawString(100, height - 250, "Date: July 23, 2025")
    c.drawString(100, height - 270, "DOB: 01/15/1980")
    
    c.line(100, height - 290, 500, height - 290)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 320, "Medications:")
    
    c.setFont("Helvetica", 11)
    medications = [
        "1. Amoxicillin 500mg - Take 1 tablet twice daily for 7 days",
        "2. Paracetamol 650mg - Take 1 tablet as needed for pain",
        "3. Vitamin D3 1000 IU - Take 1 tablet daily"
    ]
    
    y_pos = height - 350
    for med in medications:
        c.drawString(120, y_pos, med)
        y_pos -= 25
    
    c.line(100, y_pos - 20, 500, y_pos - 20)
    
    c.setFont("Helvetica", 10)
    c.drawString(100, y_pos - 50, "Instructions: Take medications as prescribed. Follow up in 1 week.")
    c.drawString(100, y_pos - 70, "Doctor's Signature: Dr. Smith")
    
    # Add a second page
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Follow-up Instructions - Page 2")
    
    c.setFont("Helvetica", 12)
    instructions = [
        "• Complete the full course of antibiotics",
        "• Return if symptoms worsen",
        "• Schedule follow-up appointment in 1 week",
        "• Contact clinic if any adverse reactions occur"
    ]
    
    y_pos = height - 140
    for instruction in instructions:
        c.drawString(120, y_pos, instruction)
        y_pos -= 25
    
    c.save()
    
    print(f"✅ Created test PDF: {filename}")
    return True

if __name__ == "__main__":
    print("Creating test prescription PDF...")
    
    if create_test_prescription_pdf():
        print("✅ Test PDF created successfully!")
        print("You can now test PDF upload functionality with 'test_prescription.pdf'")
    else:
        print("❌ Failed to create test PDF")
        print("Install ReportLab with: pip install reportlab")
