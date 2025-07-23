
"""
Enhanced Medical Named Entity Recognition Engine
"""
import re
import logging
from typing import Dict, List, Set
from collections import defaultdict

class MedicalNEREngine:
    """Enhanced Medical NER for prescription processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.medication_patterns = self._build_medication_patterns()
        self.doctor_patterns = self._build_doctor_patterns()
        self.diagnosis_patterns = self._build_diagnosis_patterns()
        
    def _build_medication_patterns(self) -> List[str]:
        """Build comprehensive medication patterns"""
        return [
            r'(?:Tab|Tablet|Cap|Capsule|Syrup|Injection|Drops)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\s*(?:\d+\s*(?:mg|ml|gm|mcg))?',
            r'([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+\d+\s*(?:mg|ml|gm|mcg)',
            r'Rx:?\s*([A-Za-z\s,]+)',
            r'(?:Medicine|Medication|Drug):\s*([A-Za-z\s,]+)',
            r'Take\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)',
            r'([A-Za-z]+(?:cillin|mycin|prazole|statin|sartan))',  # Common drug suffixes
        ]
    
    def _build_doctor_patterns(self) -> List[str]:
        """Build doctor name patterns"""
        return [
            r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Doctor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,?\s*M\.?D\.?',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,?\s*MBBS',
            r'Dr\.?\s*([A-Z\s\.]+?)(?:\s*M\.?D\.?|\s*MBBS|\s*\()',
        ]
    
    def _build_diagnosis_patterns(self) -> List[str]:
        """Build diagnosis patterns"""
        return [
            r'(?:Diagnosis|Dx|Condition):\s*([A-Za-z\s,]+)',
            r'(?:Suffering from|Diagnosed with)\s+([A-Za-z\s,]+)',
            r'(?:Patient has|Presenting with)\s+([A-Za-z\s,]+)',
        ]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text"""
        entities = defaultdict(list)
        
        try:
            # Extract medications
            medications = self._extract_medications(text)
            entities['medications'] = medications
            
            # Extract doctor names
            doctors = self._extract_doctors(text)
            entities['doctor_names'] = doctors
            
            # Extract diagnoses
            diagnoses = self._extract_diagnoses(text)
            entities['diagnoses'] = diagnoses
            
            # Extract clinic names
            clinics = self._extract_clinics(text)
            entities['clinic_names'] = clinics
            
            # Extract instructions
            instructions = self._extract_instructions(text)
            entities['instructions'] = instructions
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
        
        return dict(entities)
    
    def _extract_medications(self, text: str) -> List[str]:
        """Extract medication names"""
        medications = set()
        
        for pattern in self.medication_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Clean and validate
                clean_med = self._clean_medication_name(match)
                if clean_med and len(clean_med) > 2:
                    medications.add(clean_med)
        
        return list(medications)
    
    def _extract_doctors(self, text: str) -> List[str]:
        """Extract doctor names"""
        doctors = set()
        
        for pattern in self.doctor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Clean and validate
                clean_name = self._clean_doctor_name(match)
                if clean_name:
                    doctors.add(clean_name)
        
        return list(doctors)
    
    def _extract_diagnoses(self, text: str) -> List[str]:
        """Extract diagnoses"""
        diagnoses = set()
        
        for pattern in self.diagnosis_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Clean and validate
                clean_diagnosis = self._clean_diagnosis(match)
                if clean_diagnosis:
                    diagnoses.add(clean_diagnosis)
        
        return list(diagnoses)
    
    def _extract_clinics(self, text: str) -> List[str]:
        """Extract clinic/hospital names"""
        clinic_patterns = [
            r'([A-Z][A-Za-z\s]+(?:Clinic|Hospital|Medical Center|Healthcare|Nursing Home))',
            r'((?:Clinic|Hospital|Medical Center|Healthcare|Nursing Home)\s+[A-Za-z\s]+)',
            r'([A-Z][A-Za-z\s]+Plaza)',
        ]
        
        clinics = set()
        for pattern in clinic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_clinic = match.strip()
                if len(clean_clinic) > 5:
                    clinics.add(clean_clinic)
        
        return list(clinics)
    
    def _extract_instructions(self, text: str) -> List[str]:
        """Extract medication instructions"""
        instruction_patterns = [
            r'(?:Take|Apply|Use)\s+([^.]+)',
            r'(?:Dosage|Dose):\s*([^.]+)',
            r'(?:Instructions?):\s*([^.]+)',
            r'(?:twice|once|thrice)\s+(?:daily|a day|per day)',
            r'(?:morning|evening|night|bedtime)',
            r'(?:before|after)\s+(?:meals|food)',
        ]
        
        instructions = set()
        for pattern in instruction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_instruction = match.strip()
                if len(clean_instruction) > 3:
                    instructions.add(clean_instruction)
        
        return list(instructions)
    
    def _clean_medication_name(self, name: str) -> str:
        """Clean medication name"""
        # Remove common OCR artifacts
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Filter out common non-medication words
        exclude_words = {'the', 'and', 'or', 'with', 'for', 'take', 'tablet', 'capsule'}
        words = name.lower().split()
        filtered_words = [w for w in words if w not in exclude_words and len(w) > 1]
        
        return ' '.join(filtered_words).title() if filtered_words else ''
    
    def _clean_doctor_name(self, name: str) -> str:
        """Clean doctor name"""
        # Remove titles and clean
        name = re.sub(r'(?:Dr\.?|Doctor)\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*,?\s*M\.?D\.?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*,?\s*MBBS\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Validate name format
        if len(name) > 2 and re.match(r'^[A-Za-z\s]+$', name):
            return f"Dr. {name.title()}"
        
        return ''
    
    def _clean_diagnosis(self, diagnosis: str) -> str:
        """Clean diagnosis text"""
        diagnosis = re.sub(r'[^\w\s]', '', diagnosis)
        diagnosis = re.sub(r'\s+', ' ', diagnosis).strip()
        
        if len(diagnosis) > 3:
            return diagnosis.title()
        
        return ''




