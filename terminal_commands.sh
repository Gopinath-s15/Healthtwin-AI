# Navigate to project root (adjust path as needed)
cd "c:\Users\virat\OneDrive\Desktop\HealthTwin - Backend"

# Activate Python virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/Linux/macOS:
# source venv/bin/activate

# Start FastAPI backend server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000