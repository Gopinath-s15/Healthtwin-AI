@echo off
echo Installing missing dependencies...

pip install fuzzywuzzy python-Levenshtein
pip install rapidfuzz
pip install spacy
python -m spacy download en_core_web_sm
pip install medspacy
pip install transformers torch
pip install easyocr
pip install scikit-image scipy

echo Dependencies installed successfully!
pause