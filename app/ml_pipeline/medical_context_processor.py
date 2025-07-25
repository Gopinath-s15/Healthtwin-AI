"""
Enhanced Medical Context Processor for Handwritten and Multi-language Prescriptions
Handles medicine name recognition, dosage instruction parsing, and medical term extraction
"""
import re
import json
from typing import Dict, List, Tuple, Any, Optional
import logging
from difflib import SequenceMatcher
import spacy
from spacy.matcher import Matcher

# Import enhanced medical NER
try:
    from .enhanced_medical_ner import EnhancedMedicalNER
    ENHANCED_NER_AVAILABLE = True
    logging.info("Enhanced Medical NER available")
except ImportError:
    ENHANCED_NER_AVAILABLE = False
    logging.warning("Enhanced Medical NER not available")

logger = logging.getLogger(__name__)

class MedicalContextProcessor:
    def __init__(self):
        """Initialize enhanced medical context processor"""
        self.nlp = None
        self._init_spacy()

        # Initialize enhanced medical NER
        self.enhanced_ner = None
        if ENHANCED_NER_AVAILABLE:
            try:
                self.enhanced_ner = EnhancedMedicalNER()
                logger.info("Enhanced Medical NER initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Enhanced Medical NER: {e}")
                self.enhanced_ner = None

        # Load medical knowledge bases (fallback)
        self.medicine_database = self._load_medicine_database()
        self.dosage_patterns = self._load_dosage_patterns()
        self.instruction_patterns = self._load_instruction_patterns()
        self.multilingual_medical_terms = self._load_multilingual_medical_terms()

        # Initialize matcher for medical entities (fallback)
        self.matcher = None
        if self.nlp:
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_medical_patterns()
    
    def _init_spacy(self):
        """Initialize spaCy NLP model"""
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
        except OSError:
            logger.warning("spaCy English model not found. Medical NER will be limited.")
            self.nlp = None
    
    def _load_medicine_database(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive medicine database with common variations"""
        return {
            # Analgesics/Antipyretics
            'paracetamol': {
                'variations': ['acetaminophen', 'tylenol', 'crocin', 'dolo', 'calpol'],
                'category': 'analgesic',
                'common_doses': ['500mg', '650mg', '1000mg'],
                'forms': ['tablet', 'syrup', 'suspension']
            },
            'ibuprofen': {
                'variations': ['brufen', 'advil', 'combiflam'],
                'category': 'nsaid',
                'common_doses': ['200mg', '400mg', '600mg'],
                'forms': ['tablet', 'syrup', 'gel']
            },
            'aspirin': {
                'variations': ['ecosprin', 'disprin'],
                'category': 'antiplatelet',
                'common_doses': ['75mg', '150mg', '325mg'],
                'forms': ['tablet', 'dispersible']
            },
            
            # Antibiotics
            'amoxicillin': {
                'variations': ['amoxil', 'novamox', 'moxikind'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg', '875mg'],
                'forms': ['capsule', 'tablet', 'syrup']
            },
            'azithromycin': {
                'variations': ['zithromax', 'azee', 'azithral'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg'],
                'forms': ['tablet', 'suspension']
            },
            'ciprofloxacin': {
                'variations': ['cipro', 'ciplox', 'cifran'],
                'category': 'antibiotic',
                'common_doses': ['250mg', '500mg', '750mg'],
                'forms': ['tablet', 'drops', 'injection']
            },
            
            # Diabetes medications
            'metformin': {
                'variations': ['glucophage', 'glycomet', 'obimet'],
                'category': 'antidiabetic',
                'common_doses': ['500mg', '850mg', '1000mg'],
                'forms': ['tablet', 'extended-release']
            },
            
            # Cardiovascular
            'atorvastatin': {
                'variations': ['lipitor', 'atorlip', 'storvas'],
                'category': 'statin',
                'common_doses': ['10mg', '20mg', '40mg', '80mg'],
                'forms': ['tablet']
            },
            
            # Gastrointestinal
            'omeprazole': {
                'variations': ['prilosec', 'omez', 'ocid'],
                'category': 'ppi',
                'common_doses': ['20mg', '40mg'],
                'forms': ['capsule', 'tablet']
            },
            'pantoprazole': {
                'variations': ['protonix', 'pantop', 'pan'],
                'category': 'ppi',
                'common_doses': ['20mg', '40mg'],
                'forms': ['tablet', 'injection']
            },
            
            # Antihistamines
            'cetirizine': {
                'variations': ['zyrtec', 'cetrizet', 'alerid'],
                'category': 'antihistamine',
                'common_doses': ['5mg', '10mg'],
                'forms': ['tablet', 'syrup', 'drops']
            },
            'loratadine': {
                'variations': ['claritin', 'lorfast', 'lorinol'],
                'category': 'antihistamine',
                'common_doses': ['10mg'],
                'forms': ['tablet', 'syrup']
            }
        }
    
    def _load_dosage_patterns(self) -> List[Dict[str, Any]]:
        """Load dosage extraction patterns"""
        return [
            {
                'pattern': r'(\d+(?:\.\d+)?)\s*(mg|gm|ml|mcg|iu|units?)',
                'type': 'dose_amount',
                'description': 'Standard dosage with units'
            },
            {
                'pattern': r'(\d+)\s*(?:tablet|tab|capsule|cap|pill)s?',
                'type': 'tablet_count',
                'description': 'Number of tablets/capsules'
            },
            {
                'pattern': r'(\d+)\s*(?:drop|drops|ml|tsp|tbsp)',
                'type': 'liquid_dose',
                'description': 'Liquid medication dosage'
            },
            {
                'pattern': r'(\d+)\s*(?:time|times)\s*(?:a\s*)?(?:day|daily)',
                'type': 'frequency',
                'description': 'Frequency per day'
            },
            {
                'pattern': r'(?:twice|2x|bid)',
                'type': 'frequency',
                'description': 'Twice daily'
            },
            {
                'pattern': r'(?:thrice|3x|tid)',
                'type': 'frequency',
                'description': 'Three times daily'
            },
            {
                'pattern': r'(?:once|1x|od|qd)',
                'type': 'frequency',
                'description': 'Once daily'
            }
        ]
    
    def _load_instruction_patterns(self) -> Dict[str, List[str]]:
        """Load instruction patterns in multiple languages"""
        return {
            'timing': {
                'english': ['morning', 'evening', 'night', 'bedtime', 'before meals', 'after meals', 'with food', 'empty stomach'],
                'hindi': ['सुबह', 'शाम', 'रात', 'खाना खाने से पहले', 'खाना खाने के बाद'],
                'tamil': ['காலை', 'மாலை', 'இரவு', 'உணவுக்கு முன்', 'உணவுக்கு பின்'],
                'telugu': ['ఉదయం', 'సాయంత్రం', 'రాత్రి', 'భోజనానికి ముందు', 'భోజనానికి తరువాత'],
                'kannada': ['ಬೆಳಿಗ್ಗೆ', 'ಸಂಜೆ', 'ರಾತ್ರಿ', 'ಊಟದ ಮೊದಲು', 'ಊಟದ ನಂತರ'],
                'malayalam': ['രാവിലെ', 'വൈകുന്നേരം', 'രാത്രി', 'ഭക്ഷണത്തിന് മുമ്പ്', 'ഭക്ഷണത്തിന് ശേഷം']
            },
            'duration': {
                'english': ['for 3 days', 'for 5 days', 'for 7 days', 'for 10 days', 'for 2 weeks', 'continue', 'as needed'],
                'hindi': ['3 दिन के लिए', '5 दिन के लिए', '7 दिन के लिए', 'जारी रखें'],
                'tamil': ['3 நாட்களுக்கு', '5 நாட்களுக்கு', '7 நாட்களுக்கு', 'தொடரவும்'],
                'telugu': ['3 రోజులు', '5 రోజులు', '7 రోజులు', 'కొనసాగించండి'],
                'kannada': ['3 ದಿನಗಳು', '5 ದಿನಗಳು', '7 ದಿನಗಳು', 'ಮುಂದುವರಿಸಿ'],
                'malayalam': ['3 ദിവസം', '5 ദിവസം', '7 ദിവസം', 'തുടരുക']
            },
            'special_instructions': {
                'english': ['with plenty of water', 'do not crush', 'shake well', 'store in refrigerator', 'avoid alcohol'],
                'hindi': ['पानी के साथ', 'कुचलें नहीं', 'अच्छी तरह हिलाएं'],
                'tamil': ['நிறைய தண்ணீருடன்', 'நசுக்க வேண்டாம்', 'நன்றாக குலுக்கவும்'],
                'telugu': ['చాలా నీటితో', 'నలిపివేయవద్దు', 'బాగా కదిలించండి'],
                'kannada': ['ಸಾಕಷ್ಟು ನೀರಿನೊಂದಿಗೆ', 'ಪುಡಿಮಾಡಬೇಡಿ', 'ಚೆನ್ನಾಗಿ ಅಲ್ಲಾಡಿಸಿ'],
                'malayalam': ['ധാരാളം വെള്ളത്തോടൊപ്പം', 'ചതച്ചരയ്ക്കരുത്', 'നന്നായി കുലുക്കുക']
            }
        }
    
    def _load_multilingual_medical_terms(self) -> Dict[str, Dict[str, str]]:
        """Load medical terms in multiple languages"""
        return {
            'medicine_forms': {
                'english': ['tablet', 'capsule', 'syrup', 'injection', 'drops', 'cream', 'ointment'],
                'hindi': ['गोली', 'कैप्सूल', 'सिरप', 'इंजेक्शन', 'बूंदें', 'क्रीम'],
                'tamil': ['மாத்திரை', 'கேப்சூல்', 'சிரப்', 'ஊசி', 'துளிகள்', 'க்ரீம்'],
                'telugu': ['మాత్ర', 'క్యాప్సూల్', 'సిరప్', 'ఇంజెక్షన్', 'చుక్కలు', 'క్రీమ్'],
                'kannada': ['ಮಾತ್ರೆ', 'ಕ್ಯಾಪ್ಸೂಲ್', 'ಸಿರಪ್', 'ಇಂಜೆಕ್ಷನ್', 'ಹನಿಗಳು', 'ಕ್ರೀಮ್'],
                'malayalam': ['ഗുളിക', 'കാപ്സൂൾ', 'സിറപ്പ്', 'കുത്തിവയ്പ്പ്', 'തുള്ളികൾ', 'ക്രീം']
            },
            'body_parts': {
                'english': ['eye', 'ear', 'nose', 'throat', 'stomach', 'head', 'chest'],
                'hindi': ['आंख', 'कान', 'नाक', 'गला', 'पेट', 'सिर', 'छाती'],
                'tamil': ['கண்', 'காது', 'மூக்கு', 'தொண்டை', 'வயிறு', 'தலை', 'மார்பு'],
                'telugu': ['కన్ను', 'చెవి', 'ముక్కు', 'గొంతు', 'కడుపు', 'తల', 'ఛాతీ'],
                'kannada': ['ಕಣ್ಣು', 'ಕಿವಿ', 'ಮೂಗು', 'ಗಂಟಲು', 'ಹೊಟ್ಟೆ', 'ತಲೆ', 'ಎದೆ'],
                'malayalam': ['കണ്ണ്', 'ചെവി', 'മൂക്ക്', 'തൊണ്ട', 'വയറ്', 'തല', 'നെഞ്ച്']
            }
        }
    
    def _setup_medical_patterns(self):
        """Setup spaCy patterns for medical entity recognition"""
        if not self.matcher:
            return
        
        # Medicine name patterns
        medicine_patterns = []
        for medicine, info in self.medicine_database.items():
            # Add main name
            medicine_patterns.append([{"LOWER": medicine.lower()}])
            # Add variations
            for variation in info['variations']:
                medicine_patterns.append([{"LOWER": variation.lower()}])
        
        self.matcher.add("MEDICINE", medicine_patterns)
        
        # Dosage patterns
        dosage_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["mg", "gm", "ml", "mcg", "iu", "units", "unit"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["tablet", "tablets", "tab", "tabs", "capsule", "capsules"]}}]
        ]
        self.matcher.add("DOSAGE", dosage_patterns)
        
        # Frequency patterns
        frequency_patterns = [
            [{"LOWER": {"IN": ["once", "twice", "thrice"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["times", "time"]}}],
            [{"LOWER": {"IN": ["daily", "morning", "evening", "night", "bedtime"]}}]
        ]
        self.matcher.add("FREQUENCY", frequency_patterns)
    
    def extract_medical_entities(self, text: str, multilingual_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract medical entities from text with multilingual support"""
        try:
            entities = {
                'medicines': [],
                'dosages': [],
                'frequencies': [],
                'instructions': [],
                'durations': [],
                'special_notes': []
            }
            
            # Process English text with spaCy if available
            if self.nlp and self.matcher:
                doc = self.nlp(text)
                matches = self.matcher(doc)
                
                for match_id, start, end in matches:
                    label = self.nlp.vocab.strings[match_id]
                    span = doc[start:end]
                    
                    if label == "MEDICINE":
                        entities['medicines'].append({
                            'text': span.text,
                            'confidence': 0.9,
                            'method': 'spacy_pattern'
                        })
                    elif label == "DOSAGE":
                        entities['dosages'].append({
                            'text': span.text,
                            'confidence': 0.8,
                            'method': 'spacy_pattern'
                        })
                    elif label == "FREQUENCY":
                        entities['frequencies'].append({
                            'text': span.text,
                            'confidence': 0.8,
                            'method': 'spacy_pattern'
                        })
            
            # Extract using regex patterns
            regex_entities = self._extract_with_regex(text)
            
            # Merge regex results
            for category, items in regex_entities.items():
                if category in entities:
                    entities[category].extend(items)
            
            # Process multilingual information if available
            if multilingual_info:
                multilingual_entities = self._extract_multilingual_entities(multilingual_info)
                
                # Merge multilingual results
                for category, items in multilingual_entities.items():
                    if category in entities:
                        entities[category].extend(items)
            
            # Deduplicate and rank entities
            for category in entities:
                entities[category] = self._deduplicate_entities(entities[category])
            
            return entities
            
        except Exception as e:
            logger.error(f"Medical entity extraction failed: {e}")
            return {
                'medicines': [],
                'dosages': [],
                'frequencies': [],
                'instructions': [],
                'durations': [],
                'special_notes': [],
                'error': str(e)
            }
    
    def _extract_with_regex(self, text: str) -> Dict[str, List[Dict]]:
        """Extract medical entities using regex patterns"""
        entities = {
            'medicines': [],
            'dosages': [],
            'frequencies': [],
            'instructions': [],
            'durations': []
        }
        
        text_lower = text.lower()
        
        # Extract medicines using fuzzy matching
        for medicine, info in self.medicine_database.items():
            all_names = [medicine] + info['variations']
            for name in all_names:
                if self._fuzzy_match(name.lower(), text_lower, threshold=0.8):
                    entities['medicines'].append({
                        'text': name,
                        'confidence': 0.7,
                        'method': 'fuzzy_match',
                        'category': info['category']
                    })
        
        # Extract dosages
        for pattern_info in self.dosage_patterns:
            matches = re.finditer(pattern_info['pattern'], text_lower, re.IGNORECASE)
            for match in matches:
                entities['dosages'].append({
                    'text': match.group(),
                    'confidence': 0.8,
                    'method': 'regex',
                    'type': pattern_info['type']
                })
        
        # Extract timing instructions
        timing_patterns = self.instruction_patterns['timing']['english']
        for pattern in timing_patterns:
            if pattern.lower() in text_lower:
                entities['instructions'].append({
                    'text': pattern,
                    'confidence': 0.7,
                    'method': 'pattern_match',
                    'type': 'timing'
                })
        
        return entities
    
    def _extract_multilingual_entities(self, multilingual_info: Dict) -> Dict[str, List[Dict]]:
        """Extract entities from multilingual OCR results"""
        entities = {
            'medicines': [],
            'dosages': [],
            'frequencies': [],
            'instructions': [],
            'durations': []
        }
        
        # Process each language result
        language_results = multilingual_info.get('language_results', {})
        
        for lang, text in language_results.items():
            if lang == 'en':
                continue  # Already processed
            
            # Extract timing instructions in regional languages
            if lang in self.instruction_patterns['timing']:
                patterns = self.instruction_patterns['timing'][lang]
                for pattern in patterns:
                    if pattern in text:
                        entities['instructions'].append({
                            'text': pattern,
                            'confidence': 0.6,
                            'method': 'multilingual_pattern',
                            'language': lang,
                            'type': 'timing'
                        })
            
            # Extract medicine forms in regional languages
            if lang in self.multilingual_medical_terms['medicine_forms']:
                forms = self.multilingual_medical_terms['medicine_forms'][lang]
                for form in forms:
                    if form in text:
                        entities['medicines'].append({
                            'text': form,
                            'confidence': 0.5,
                            'method': 'multilingual_form',
                            'language': lang,
                            'type': 'medicine_form'
                        })
        
        return entities
    
    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.8) -> bool:
        """Check if pattern fuzzy matches any part of text"""
        words = text.split()
        for word in words:
            if SequenceMatcher(None, pattern, word).ratio() >= threshold:
                return True
        return False
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities and rank by confidence"""
        if not entities:
            return []
        
        # Group by text (case-insensitive)
        groups = {}
        for entity in entities:
            key = entity['text'].lower()
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)
        
        # Select best entity from each group
        deduplicated = []
        for group in groups.values():
            best_entity = max(group, key=lambda x: x['confidence'])
            deduplicated.append(best_entity)
        
        # Sort by confidence
        return sorted(deduplicated, key=lambda x: x['confidence'], reverse=True)
    
    def process_prescription_context(self, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process prescription context from unified OCR results"""
        try:
            # Extract text from OCR results
            main_text = ocr_results.get('raw_extracted_text', '')
            multilingual_info = ocr_results.get('multilingual_info', {})
            handwriting_info = ocr_results.get('handwriting_info', {})
            
            # Use enhanced NER if available
            if self.enhanced_ner:
                logger.info("Using Enhanced Medical NER for entity extraction")

                try:
                    # Extract structured prescription data
                    enhanced_structured_data = self.enhanced_ner.extract_structured_prescription_data(main_text)
                    logger.debug(f"Enhanced structured data: {type(enhanced_structured_data)}")

                    # Extract basic entities for compatibility
                    entities = self.enhanced_ner.extract_medical_entities(main_text)
                    logger.debug(f"Enhanced entities: {type(entities)}")

                    # Convert enhanced format to legacy format for compatibility
                    entities = self._convert_enhanced_to_legacy_format(entities, enhanced_structured_data)

                except Exception as e:
                    logger.error(f"Enhanced NER processing failed: {e}")
                    logger.info("Falling back to legacy medical entity extraction")
                    entities = self.extract_medical_entities(main_text, multilingual_info)
                    enhanced_structured_data = {}

            else:
                logger.info("Using legacy medical entity extraction")
                # Extract medical entities (legacy method)
                entities = self.extract_medical_entities(main_text, multilingual_info)
            
            # Structure the prescription information
            try:
                logger.debug(f"Structuring medicines: {len(entities.get('medicines', []))} found")
                medicines_structured = self._structure_medicines(entities['medicines'], entities['dosages'])
                logger.debug(f"Medicines structured successfully: {len(medicines_structured)}")

                logger.debug(f"Structuring instructions: {len(entities.get('instructions', []))} found")
                instructions_structured = self._structure_instructions(entities['instructions'], entities['frequencies'])
                logger.debug(f"Instructions structured successfully: {len(instructions_structured)}")

                logger.debug("Calculating entity confidence...")
                confidence_scores = self._calculate_entity_confidence(entities)
                logger.debug("Entity confidence calculated successfully")

                structured_prescription = {
                    'medicines': medicines_structured,
                    'instructions': instructions_structured,
                    'special_notes': entities.get('special_notes', []),
                    'confidence_scores': confidence_scores,
                    'extraction_summary': {
                        'total_medicines': len(entities.get('medicines', [])),
                        'total_instructions': len(entities.get('instructions', [])),
                        'multilingual_detected': bool(multilingual_info.get('is_multilingual', False)),
                        'handwriting_detected': bool(handwriting_info.get('handwriting_detected', False))
                    }
                }
                logger.debug("Structured prescription created successfully")
            except Exception as e:
                logger.error(f"Error structuring prescription: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            return {
                'success': True,
                'structured_prescription': structured_prescription,
                'raw_entities': entities,
                'processing_notes': []
            }
            
        except Exception as e:
            logger.error(f"Medical context processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'structured_prescription': {},
                'raw_entities': {},
                'processing_notes': [f"Processing failed: {str(e)}"]
            }

    def _convert_enhanced_to_legacy_format(self, enhanced_entities: Dict[str, Any], structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert enhanced NER format to legacy format for compatibility"""
        try:
            logger.debug(f"Converting enhanced entities: {type(enhanced_entities)}")
            logger.debug(f"Enhanced entities keys: {enhanced_entities.keys() if isinstance(enhanced_entities, dict) else 'Not a dict'}")
            # Convert medications
            medicines = []
            for i, med in enumerate(enhanced_entities.get('medications', [])):
                try:
                    logger.debug(f"Processing medication {i}: {type(med)} - {med}")
                    # Handle different possible formats
                    if isinstance(med, dict):
                        med_text = med.get('text', '') or med.get('drug_name', '') or str(med)
                        generic_name = med.get('generic_name', '')
                        confidence = med.get('confidence', 0.0)
                        category = med.get('category', '')
                        method = med.get('method', 'enhanced_ner')
                    else:
                        med_text = str(med)
                        generic_name = ''
                        confidence = 0.5
                        category = ''
                        method = 'enhanced_ner'

                    medicines.append({
                        'name': med_text,
                        'generic_name': generic_name,
                        'confidence': confidence,
                        'category': category,
                        'method': method
                    })
                except Exception as e:
                    logger.error(f"Error processing medication {i}: {e}")
                    continue

            # Convert dosages
            dosages = []
            for i, dosage in enumerate(enhanced_entities.get('dosages', [])):
                try:
                    logger.debug(f"Processing dosage {i}: {type(dosage)} - {dosage}")
                    if isinstance(dosage, dict):
                        dosage_text = dosage.get('text', '') or str(dosage)
                        confidence = dosage.get('confidence', 0.0)
                        method = dosage.get('method', 'enhanced_ner')
                    else:
                        dosage_text = str(dosage)
                        confidence = 0.5
                        method = 'enhanced_ner'

                    dosages.append({
                        'text': dosage_text,
                        'confidence': confidence,
                        'method': method
                    })
                except Exception as e:
                    logger.error(f"Error processing dosage {i}: {e}")
                    continue

            # Convert frequencies
            frequencies = []
            for i, freq in enumerate(enhanced_entities.get('frequencies', [])):
                try:
                    logger.debug(f"Processing frequency {i}: {type(freq)} - {freq}")
                    if isinstance(freq, dict):
                        freq_text = freq.get('text', '') or str(freq)
                        confidence = freq.get('confidence', 0.0)
                        method = freq.get('method', 'enhanced_ner')
                    else:
                        freq_text = str(freq)
                        confidence = 0.5
                        method = 'enhanced_ner'

                    frequencies.append({
                        'text': freq_text,
                        'confidence': confidence,
                        'method': method
                    })
                except Exception as e:
                    logger.error(f"Error processing frequency {i}: {e}")
                    continue

            # Convert instructions
            instructions = []
            for i, instr in enumerate(enhanced_entities.get('instructions', [])):
                try:
                    logger.debug(f"Processing instruction {i}: {type(instr)} - {instr}")
                    if isinstance(instr, dict):
                        instr_text = instr.get('text', '') or str(instr)
                        confidence = instr.get('confidence', 0.0)
                        method = instr.get('method', 'enhanced_ner')
                    else:
                        instr_text = str(instr)
                        confidence = 0.5
                        method = 'enhanced_ner'

                    instructions.append({
                        'text': instr_text,
                        'confidence': confidence,
                        'method': method
                    })
                except Exception as e:
                    logger.error(f"Error processing instruction {i}: {e}")
                    continue

            logger.debug("Creating return dictionary...")
            result = {
                'medicines': medicines,
                'dosages': dosages,
                'frequencies': frequencies,
                'instructions': instructions,
                'special_notes': [],
                'enhanced_data': structured_data  # Include enhanced data for reference
            }
            logger.debug(f"Return dictionary created successfully: {len(result)} keys")
            return result

        except Exception as e:
            logger.error(f"Failed to convert enhanced format: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'medicines': [],
                'dosages': [],
                'frequencies': [],
                'instructions': [],
                'special_notes': []
            }
    
    def _structure_medicines(self, medicines: List[Dict], dosages: List[Dict]) -> List[Dict]:
        """Structure medicine information with dosages"""
        structured = []
        
        for medicine in medicines[:10]:  # Limit to 10 medicines
            # Handle different medicine formats
            med_name = medicine.get('name', '') or medicine.get('text', '') or str(medicine)
            med_confidence = medicine.get('confidence', 0.0) if isinstance(medicine, dict) else 0.5
            med_category = medicine.get('category', 'unknown') if isinstance(medicine, dict) else 'unknown'

            med_info = {
                'name': med_name,
                'confidence': med_confidence,
                'category': med_category,
                'dosage': 'Not specified',
                'form': 'Not specified'
            }
            
            # Try to find matching dosage
            for dosage in dosages:
                try:
                    if abs(medicines.index(medicine) - dosages.index(dosage)) <= 2:  # Nearby in text
                        dosage_text = dosage.get('text', '') if isinstance(dosage, dict) else str(dosage)
                        if dosage_text:
                            med_info['dosage'] = dosage_text
                            break
                except (ValueError, TypeError):
                    # Handle cases where index() fails
                    dosage_text = dosage.get('text', '') if isinstance(dosage, dict) else str(dosage)
                    if dosage_text:
                        med_info['dosage'] = dosage_text
                        break
            
            structured.append(med_info)
        
        return structured
    
    def _structure_instructions(self, instructions: List[Dict], frequencies: List[Dict]) -> List[Dict]:
        """Structure instruction information"""
        structured = []
        
        for instruction in instructions:
            inst_info = {
                'instruction': instruction['text'],
                'type': instruction.get('type', 'general'),
                'language': instruction.get('language', 'english'),
                'confidence': instruction['confidence']
            }
            structured.append(inst_info)
        
        for frequency in frequencies:
            freq_info = {
                'instruction': frequency['text'],
                'type': 'frequency',
                'language': 'english',
                'confidence': frequency['confidence']
            }
            structured.append(freq_info)
        
        return structured
    
    def _calculate_entity_confidence(self, entities: Dict[str, List]) -> Dict[str, float]:
        """Calculate confidence scores for different entity types"""
        confidence_scores = {}

        for category, entity_list in entities.items():
            if entity_list:
                try:
                    # Handle different entity formats
                    confidences = []
                    for e in entity_list:
                        if isinstance(e, dict):
                            confidence = e.get('confidence', 0.5)
                        else:
                            # If entity is not a dict (e.g., string), assign default confidence
                            confidence = 0.5
                        confidences.append(confidence)

                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    confidence_scores[category] = avg_confidence
                except Exception as e:
                    logger.warning(f"Error calculating confidence for {category}: {e}")
                    confidence_scores[category] = 0.5  # Default confidence
            else:
                confidence_scores[category] = 0.0

        return confidence_scores
