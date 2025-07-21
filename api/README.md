# HealthTwin AI API

This folder documents the REST API endpoints for the HealthTwin AI backend.

## Endpoints

### 1. Register Patient
- **POST** `/register`
- **Body:**
  ```json
  {
    "phone": "9876543210",
    "name": "Amit Kumar"
  }
  ```
- **Response:**
  ```json
  {
    "healthtwin_id": "<uuid>"
  }
  ```

### 2. Upload Prescription
- **POST** `/upload-prescription?patient_id=<healthtwin_id>`
- **Form Data:**
  - `file`: (image file, e.g. JPG/PNG)
- **Response:**
  ```json
  {
    "status": "success",
    "file": "uploads/<filename>"
  }
  ```

### 3. Get Timeline
- **GET** `/timeline/<healthtwin_id>`
- **Response:**
  ```json
  {
    "timeline": [
      {
        "doctor": "Dr. Example",
        "diagnosis": "Diagnosis Example",
        "medications": "Paracetamol, Amoxicillin",
        "img": "uploads/<filename>",
        "created_at": "2025-07-20 17:50:00"
      },
      ...
    ]
  }
  ```

## Usage
- Use these endpoints from the frontend or with tools like Postman/cURL.
- The backend must be running (see main.py for instructions). 