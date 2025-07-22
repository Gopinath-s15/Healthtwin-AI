import pytesseract
from PIL import Image
import re
import json
from typing import Dict, Any, Optional
import os

class PrescriptionOCR:
    def __init__(self):
        # Configure tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract raw text from prescription image"""
        try:
            image = Image.open(image_path)
            # Enhance image for better OCR
            image = image.convert('RGB')
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    def parse_prescription_details(self, raw_text: str) -> Dict[str, Any]:
        """Parse extracted text to identify prescription components"""
        details = {
            "clinic_name": "",
            "doctor_name": "",
            "patient_name": "",
            "patient_age": "",
            "patient_gender": "",
            "prescription_date": "",
            "medications": [],
            "diagnosis": "",
            "instructions": "",
            "follow_up": "",
            "raw_text": raw_text
        }
        
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Extract clinic/hospital name (usually at top)
            if i < 3 and any(word in line_lower for word in ['clinic', 'hospital', 'medical', 'center', 'healthcare']):
                details["clinic_name"] = line
            
            # Extract doctor name
            if any(prefix in line_lower for prefix in ['dr.', 'dr ', 'doctor']):
                details["doctor_name"] = line
            
            # Extract patient name
            if any(prefix in line_lower for prefix in ['patient:', 'name:', 'pt:']):
                details["patient_name"] = re.sub(r'(patient:|name:|pt:)', '', line, flags=re.IGNORECASE).strip()
            
            # Extract age
            age_match = re.search(r'age[:\s]*(\d+)', line_lower)
            if age_match:
                details["patient_age"] = age_match.group(1)
            
            # Extract gender
            if any(gender in line_lower for gender in ['male', 'female', 'm/f', 'gender']):
                details["patient_gender"] = line
            
            # Extract date
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4}',
                r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, line_lower)
                if date_match:
                    details["prescription_date"] = date_match.group(0)
                    break
            
            # Extract medications (look for common patterns)
            if any(indicator in line_lower for indicator in ['tab', 'cap', 'syrup', 'mg', 'ml', 'twice', 'daily', 'morning', 'evening']):
                if line not in details["medications"]:
                    details["medications"].append(line)
            
            # Extract diagnosis
            if any(prefix in line_lower for prefix in ['diagnosis:', 'dx:', 'condition:']):
                details["diagnosis"] = re.sub(r'(diagnosis:|dx:|condition:)', '', line, flags=re.IGNORECASE).strip()
            
            # Extract instructions
            if any(word in line_lower for word in ['take', 'apply', 'use', 'follow', 'avoid']):
                if details["instructions"]:
                    details["instructions"] += " " + line
                else:
                    details["instructions"] = line
            
            # Extract follow-up
            if any(word in line_lower for word in ['follow', 'next', 'visit', 'review']):
                details["follow_up"] = line
        
        return details
    
    def process_prescription(self, image_path: str) -> Dict[str, Any]:
        """Complete prescription processing pipeline"""
        raw_text = self.extract_text_from_image(image_path)
        if not raw_text:
            return {"error": "Could not extract text from image"}
        
        parsed_details = self.parse_prescription_details(raw_text)
        
        # Format medications as string
        medications_str = "; ".join(parsed_details["medications"]) if parsed_details["medications"] else "Not clearly visible"
        
        return {
            "clinic_name": parsed_details["clinic_name"] or "Not found",
            "doctor_name": parsed_details["doctor_name"] or "Not clearly visible",
            "patient_name": parsed_details["patient_name"] or "Not clearly visible",
            "patient_details": f"Age: {parsed_details['patient_age'] or 'N/A'}, Gender: {parsed_details['patient_gender'] or 'N/A'}",
            "prescription_date": parsed_details["prescription_date"] or "Not found",
            "diagnosis": parsed_details["diagnosis"] or "Not clearly specified",
            "medications": medications_str,
            "instructions": parsed_details["instructions"] or "Follow doctor's advice",
            "follow_up": parsed_details["follow_up"] or "As advised",
            "raw_extracted_text": raw_text,
            "confidence": "Medium" if len(raw_text) > 50 else "Low"
        }