"""
Enhanced Multi-language OCR Engine for Indian Medical Prescriptions
Handles mixed-language prescriptions with English medicine names and regional language instructions
"""
import cv2
import numpy as np
from PIL import Image
import paddleocr
import re
from typing import Dict, List, Tuple, Any, Optional
import logging
import json

# Try to import optional dependencies with proper error handling
try:
    from langdetect import detect
    # Handle different versions of langdetect
    try:
        from langdetect import LangDetectError
    except ImportError:
        # Create a custom exception for older versions
        class LangDetectError(Exception):
            pass
    LANGDETECT_AVAILABLE = True
    logging.info("Language detection available")
except ImportError as e:
    LANGDETECT_AVAILABLE = False
    logging.warning(f"langdetect not available - language detection will be limited: {e}")
    # Create dummy classes for fallback
    class LangDetectError(Exception):
        pass
    def detect(text):
        return 'en'  # Default fallback

# Try multiple translation libraries for better compatibility
GOOGLETRANS_AVAILABLE = False
translator_type = None
Translator = None
GoogleTranslator = None

# Try different translation libraries in order of preference
try:
    # Try deep_translator first (more stable)
    from deep_translator import GoogleTranslator  # type: ignore
    GOOGLETRANS_AVAILABLE = True
    translator_type = 'deep_translator'
    logging.info("Deep Translator (Google) available")
except ImportError:
    try:
        # Fallback to googletrans (may have compatibility issues)
        from googletrans import Translator  # type: ignore
        GOOGLETRANS_AVAILABLE = True
        translator_type = 'googletrans'
        logging.info("Google Translate (googletrans) available")
    except ImportError as e:
        # No translation library available
        GOOGLETRANS_AVAILABLE = False
        logging.warning(f"No translation library available - translation features will be limited: {e}")

        # Create dummy classes for fallback
        class DummyTranslator:
            def translate(self, text, src='auto', dest='en'):  # type: ignore
                return type('obj', (object,), {'text': f'[Translation not available: {text}]'})

            def __call__(self, source='auto', target='en'):
                return self

        Translator = DummyTranslator
        GoogleTranslator = DummyTranslator

logger = logging.getLogger(__name__)

class MultilingualOCREngine:
    def __init__(self):
        """Initialize multi-language OCR engines"""
        self.ocr_engines = {}
        self.translator = None

        # Initialize translator based on available library
        if GOOGLETRANS_AVAILABLE:
            if translator_type == 'googletrans':
                self.translator = Translator()
            elif translator_type == 'deep_translator':
                self.translator = GoogleTranslator

        # Language mappings for Indian languages
        self.language_codes = {
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'gu': 'Gujarati',
            'bn': 'Bengali',
            'pa': 'Punjabi',
            'or': 'Odia',
            'as': 'Assamese',
            'en': 'English'
        }

        # Medical terms in different languages for better recognition
        self.medical_terms_multilang = self._load_multilingual_medical_terms()

        # Common transliteration patterns
        self.transliteration_patterns = self._load_transliteration_patterns()

        # Initialize OCR engines
        self._init_ocr_engines()

    def _init_ocr_engines(self):
        """Initialize PaddleOCR engines for different languages"""
        try:
            logger.info("Initializing multi-language OCR engines...")

            # Primary languages for Indian medical prescriptions
            # Start with languages that are more likely to be supported
            primary_languages = ['en', 'hi']  # English and Hindi are most commonly supported
            secondary_languages = ['ta', 'te']  # Tamil and Telugu
            experimental_languages = ['kn', 'ml', 'gu', 'bn']  # May not be available in all PaddleOCR versions

            # Try primary languages first
            for lang in primary_languages:
                self._try_load_ocr_engine(lang)

            # Try secondary languages
            for lang in secondary_languages:
                self._try_load_ocr_engine(lang)

            # Try experimental languages (don't fail if these don't work)
            for lang in experimental_languages:
                self._try_load_ocr_engine(lang, critical=False)

            # Ensure we have at least English
            if 'en' not in self.ocr_engines:
                logger.warning("English OCR not available, trying fallback initialization...")
                self._try_load_ocr_engine('en', critical=True)

            if not self.ocr_engines:
                logger.error("No OCR engines could be initialized")
                raise Exception("Failed to initialize any OCR engines")

            logger.info(f"Successfully initialized OCR engines for languages: {list(self.ocr_engines.keys())}")

        except Exception as e:
            logger.error(f"Failed to initialize OCR engines: {e}")
            # Last resort fallback
            try:
                logger.info("Attempting last resort English-only OCR initialization...")
                self.ocr_engines = {'en': paddleocr.PaddleOCR(use_angle_cls=True, lang='en')}
                logger.info("Fallback English OCR initialized successfully")
            except Exception as e2:
                logger.error(f"Even fallback OCR failed: {e2}")
                self.ocr_engines = {}

    def _try_load_ocr_engine(self, lang: str, critical: bool = True):
        """Try to load a specific OCR engine"""
        try:
            logger.info(f"Loading OCR engine for {self.language_codes.get(lang, lang)}...")
            ocr_engine = paddleocr.PaddleOCR(
                use_angle_cls=True,
                lang=lang
            )
            self.ocr_engines[lang] = ocr_engine
            logger.info(f"✓ Loaded OCR engine for {self.language_codes.get(lang, lang)}")
            return True
        except Exception as e:
            if critical:
                logger.error(f"✗ Failed to load critical OCR engine for {lang}: {e}")
            else:
                logger.warning(f"⚠ Failed to load optional OCR engine for {lang}: {e}")
            return False

    def _load_multilingual_medical_terms(self) -> Dict[str, List[str]]:
        """Load medical terms in different languages"""
        return {
            'en': [
                'tablet', 'capsule', 'syrup', 'injection', 'drops', 'cream', 'ointment',
                'mg', 'ml', 'gm', 'dose', 'twice', 'daily', 'morning', 'evening', 'night',
                'before', 'after', 'meals', 'paracetamol', 'ibuprofen', 'aspirin'
            ],
            'hi': [
                'गोली', 'कैप्सूल', 'सिरप', 'इंजेक्शन', 'बूंदें', 'क्रीम',
                'दवा', 'सुबह', 'शाम', 'रात', 'खाना', 'पहले', 'बाद', 'दिन'
            ],
            'ta': [
                'மாத்திரை', 'கேப்சூல்', 'சிரப்', 'ஊசி', 'துளிகள்', 'க்ரீம்',
                'மருந்து', 'காலை', 'மாலை', 'இரவு', 'உணவு', 'முன்', 'பின்', 'நாள்'
            ],
            'te': [
                'మాత్ర', 'క్యాప్సూల్', 'సిరప్', 'ఇంజెక్షన్', 'చుక్కలు', 'క్రీమ్',
                'మందు', 'ఉదయం', 'సాయంత్రం', 'రాత్రి', 'భోజనం', 'ముందు', 'తరువాత', 'రోజు'
            ]
        }

    def _load_transliteration_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load common transliteration patterns for mixed-language text"""
        return {
            'hi_to_en': {
                'गोली': 'tablet',
                'दवा': 'medicine',
                'सुबह': 'morning',
                'शाम': 'evening',
                'रात': 'night',
                'खाना': 'food',
                'पहले': 'before',
                'बाद': 'after'
            },
            'ta_to_en': {
                'மாத்திரை': 'tablet',
                'மருந்து': 'medicine',
                'காலை': 'morning',
                'மாலை': 'evening',
                'இரவு': 'night',
                'உணவு': 'food',
                'முன்': 'before',
                'பின்': 'after'
            },
            'te_to_en': {
                'మాత్ర': 'tablet',
                'మందు': 'medicine',
                'ఉదయం': 'morning',
                'సాయంత్రం': 'evening',
                'రాత్రి': 'night',
                'భోజనం': 'food',
                'ముందు': 'before',
                'తరువాత': 'after'
            }
        }

    def preprocess_for_multilingual(self, image_path: str) -> np.ndarray:
        """Enhanced preprocessing for multi-language text"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)

            # Enhance contrast for better multi-language recognition
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)

            # Adaptive thresholding optimized for mixed scripts
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 13, 4
            )

            # Morphological operations to improve character connectivity
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            logger.error(f"Multi-language preprocessing failed: {e}")
            return None

    def detect_languages_in_image(self, image: np.ndarray) -> List[str]:
        """Detect languages present in the image"""
        detected_languages = []

        try:
            # Try English first (most medical prescriptions have English)
            if 'en' in self.ocr_engines:
                eng_result = self.ocr_engines['en'].ocr(image, cls=True)
                if eng_result and eng_result[0]:
                    eng_text = self._extract_text_from_result(eng_result)
                    if eng_text and len(eng_text.strip()) > 10:
                        detected_languages.append('en')

            # Try regional languages
            for lang in ['hi', 'ta', 'te', 'kn', 'ml']:
                if lang in self.ocr_engines:
                    try:
                        result = self.ocr_engines[lang].ocr(image, cls=True)
                        if result and result[0]:
                            text = self._extract_text_from_result(result)
                            if text and len(text.strip()) > 5:
                                # Check if text contains language-specific characters
                                if self._contains_language_script(text, lang):
                                    detected_languages.append(lang)
                    except Exception as e:
                        logger.warning(f"Language detection failed for {lang}: {e}")
                        continue

            return detected_languages if detected_languages else ['en']

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['en']  # Fallback to English

    def _contains_language_script(self, text: str, language: str) -> bool:
        """Check if text contains script specific to the language"""
        script_ranges = {
            'hi': (0x0900, 0x097F),  # Devanagari
            'ta': (0x0B80, 0x0BFF),  # Tamil
            'te': (0x0C00, 0x0C7F),  # Telugu
            'kn': (0x0C80, 0x0CFF),  # Kannada
            'ml': (0x0D00, 0x0D7F),  # Malayalam
        }

        if language not in script_ranges:
            return False

        start, end = script_ranges[language]

        for char in text:
            if start <= ord(char) <= end:
                return True

        return False

    def _extract_text_from_result(self, ocr_result: List) -> str:
        """Extract text from PaddleOCR result"""
        text_lines = []
        for line in ocr_result[0]:
            if len(line) >= 2:
                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                text_lines.append(text)
        return '\n'.join(text_lines)

    def extract_multilingual_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using multiple language OCR engines"""
        try:
            # Preprocess image
            processed_img = self.preprocess_for_multilingual(image_path)
            if processed_img is None:
                return self._create_error_response("Image preprocessing failed")

            # Detect languages in the image
            detected_languages = self.detect_languages_in_image(processed_img)
            logger.info(f"Detected languages: {detected_languages}")

            # Extract text for each detected language
            language_results = {}
            confidence_scores = {}

            for lang in detected_languages:
                if lang in self.ocr_engines:
                    try:
                        result = self.ocr_engines[lang].ocr(processed_img, cls=True)
                        if result and result[0]:
                            text, confidence = self._process_ocr_result(result)
                            if text:
                                language_results[lang] = text
                                confidence_scores[lang] = confidence
                                logger.info(f"Extracted {len(text)} chars in {self.language_codes.get(lang, lang)}")
                    except Exception as e:
                        logger.warning(f"OCR failed for {lang}: {e}")
                        continue

            if not language_results:
                return self._create_error_response("No text extracted from any language")

            # Combine and process multilingual results
            combined_text = self._combine_multilingual_results(language_results)
            translated_text = self._translate_regional_to_english(language_results)

            # Calculate overall confidence
            overall_confidence = max(confidence_scores.values()) if confidence_scores else 0.0

            return {
                'success': True,
                'detected_languages': detected_languages,
                'language_results': language_results,
                'confidence_scores': confidence_scores,
                'combined_text': combined_text,
                'translated_text': translated_text,
                'overall_confidence': overall_confidence,
                'is_multilingual': len(detected_languages) > 1
            }

        except Exception as e:
            logger.error(f"Multilingual OCR failed: {e}")
            return self._create_error_response(f"Multilingual OCR error: {str(e)}")

    def _process_ocr_result(self, ocr_result: List) -> Tuple[str, float]:
        """Process PaddleOCR result and calculate confidence"""
        text_lines = []
        confidences = []

        for line in ocr_result[0]:
            if len(line) >= 2:
                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                confidence = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 0.8

                text_lines.append(text)
                confidences.append(confidence)

        combined_text = '\n'.join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return combined_text, avg_confidence

    def _combine_multilingual_results(self, language_results: Dict[str, str]) -> str:
        """Intelligently combine multilingual OCR results"""
        if not language_results:
            return ""

        combined_lines = []

        # Prioritize English for medicine names
        if 'en' in language_results:
            eng_lines = language_results['en'].split('\n')
            combined_lines.extend(eng_lines)

        # Add unique lines from regional languages
        for lang, text in language_results.items():
            if lang != 'en':
                regional_lines = text.split('\n')
                for line in regional_lines:
                    if line.strip() and not any(self._similar_text(line, existing) for existing in combined_lines):
                        combined_lines.append(f"[{self.language_codes.get(lang, lang)}] {line}")

        return '\n'.join(combined_lines)

    def _translate_regional_to_english(self, language_results: Dict[str, str]) -> Dict[str, str]:
        """Translate regional language text to English"""
        translations = {}

        for lang, text in language_results.items():
            if lang != 'en' and text.strip():
                try:
                    # Use local transliteration patterns first
                    transliterated = self._apply_transliteration_patterns(text, lang)
                    if transliterated != text:
                        translations[f"{lang}_transliterated"] = transliterated

                    # Use translation service if available
                    if GOOGLETRANS_AVAILABLE and self.translator:
                        try:
                            if translator_type == 'googletrans':
                                translated = self.translator.translate(text, src=lang, dest='en')
                                if translated and translated.text:
                                    translations[f"{lang}_translated"] = translated.text
                            elif translator_type == 'deep_translator':
                                translated = self.translator(source=lang, target='en').translate(text)
                                if translated:
                                    translations[f"{lang}_translated"] = translated
                        except Exception as e:
                            logger.warning(f"Translation service failed for {lang}: {e}")
                            translations[f"{lang}_translation_error"] = str(e)
                    else:
                        translations[f"{lang}_translated"] = "[Translation service not available]"

                except Exception as e:
                    logger.warning(f"Translation failed for {lang}: {e}")
                    translations[f"{lang}_translation_error"] = str(e)

        return translations

    def _apply_transliteration_patterns(self, text: str, language: str) -> str:
        """Apply transliteration patterns for common medical terms"""
        pattern_key = f"{language}_to_en"
        if pattern_key not in self.transliteration_patterns:
            return text

        patterns = self.transliteration_patterns[pattern_key]
        transliterated = text

        for regional_term, english_term in patterns.items():
            transliterated = transliterated.replace(regional_term, english_term)

        return transliterated

    def _similar_text(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two text lines are similar"""
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())

        if not text1_clean or not text2_clean:
            return False

        # Jaccard similarity
        set1 = set(text1_clean.split())
        set2 = set(text2_clean.split())

        if not set1 or not set2:
            return False

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return (intersection / union) >= threshold

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error': error_message,
            'detected_languages': [],
            'language_results': {},
            'confidence_scores': {},
            'combined_text': '',
            'translated_text': {},
            'overall_confidence': 0.0,
            'is_multilingual': False
        }
