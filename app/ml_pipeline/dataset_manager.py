#!/usr/bin/env python3
"""
Dataset Manager for Handwriting Recognition Enhancement
Handles IAM Words dataset and custom medical datasets
"""

import os
import requests
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, List, Tuple, Optional
import json
import sqlite3

logger = logging.getLogger(__name__)

class DatasetManager:
    def __init__(self, data_dir: str = "data/datasets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset paths
        self.iam_dir = self.data_dir / "iam_words"
        self.medical_dir = self.data_dir / "medical_handwriting"
        self.synthetic_dir = self.data_dir / "synthetic_medical"
        
        # Database for medical terms
        self.medical_db_path = self.data_dir / "medical_terms.db"
        self._init_medical_database()
    
    def _init_medical_database(self):
        """Initialize medical terms database with Indian pharmaceutical data"""
        conn = sqlite3.connect(self.medical_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_terms (
                id INTEGER PRIMARY KEY,
                term TEXT UNIQUE,
                category TEXT,
                variations TEXT,
                frequency INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS handwriting_samples (
                id INTEGER PRIMARY KEY,
                term TEXT,
                image_path TEXT,
                transcription TEXT,
                confidence REAL,
                source TEXT
            )
        ''')
        
        # Insert comprehensive Indian medical terms
        indian_medical_terms = [
            ('paracetamol', 'analgesic', '["acetaminophen", "crocin", "dolo"]', 100),
            ('ibuprofen', 'analgesic', '["brufen", "combiflam"]', 95),
            ('amoxicillin', 'antibiotic', '["amoxil", "novamox"]', 90),
            ('azithromycin', 'antibiotic', '["azee", "zithromax"]', 85),
            ('diclofenac', 'analgesic', '["voveran", "voltaren"]', 80),
            ('cetirizine', 'antihistamine', '["zyrtec", "alerid"]', 75),
            ('omeprazole', 'antacid', '["prilosec", "omez"]', 70),
            ('metformin', 'antidiabetic', '["glucophage", "glycomet"]', 85),
            ('amlodipine', 'antihypertensive', '["norvasc", "amlong"]', 80),
            ('atorvastatin', 'statin', '["lipitor", "atorlip"]', 75),
        ]
        
        cursor.executemany(
            'INSERT OR IGNORE INTO medical_terms (term, category, variations, frequency) VALUES (?, ?, ?, ?)',
            indian_medical_terms
        )
        
        conn.commit()
        conn.close()
        
        logger.info("Medical database initialized with Indian pharmaceutical terms")
    
    def get_medical_vocabulary(self) -> Dict[str, Dict]:
        """Get medical vocabulary with metadata"""
        conn = sqlite3.connect(self.medical_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT term, category, variations, frequency FROM medical_terms")
        vocabulary = {}
        
        for term, category, variations_json, frequency in cursor.fetchall():
            variations = json.loads(variations_json) if variations_json else []
            vocabulary[term] = {
                'category': category,
                'variations': variations,
                'frequency': frequency
            }
        
        conn.close()
        return vocabulary

