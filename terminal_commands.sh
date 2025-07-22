# Navigate to project root
cd "C:\Users\virat\OneDrive\Desktop\HealthTwin - AI"

# Activate Python virtual environment
venv\Scripts\activate

# Start FastAPI backend server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
