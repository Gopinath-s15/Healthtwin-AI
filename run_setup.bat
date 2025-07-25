@echo off
echo Setting up HealthTwin AI Medical Datasets...

echo Step 1: Installing dependencies...
pip install -r requirements.txt

echo Step 2: Creating dataset directories...
python -c "from pathlib import Path; Path('data/datasets').mkdir(parents=True, exist_ok=True)"

echo Step 3: Running dataset setup...
python scripts/setup_medical_datasets.py

echo Step 4: Testing integration...
python -c "from app.ml_pipeline.handwriting_specialist import HandwritingSpecialist; hs = HandwritingSpecialist(); print('✅ Integration successful')"

echo Setup completed!
pause
