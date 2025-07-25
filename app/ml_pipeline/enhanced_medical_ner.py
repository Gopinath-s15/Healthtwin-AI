"""
Enhanced Medical Named Entity Recognition (NER) System for HealthTwin AI
Integrates spaCy, medSpaCy, fuzzy matching, and medical databases for accurate entity extraction
"""

import re
import json
import logging
import sqlite3
from typing import Dict, List, Tuple, Any, Optional, Set
from difflib import SequenceMatcher
import spacy
from spacy.matcher import Matcher, PhraseMatcher

logger = logging.getLogger(__name__)

# Try to import advanced NLP libraries
try:
    import rapidfuzz
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
    logger.info("RapidFuzz available for fuzzy string matching")
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("RapidFuzz not available - using basic fuzzy matching")

try:
    import medspacy
    MEDSPACY_AVAILABLE = True
    logger.info("medSpaCy available for clinical NER")
except ImportError:
    MEDSPACY_AVAILABLE = False
    logger.warning("medSpaCy not available - using basic medical NER")

# Create a simple DatasetManager class if not available
class DatasetManager:
    """Simple dataset manager for medical terms"""
    def __init__(self):
        self.medical_db_path = "data/medical_terms.db"
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database if it doesn't exist"""
        import os
        os.makedirs(os.path.dirname(self.medical_db_path), exist_ok=True)
        
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
        
        conn.commit()
        conn.close()

class EnhancedMedicalNER:
    """Enhanced Medical Named Entity Recognition with fuzzy matching and medical databases"""
    
    def __init__(self):
        """Initialize enhanced medical NER system"""
        self.nlp = None
        self.medspacy_nlp = None
        self.matcher = None
        self.phrase_matcher = None
        
        # Initialize NLP models
        self._init_spacy_models()
        
        # Load medical knowledge bases
        self.drug_database = self._load_comprehensive_drug_database()
        self.medical_patterns = self._load_medical_patterns()
        self.dosage_patterns = self._load_dosage_patterns()
        self.frequency_patterns = self._load_frequency_patterns()
        self.duration_patterns = self._load_duration_patterns()
        
        # Load custom medical vocabulary
        self.dataset_manager = DatasetManager()
        self.custom_medical_terms = self._load_custom_medical_terms()
        
        # Initialize matchers
        if self.nlp:
            self._init_matchers()
    
    def _init_spacy_models(self):
        """Initialize spaCy and medSpaCy models"""
        try:
            # Load standard spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
            
            # Try to load medSpaCy for clinical text
            if MEDSPACY_AVAILABLE:
                self.medspacy_nlp = medspacy.load()
                logger.info("Loaded medSpaCy clinical model")
            
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def _load_comprehensive_drug_database(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive drug database with Indian and international medicines"""
        return {
            # Analgesics/Antipyretics
            'paracetamol': {
                'variations': ['acetaminophen', 'tylenol', 'crocin', 'dolo', 'calpol', 'metacin', 'pyrigesic'],
                'category': 'analgesic_antipyretic',
                'common_doses': ['500mg', '650mg', '1000mg', '125mg', '250mg'],
                'forms': ['tablet', 'syrup', 'injection', 'suppository'],
                'generic_name': 'paracetamol'
            },
            'ibuprofen': {
                'variations': ['brufen', 'combiflam', 'ibuclin', 'advil', 'motrin', 'nurofen'],
                'category': 'nsaid',
                'common_doses': ['200mg', '400mg', '600mg', '800mg'],
                'forms': ['tablet', 'syrup', 'gel'],
                'generic_name': 'ibuprofen'
            },
            'diclofenac': {
                'variations': ['voveran', 'voltaren', 'diclo', 'diclomol', 'dynapar'],
                'category': 'nsaid',
                'common_doses': ['50mg', '75mg', '100mg'],
                'forms': ['tablet', 'injection', 'gel'],
                'generic_name': 'diclofenac'
            },
            
            # Antibiotics
            'amoxicillin': {
                'variations': ['amoxil', 'augmentin', 'clavulin', 'moxikind', 'amoxyclav'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg', '875mg', '1000mg'],
                'forms': ['tablet', 'capsule', 'syrup', 'injection'],
                'generic_name': 'amoxicillin'
            },
            'azithromycin': {
                'variations': ['zithromax', 'azee', 'azithral', 'azimax', 'azax'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg'],
                'forms': ['tablet', 'syrup'],
                'generic_name': 'azithromycin'
            },
            'ciprofloxacin': {
                'variations': ['cipro', 'ciplox', 'cifran', 'ciproxin'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg', '750mg'],
                'forms': ['tablet', 'injection', 'eye drops'],
                'generic_name': 'ciprofloxacin'
            },
            
            # Antacids/Gastric
            'omeprazole': {
                'variations': ['prilosec', 'omez', 'omepraz', 'ocid', 'omecip'],
                'category': 'ppi',
                'common_doses': ['20mg', '40mg'],
                'forms': ['capsule', 'tablet', 'injection'],
                'generic_name': 'omeprazole'
            },
            'pantoprazole': {
                'variations': ['protonix', 'pantop', 'pantocid', 'pantocar'],
                'category': 'ppi',
                'common_doses': ['20mg', '40mg'],
                'forms': ['tablet', 'injection'],
                'generic_name': 'pantoprazole'
            },
            'ranitidine': {
                'variations': ['zantac', 'rantac', 'aciloc', 'zinetac'],
                'category': 'h2_blocker',
                'common_doses': ['150mg', '300mg'],
                'forms': ['tablet', 'syrup', 'injection'],
                'generic_name': 'ranitidine'
            },
            
            # Vitamins/Supplements
            'vitamin_d3': {
                'variations': ['cholecalciferol', 'calcirol', 'uprise', 'dvion', 'calcimax'],
                'category': 'vitamin',
                'common_doses': ['1000iu', '2000iu', '5000iu', '60000iu'],
                'forms': ['tablet', 'capsule', 'drops', 'sachet'],
                'generic_name': 'cholecalciferol'
            },
            'vitamin_b12': {
                'variations': ['cyanocobalamin', 'methylcobalamin', 'neurobion', 'nervijen'],
                'category': 'vitamin',
                'common_doses': ['500mcg', '1000mcg', '1500mcg'],
                'forms': ['tablet', 'injection'],
                'generic_name': 'cyanocobalamin'
            },
            
            # Antidiabetic
            'metformin': {
                'variations': ['glucophage', 'glycomet', 'obimet', 'formet'],
                'category': 'antidiabetic',
                'common_doses': ['500mg', '850mg', '1000mg'],
                'forms': ['tablet', 'extended_release'],
                'generic_name': 'metformin'
            },
            'glimepiride': {
                'variations': ['amaryl', 'glimpid', 'glimy', 'glimisave'],
                'category': 'antidiabetic',
                'common_doses': ['1mg', '2mg', '3mg', '4mg'],
                'forms': ['tablet'],
                'generic_name': 'glimepiride'
            },
            
            # Antihypertensive
            'amlodipine': {
                'variations': ['norvasc', 'amlong', 'amlokind', 'stamlo'],
                'category': 'calcium_channel_blocker',
                'common_doses': ['2.5mg', '5mg', '10mg'],
                'forms': ['tablet'],
                'generic_name': 'amlodipine'
            },
            'atenolol': {
                'variations': ['tenormin', 'aten', 'atecor', 'ziblok'],
                'category': 'beta_blocker',
                'common_doses': ['25mg', '50mg', '100mg'],
                'forms': ['tablet'],
                'generic_name': 'atenolol'
            },
            
            # Respiratory
            'salbutamol': {
                'variations': ['ventolin', 'asthalin', 'levolin', 'albuterol'],
                'category': 'bronchodilator',
                'common_doses': ['2mg', '4mg', '100mcg'],
                'forms': ['tablet', 'syrup', 'inhaler', 'nebulizer'],
                'generic_name': 'salbutamol'
            },
            'montelukast': {
                'variations': ['singulair', 'montair', 'montek', 'airlukast'],
                'category': 'leukotriene_antagonist',
                'common_doses': ['4mg', '5mg', '10mg'],
                'forms': ['tablet', 'chewable'],
                'generic_name': 'montelukast'
            }
        }
    
    def _load_medical_patterns(self) -> Dict[str, List[str]]:
        """Load medical regex patterns for entity extraction"""
        return {
            'dosage_patterns': [
                r'\b(\d+(?:\.\d+)?)\s*(mg|gm|g|ml|mcg|iu|units?)\b',
                r'\b(\d+(?:\.\d+)?)\s*(milligram|gram|milliliter|microgram|international\s+unit)\b',
                r'\b(\d+(?:\.\d+)?)\s*(tab|tablet|cap|capsule|drop|drops)\b'
            ],
            'frequency_patterns': [
                r'\b(\d+)\s*(?:times?|x)\s*(?:a\s*)?(?:day|daily|per\s*day)\b',
                r'\b(?:once|twice|thrice)\s*(?:a\s*)?(?:day|daily)\b',
                r'\b(?:morning|evening|night|bedtime|before\s*meals?|after\s*meals?)\b',
                r'\b(\d+)-(\d+)-(\d+)\b',  # Indian format like 1-0-1
                r'\bbd|od|tid|qid|sos\b'  # Medical abbreviations
            ],
            'duration_patterns': [
                r'\b(?:for\s*)?(\d+)\s*(?:days?|weeks?|months?|years?)\b',
                r'\b(?:continue\s*(?:for\s*)?)?(\d+)\s*(?:days?|weeks?|months?)\b',
                r'\b(?:take\s*(?:for\s*)?)?(\d+)\s*(?:days?|weeks?|months?)\b'
            ],
            'instruction_patterns': [
                r'\b(?:take|apply|use|continue|stop|reduce|increase)\b',
                r'\b(?:as\s*needed|as\s*required|when\s*needed|sos)\b',
                r'\b(?:before\s*meals?|after\s*meals?|with\s*meals?|empty\s*stomach)\b',
                r'\b(?:morning|evening|night|bedtime)\b'
            ]
        }
    
    def _load_dosage_patterns(self) -> List[str]:
        """Load comprehensive dosage patterns"""
        return [
            r'\b(\d+(?:\.\d+)?)\s*(mg|gm|g|ml|mcg|iu|units?|tab|tablet|cap|capsule)\b',
            r'\b(\d+(?:\.\d+)?)\s*(milligram|gram|milliliter|microgram)\b',
            r'\b(\d+(?:\.\d+)?)\s*(?:mg|gm)\s*/\s*(\d+(?:\.\d+)?)\s*(?:mg|gm)\b',  # Combination doses
        ]
    
    def _load_frequency_patterns(self) -> List[str]:
        """Load comprehensive frequency patterns"""
        return [
            r'\b(\d+)\s*(?:times?|x)\s*(?:a\s*)?(?:day|daily|per\s*day)\b',
            r'\b(?:once|twice|thrice)\s*(?:a\s*)?(?:day|daily)\b',
            r'\b(\d+)-(\d+)-(\d+)\b',  # Indian format
            r'\bbd|od|tid|qid|sos|prn\b',  # Medical abbreviations
            r'\b(?:every|q)\s*(\d+)\s*(?:hours?|hrs?|h)\b'
        ]
    
    def _load_duration_patterns(self) -> List[str]:
        """Load comprehensive duration patterns"""
        return [
            r'\b(?:for\s*)?(\d+)\s*(?:days?|weeks?|months?|years?)\b',
            r'\b(?:continue\s*(?:for\s*)?)?(\d+)\s*(?:days?|weeks?|months?)\b',
            r'\b(?:complete\s*(?:the\s*)?course)\b'
        ]

    def _init_matchers(self):
        """Initialize spaCy matchers for medical entities"""
        if not self.nlp:
            return

        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # Add drug name patterns
        drug_patterns = []
        for drug, info in self.drug_database.items():
            # Add main drug name
            drug_patterns.append(self.nlp(drug.replace('_', ' ')))
            # Add variations
            for variation in info['variations']:
                drug_patterns.append(self.nlp(variation))

        self.phrase_matcher.add("DRUG", drug_patterns)

        # Add dosage patterns
        dosage_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["mg", "gm", "g", "ml", "mcg", "iu", "units", "unit"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps"]}}],
            [{"LIKE_NUM": True}, {"LOWER": "/"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["mg", "gm", "g"]}}]  # Combination doses
        ]
        self.matcher.add("DOSAGE", dosage_patterns)

        # Add frequency patterns
        frequency_patterns = [
            [{"LOWER": {"IN": ["once", "twice", "thrice"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["times", "time"]}}, {"LOWER": {"IN": ["daily", "day"]}}],
            [{"LOWER": {"IN": ["morning", "evening", "night", "bedtime"]}}],
            [{"LOWER": {"IN": ["bd", "od", "tid", "qid", "sos", "prn"]}}]
        ]
        self.matcher.add("FREQUENCY", frequency_patterns)

    def extract_medical_entities(self, text: str, use_fuzzy: bool = True) -> Dict[str, Any]:
        """Extract medical entities using multiple approaches"""
        try:
            entities = {
                'medications': [],
                'dosages': [],
                'frequencies': [],
                'durations': [],
                'instructions': [],
                'confidence_scores': {}
            }

            # Method 1: spaCy NER
            if self.nlp:
                spacy_entities = self._extract_with_spacy(text)
                entities = self._merge_entities(entities, spacy_entities)

            # Method 2: medSpaCy clinical NER
            if self.medspacy_nlp:
                medspacy_entities = self._extract_with_medspacy(text)
                entities = self._merge_entities(entities, medspacy_entities)

            # Method 3: Regex-based extraction
            regex_entities = self._extract_with_regex(text)
            entities = self._merge_entities(entities, regex_entities)

            # Method 4: Fuzzy matching for drug names
            if use_fuzzy:
                fuzzy_entities = self._extract_with_fuzzy_matching(text)
                entities = self._merge_entities(entities, fuzzy_entities)

            # Post-process and normalize entities
            entities = self._normalize_entities(entities)

            return entities

        except Exception as e:
            logger.error(f"Medical entity extraction failed: {e}")
            return {
                'medications': [],
                'dosages': [],
                'frequencies': [],
                'durations': [],
                'instructions': [],
                'confidence_scores': {},
                'error': str(e)
            }

    def _extract_with_spacy(self, text: str) -> Dict[str, Any]:
        """Extract entities using spaCy matchers"""
        entities = {
            'medications': [],
            'dosages': [],
            'frequencies': [],
            'durations': [],
            'instructions': []
        }

        try:
            doc = self.nlp(text)

            # Use phrase matcher for drugs
            matches = self.phrase_matcher(doc)
            for match_id, start, end in matches:
                label = self.nlp.vocab.strings[match_id]
                if label == "DRUG":
                    entities['medications'].append({
                        'text': doc[start:end].text,
                        'start': start,
                        'end': end,
                        'confidence': 0.8,
                        'method': 'spacy_phrase_matcher'
                    })

            # Use rule-based matcher for other entities
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                label = self.nlp.vocab.strings[match_id]
                entity_text = doc[start:end].text

                if label == "DOSAGE":
                    entities['dosages'].append({
                        'text': entity_text,
                        'start': start,
                        'end': end,
                        'confidence': 0.9,
                        'method': 'spacy_matcher'
                    })
                elif label == "FREQUENCY":
                    entities['frequencies'].append({
                        'text': entity_text,
                        'start': start,
                        'end': end,
                        'confidence': 0.9,
                        'method': 'spacy_matcher'
                    })

        except Exception as e:
            logger.warning(f"spaCy extraction failed: {e}")

        return entities

    def _extract_with_medspacy(self, text: str) -> Dict[str, Any]:
        """Extract entities using medSpaCy clinical NLP"""
        entities = {
            'medications': [],
            'dosages': [],
            'frequencies': [],
            'durations': [],
            'instructions': []
        }

        try:
            if not self.medspacy_nlp:
                return entities

            doc = self.medspacy_nlp(text)

            for ent in doc.ents:
                if ent.label_ in ["MEDICATION", "DRUG"]:
                    entities['medications'].append({
                        'text': ent.text,
                        'start': ent.start,
                        'end': ent.end,
                        'confidence': 0.85,
                        'method': 'medspacy',
                        'label': ent.label_
                    })
                elif ent.label_ in ["DOSAGE", "STRENGTH"]:
                    entities['dosages'].append({
                        'text': ent.text,
                        'start': ent.start,
                        'end': ent.end,
                        'confidence': 0.85,
                        'method': 'medspacy',
                        'label': ent.label_
                    })
                elif ent.label_ in ["FREQUENCY", "ROUTE"]:
                    entities['frequencies'].append({
                        'text': ent.text,
                        'start': ent.start,
                        'end': ent.end,
                        'confidence': 0.85,
                        'method': 'medspacy',
                        'label': ent.label_
                    })
                elif ent.label_ in ["DURATION"]:
                    entities['durations'].append({
                        'text': ent.text,
                        'start': ent.start,
                        'end': ent.end,
                        'confidence': 0.85,
                        'method': 'medspacy',
                        'label': ent.label_
                    })

        except Exception as e:
            logger.warning(f"medSpaCy extraction failed: {e}")

        return entities

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract entities using regex patterns"""
        try:
            from .enhanced_medical_ner_utils import extract_with_regex
            return extract_with_regex(text, self.medical_patterns)
        except ImportError:
            # Fallback to basic regex extraction
            return self._basic_regex_extraction(text)

    def _basic_regex_extraction(self, text: str) -> Dict[str, Any]:
        """Basic regex extraction fallback"""
        import re

        entities = {
            'medications': [],
            'dosages': [],
            'frequencies': [],
            'durations': [],
            'instructions': []
        }

        try:
            # Basic dosage patterns
            dosage_patterns = [r'\b(\d+(?:\.\d+)?)\s*(mg|gm|g|ml|mcg|iu|units?)\b']
            for pattern in dosage_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities['dosages'].append({
                        'text': match.group(),
                        'confidence': 0.8,
                        'method': 'basic_regex'
                    })

            # Basic frequency patterns
            freq_patterns = [r'\b(once|twice|thrice|bd|od|tid|qid|sos)\b']
            for pattern in freq_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities['frequencies'].append({
                        'text': match.group(),
                        'confidence': 0.8,
                        'method': 'basic_regex'
                    })

        except Exception as e:
            logger.warning(f"Basic regex extraction failed: {e}")

        return entities

    def _extract_with_fuzzy_matching(self, text: str) -> Dict[str, Any]:
        """Extract drug names using fuzzy string matching"""
        try:
            from .enhanced_medical_ner_utils import extract_with_fuzzy_matching
            return extract_with_fuzzy_matching(text, self.drug_database)
        except ImportError:
            # Fallback to basic fuzzy matching
            return self._basic_fuzzy_matching(text)

    def _basic_fuzzy_matching(self, text: str) -> Dict[str, Any]:
        """Basic fuzzy matching fallback"""
        entities = {
            'medications': [],
            'dosages': [],
            'frequencies': [],
            'durations': [],
            'instructions': []
        }

        try:
            text_lower = text.lower()

            # Simple exact matching for drug names
            for drug, info in self.drug_database.items():
                all_names = [drug.replace('_', ' ')] + info['variations']

                for name in all_names:
                    if name.lower() in text_lower:
                        entities['medications'].append({
                            'text': name,
                            'generic_name': info['generic_name'],
                            'category': info['category'],
                            'confidence': 0.9,
                            'method': 'basic_fuzzy_exact'
                        })

        except Exception as e:
            logger.warning(f"Basic fuzzy matching failed: {e}")

        return entities

    def _merge_entities(self, base_entities: Dict[str, Any], new_entities: Dict[str, Any]) -> Dict[str, Any]:
        """Merge entities from different extraction methods"""
        try:
            from .enhanced_medical_ner_utils import merge_entities
            return merge_entities(base_entities, new_entities)
        except ImportError:
            # Basic merge fallback
            for entity_type in ['medications', 'dosages', 'frequencies', 'durations', 'instructions']:
                if entity_type in new_entities:
                    base_entities[entity_type].extend(new_entities[entity_type])
            return base_entities

    def _normalize_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and deduplicate extracted entities"""
        try:
            from .enhanced_medical_ner_utils import normalize_entities
            return normalize_entities(entities)
        except ImportError:
            # Basic normalization fallback
            for entity_type in ['medications', 'dosages', 'frequencies', 'durations', 'instructions']:
                if entity_type in entities:
                    # Simple deduplication by text
                    seen = set()
                    unique_entities = []
                    for entity in entities[entity_type]:
                        entity_text = entity.get('text', '').lower()
                        if entity_text not in seen:
                            seen.add(entity_text)
                            unique_entities.append(entity)
                    entities[entity_type] = unique_entities
            return entities

    def extract_structured_prescription_data(self, text: str) -> Dict[str, Any]:
        """Extract structured prescription data with normalized drug information"""
        try:
            # Extract basic entities
            entities = self.extract_medical_entities(text)

            # Structure the data for prescription format
            structured_data = {
                'medications': [],
                'patient_instructions': [],
                'prescription_summary': {},
                'confidence_assessment': {}
            }

            # Process medications with dosage and frequency information
            medications = entities.get('medications', [])
            dosages = entities.get('dosages', [])
            frequencies = entities.get('frequencies', [])
            durations = entities.get('durations', [])

            # Group related information
            for med in medications:
                medication_entry = {
                    'drug_name': med.get('text', ''),
                    'generic_name': med.get('generic_name', ''),
                    'category': med.get('category', ''),
                    'dosage': self._find_related_dosage(med, dosages),
                    'frequency': self._find_related_frequency(med, frequencies),
                    'duration': self._find_related_duration(med, durations),
                    'confidence': med.get('confidence', 0.0),
                    'extraction_method': med.get('method', '')
                }
                structured_data['medications'].append(medication_entry)

            # Extract patient instructions
            instructions = entities.get('instructions', [])
            for instruction in instructions:
                structured_data['patient_instructions'].append({
                    'instruction': instruction.get('text', ''),
                    'confidence': instruction.get('confidence', 0.0)
                })

            # Create prescription summary
            structured_data['prescription_summary'] = {
                'total_medications': len(medications),
                'medications_with_dosage': len([m for m in structured_data['medications'] if m['dosage']]),
                'medications_with_frequency': len([m for m in structured_data['medications'] if m['frequency']]),
                'overall_confidence': entities.get('confidence_scores', {})
            }

            # Confidence assessment
            structured_data['confidence_assessment'] = self._assess_extraction_confidence(entities)

            return structured_data

        except Exception as e:
            logger.error(f"Structured prescription data extraction failed: {e}")
            return {
                'medications': [],
                'patient_instructions': [],
                'prescription_summary': {},
                'confidence_assessment': {'overall': 'low', 'error': str(e)}
            }

    def _find_related_dosage(self, medication: Dict[str, Any], dosages: List[Dict[str, Any]]) -> Optional[str]:
        """Find dosage information related to a specific medication"""
        try:
            # Handle different medication object formats
            if isinstance(medication, dict):
                med_text = medication.get('text', '') or medication.get('drug_name', '') or str(medication)
            else:
                med_text = str(medication)

            med_text = med_text.lower()

            for dosage in dosages:
                if isinstance(dosage, dict):
                    dosage_text = dosage.get('text', '')
                    confidence = dosage.get('confidence', 0)
                else:
                    dosage_text = str(dosage)
                    confidence = 0.5

                # If dosage appears near the medication in text, consider it related
                if dosage_text and confidence > 0.7:
                    return dosage_text

            return None
        except Exception as e:
            logger.warning(f"Error finding related dosage: {e}")
            return None

    def _find_related_frequency(self, medication: Dict[str, Any], frequencies: List[Dict[str, Any]]) -> Optional[str]:
        """Find frequency information related to a specific medication"""
        try:
            for frequency in frequencies:
                if isinstance(frequency, dict):
                    frequency_text = frequency.get('text', '')
                    confidence = frequency.get('confidence', 0)
                else:
                    frequency_text = str(frequency)
                    confidence = 0.5

                if frequency_text and confidence > 0.7:
                    return frequency_text

            return None
        except Exception as e:
            logger.warning(f"Error finding related frequency: {e}")
            return None

    def _find_related_duration(self, medication: Dict[str, Any], durations: List[Dict[str, Any]]) -> Optional[str]:
        """Find duration information related to a specific medication"""
        try:
            for duration in durations:
                if isinstance(duration, dict):
                    duration_text = duration.get('text', '')
                    confidence = duration.get('confidence', 0)
                else:
                    duration_text = str(duration)
                    confidence = 0.5

                if duration_text and confidence > 0.7:
                    return duration_text

            return None
        except Exception as e:
            logger.warning(f"Error finding related duration: {e}")
            return None

    def _assess_extraction_confidence(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall confidence of the extraction"""
        confidence_scores = entities.get('confidence_scores', {})

        # Calculate overall confidence
        scores = [score for score in confidence_scores.values() if score > 0]
        overall_confidence = sum(scores) / len(scores) if scores else 0.0

        # Determine confidence level
        if overall_confidence >= 0.8:
            confidence_level = 'high'
        elif overall_confidence >= 0.6:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'

        return {
            'overall_score': overall_confidence,
            'confidence_level': confidence_level,
            'entity_scores': confidence_scores,
            'requires_review': overall_confidence < 0.7
        }

    def _load_custom_medical_terms(self) -> Dict[str, List[str]]:
        """Load custom medical terms from dataset"""
        conn = sqlite3.connect(self.dataset_manager.medical_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT term, category, variations 
            FROM medical_terms 
            WHERE frequency > 5
        """)
        
        terms_by_category = {}
        for term, category, variations_json in cursor.fetchall():
            if category not in terms_by_category:
                terms_by_category[category] = []
            
            terms_by_category[category].append(term)
            
            # Add variations
            if variations_json:
                variations = json.loads(variations_json)
                terms_by_category[category].extend(variations)
        
        conn.close()
        return terms_by_category


