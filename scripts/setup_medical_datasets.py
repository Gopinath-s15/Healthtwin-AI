#!/usr/bin/env python3
"""
Setup script for medical handwriting datasets
"""

import logging
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "app"))

from app.ml_pipeline.dataset_manager import DatasetManager
from app.ml_pipeline.medical_dataset_creator import MedicalDatasetCreator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    logger.info("🚀 Setting up medical handwriting datasets...")
    
    try:
        # Initialize components
        dataset_manager = DatasetManager()
        dataset_creator = MedicalDatasetCreator(dataset_manager)
        
        # Create synthetic medical samples
        logger.info("📝 Creating synthetic medical samples...")
        synthetic_samples = dataset_creator.create_synthetic_samples(num_samples=500)
        
        # Save samples metadata
        samples_file = dataset_manager.data_dir / "medical_samples.json"
        with open(samples_file, 'w') as f:
            json.dump(synthetic_samples, f, indent=2)
        
        logger.info(f"✅ Created {len(synthetic_samples)} synthetic samples")
        logger.info(f"📁 Samples saved to: {samples_file}")
        
        # Test medical vocabulary
        vocabulary = dataset_manager.get_medical_vocabulary()
        logger.info(f"📚 Medical vocabulary loaded: {len(vocabulary)} terms")
        
        logger.info("🎉 Medical dataset setup completed!")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
