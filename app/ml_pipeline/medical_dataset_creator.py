#!/usr/bin/env python3
"""
Medical Dataset Creator for HealthTwin AI
Creates synthetic handwritten medical samples for training
"""

import os
import cv2
import numpy as np
import random
import logging
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3

logger = logging.getLogger(__name__)

class MedicalDatasetCreator:
    def __init__(self, dataset_manager):
        self.dataset_manager = dataset_manager
        self.medical_terms = self._load_indian_medical_terms()
        self.fonts_dir = Path("data/fonts")
        self._setup_fonts()
    
    def _load_indian_medical_terms(self) -> Dict[str, List[str]]:
        """Load comprehensive Indian medical terms"""
        return {
            "antibiotics": [
                "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline",
                "cephalexin", "metronidazole", "clarithromycin", "levofloxacin",
                "ampicillin", "erythromycin", "clindamycin", "cefixime"
            ],
            "analgesics": [
                "paracetamol", "ibuprofen", "diclofenac", "aspirin",
                "tramadol", "ketorolac", "nimesulide", "aceclofenac",
                "piroxicam", "indomethacin", "naproxen", "celecoxib"
            ],
            "indian_brands": [
                "crocin", "combiflam", "volini", "moov", "dolo",
                "zerodol", "flexon", "brufen", "disprin", "anacin",
                "saridon", "dart", "voveran", "omez", "pan"
            ],
            "dosage_forms": [
                "tablet", "capsule", "syrup", "gel", "cream", "ointment",
                "drops", "injection", "powder", "lotion", "suspension"
            ],
            "dosage_units": [
                "mg", "ml", "gm", "mcg", "iu", "units", "drops", 
                "tsp", "tbsp", "cc", "oz"
            ],
            "frequencies": [
                "once daily", "twice daily", "thrice daily", "qid", "bid", "tid",
                "sos", "stat", "prn", "ac", "pc", "hs", "morning", "evening",
                "before meals", "after meals", "at bedtime"
            ]
        }
    
    def _setup_fonts(self):
        """Setup fonts for synthetic generation"""
        self.fonts_dir.mkdir(exist_ok=True)
        # Note: In production, you would download handwriting-like fonts
        logger.info("Font directory created for synthetic generation")
    
    def create_synthetic_samples(self, num_samples: int = 1000) -> List[Dict]:
        """Generate synthetic handwritten medical samples"""
        samples = []
        
        for i in range(num_samples):
            # Select random medical term
            category = random.choice(list(self.medical_terms.keys()))
            term = random.choice(self.medical_terms[category])
            
            # Add variations and common misspellings
            variations = self._generate_variations(term)
            
            for variation in variations[:2]:  # Limit variations
                sample = self._create_handwritten_sample(variation, category)
                if sample:
                    samples.append(sample)
        
        logger.info(f"Created {len(samples)} synthetic medical samples")
        return samples
    
    def _generate_variations(self, term: str) -> List[str]:
        """Generate common handwriting variations and OCR errors"""
        variations = [term]
        
        # Common handwriting errors for medical terms
        error_patterns = {
            'a': ['o', 'e'], 'e': ['a', 'o'], 'i': ['l', 'j', '1'],
            'o': ['a', '0'], 'u': ['n', 'v'], 'n': ['m', 'u'],
            'rn': ['m'], 'cl': ['d'], 'li': ['h'], 'vv': ['w'],
            'mg': ['mq', 'my'], 'ml': ['m1', 'mi']
        }
        
        for original, replacements in error_patterns.items():
            if original in term:
                for replacement in replacements:
                    new_term = term.replace(original, replacement)
                    if new_term != term:
                        variations.append(new_term)
        
        return list(set(variations))
    
    def _create_handwritten_sample(self, text: str, category: str) -> Optional[Dict]:
        """Create a synthetic handwritten sample"""
        try:
            # Create image with handwriting-like characteristics
            img_width, img_height = 200, 50
            img = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Simulate handwriting variations
            x_offset = random.randint(5, 15)
            y_offset = random.randint(5, 15)
            
            # Draw text (simplified - in production use handwriting fonts)
            draw.text((x_offset, y_offset), text, fill='black')
            
            # Convert to numpy for OpenCV processing
            img_array = np.array(img)
            
            # Add handwriting-like distortions
            img_array = self._add_handwriting_distortions(img_array)
            
            # Save sample
            sample_id = f"{category}_{text}_{random.randint(1000, 9999)}"
            sample_dir = self.dataset_manager.medical_dir
            sample_dir.mkdir(exist_ok=True)
            sample_path = sample_dir / f"{sample_id}.png"
            
            cv2.imwrite(str(sample_path), img_array)
            
            return {
                'id': sample_id,
                'text': text,
                'category': category,
                'image_path': str(sample_path),
                'source': 'synthetic'
            }
            
        except Exception as e:
            logger.error(f"Failed to create sample for {text}: {e}")
            return None
    
    def _add_handwriting_distortions(self, img_array: np.ndarray) -> np.ndarray:
        """Add realistic handwriting distortions"""
        # Add slight blur
        img_array = cv2.GaussianBlur(img_array, (3, 3), 0.5)
        
        # Add noise
        noise = np.random.normal(0, 10, img_array.shape).astype(np.uint8)
        img_array = cv2.add(img_array, noise)
        
        # Slight rotation
        angle = random.uniform(-2, 2)
        center = (img_array.shape[1]//2, img_array.shape[0]//2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        img_array = cv2.warpAffine(img_array, rotation_matrix, (img_array.shape[1], img_array.shape[0]))
        
        return img_array

