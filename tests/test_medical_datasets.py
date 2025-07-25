#!/usr/bin/env python3
"""
Tests for medical dataset integration
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.ml_pipeline.dataset_manager import DatasetManager
from app.ml_pipeline.medical_dataset_creator import MedicalDatasetCreator
from app.ml_pipeline.handwriting_specialist import HandwritingSpecialist

class TestMedicalDatasets(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.dataset_manager = DatasetManager(self.temp_dir)
        self.dataset_creator = MedicalDatasetCreator(self.dataset_manager)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_synthetic_sample_creation(self):
        """Test synthetic medical sample creation"""
        samples = self.dataset_creator.create_synthetic_samples(num_samples=10)
        
        self.assertGreater(len(samples), 0)
        self.assertTrue(all('text' in sample for sample in samples))
        self.assertTrue(all('category' in sample for sample in samples))
    
    def test_handwriting_specialist_enhancement(self):
        """Test handwriting specialist with medical context"""
        specialist = HandwritingSpecialist()
        
        # Test medical context enhancement
        test_text = "paracetamol 500mg twice daily"
        enhanced = specialist.enhance_with_medical_context(test_text)
        
        self.assertIsInstance(enhanced, str)
        self.assertIn("paracetamol", enhanced.lower())

if __name__ == "__main__":
    unittest.main()