# HealthTwin AI - API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All API responses follow this structure:

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error description"
}
```

## Authentication Endpoints

### Register Patient
**POST** `/auth/patient/register`

Register a new patient with authentication.

**Request Body:**
```json
{
  "phone": "1234567890",
  "name": "John Doe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "patient",
  "user_id": "uuid-here"
}
```

### Patient Login
**POST** `/auth/patient/login`

Authenticate an existing patient.

**Request Body:**
```json
{
  "patient_id": "uuid-here",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "patient",
  "user_id": "uuid-here"
}
```

### Register Doctor
**POST** `/auth/doctor/register`

Register a new healthcare provider.

**Request Body:**
```json
{
  "doctor_id": "DR001",
  "name": "Dr. Jane Smith",
  "specialization": "Cardiology",
  "license_number": "LIC123456",
  "password": "doctorpassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "doctor",
  "user_id": "DR001"
}
```

### Doctor Login
**POST** `/auth/doctor/login`

Authenticate an existing doctor.

**Request Body:**
```json
{
  "doctor_id": "DR001",
  "password": "doctorpassword123"
}
```

## Patient Endpoints

### Get Patient Profile
**GET** `/patient/profile`

Get the authenticated patient's profile information.

**Headers:**
```
Authorization: Bearer <patient-token>
```

**Response:**
```json
{
  "patient": {
    "id": "uuid-here",
    "phone": "1234567890",
    "name": "John Doe",
    "date_of_birth": null,
    "gender": null,
    "address": null,
    "emergency_contact": null,
    "blood_type": null,
    "allergies": null,
    "chronic_conditions": null,
    "preferred_language": "en"
  }
}
```

### Get Patient Timeline
**GET** `/patient/timeline`

Get the authenticated patient's complete medical timeline.

**Headers:**
```
Authorization: Bearer <patient-token>
```

**Response:**
```json
{
  "patient": { ... },
  "timeline": [
    {
      "id": 1,
      "doctor_name": "Dr. Smith",
      "diagnosis": "Hypertension",
      "medications": "Lisinopril 10mg",
      "prescription_img": "prescription-uuid.jpg",
      "created_at": "2024-01-15T10:30:00Z",
      "notes": "Follow up in 2 weeks"
    }
  ]
}
```

### Upload Prescription
**POST** `/patient/upload-prescription`

Upload a prescription image for the authenticated patient.

**Headers:**
```
Authorization: Bearer <patient-token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <image-file> (JPG, PNG, GIF, BMP, TIFF, WebP, max 10MB)
```

**Response:**
```json
{
  "status": "success",
  "timeline_id": 123,
  "file": "uuid-filename.jpg",
  "message": "Prescription uploaded successfully"
}
```

## Doctor Endpoints

### Search Patients
**GET** `/doctor/patients`

Search for patients accessible to the authenticated doctor.

**Headers:**
```
Authorization: Bearer <doctor-token>
```

**Query Parameters:**
- `search` (optional): Search term for patient name, phone, or ID

**Response:**
```json
{
  "patients": [
    {
      "id": "uuid-here",
      "name": "John Doe",
      "phone": "1234567890",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Patient Timeline (Doctor View)
**GET** `/doctor/patient/{patient_id}/timeline`

Get a patient's timeline from the doctor's perspective.

**Headers:**
```
Authorization: Bearer <doctor-token>
```

**Path Parameters:**
- `patient_id`: Patient UUID

**Response:**
```json
{
  "patient": { ... },
  "timeline": [
    {
      "id": 1,
      "doctor_name": "Dr. Smith",
      "diagnosis": "Hypertension",
      "medications": "Lisinopril 10mg",
      "prescription_img": "prescription-uuid.jpg",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Add Medical Entry
**POST** `/doctor/patient/{patient_id}/timeline`

Add a new medical entry to a patient's timeline.

**Headers:**
```
Authorization: Bearer <doctor-token>
Content-Type: application/json
```

**Path Parameters:**
- `patient_id`: Patient UUID

**Request Body:**
```json
{
  "diagnosis": "Hypertension",
  "medications": "Lisinopril 10mg daily",
  "dosage_instructions": "Take once daily with food",
  "follow_up_date": "2024-02-15",
  "notes": "Patient responding well to treatment"
}
```

**Response:**
```json
{
  "status": "success",
  "timeline_id": 123,
  "message": "Medical entry added successfully"
}
```

## Legacy Endpoints (Backward Compatibility)

### Register Patient (Legacy)
**POST** `/register`

Legacy patient registration without password.

**Request Body:**
```json
{
  "phone": "1234567890",
  "name": "John Doe"
}
```

### Upload Prescription (Legacy)
**POST** `/upload-prescription?patient_id={uuid}`

Legacy prescription upload with query parameter.

### Get Timeline (Legacy)
**GET** `/timeline/{patient_id}`

Legacy timeline retrieval.

## System Endpoints

### Health Check
**GET** `/health`

Check system health and status.

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "uploads_dir": "exists",
  "auth_service": "active",
  "version": "2.0.0"
}
```

### Root Endpoint
**GET** `/`

Basic API information.

**Response:**
```json
{
  "message": "HealthTwin AI API is running",
  "version": "2.0.0",
  "features": ["authentication", "ai-processing", "multi-language"]
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute per IP
- **File upload endpoints**: 10 requests per minute per user
- **General endpoints**: 100 requests per minute per user

## File Upload Specifications

### Supported Formats
- JPG, JPEG
- PNG
- GIF
- BMP
- TIFF
- WebP

### Limitations
- Maximum file size: 10MB
- Maximum files per request: 1
- File validation: MIME type and extension checking

## Security Considerations

1. **Always use HTTPS in production**
2. **Store JWT tokens securely** (httpOnly cookies recommended)
3. **Implement proper CORS policies**
4. **Validate all input data**
5. **Use environment variables for sensitive configuration**
6. **Implement rate limiting and monitoring**
7. **Regular security audits and updates**

## SDK and Client Libraries

Coming soon:
- Python SDK
- JavaScript/TypeScript SDK
- Mobile SDKs (iOS/Android)

## Interactive API Documentation

When running the backend server, you can access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Additional Resources

- **Main Repository**: [Healthtwin-AI on GitHub](https://github.com/yourusername/Healthtwin-AI)
- **Report Issues**: [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues)
- **API Discussions**: [GitHub Discussions](https://github.com/yourusername/Healthtwin-AI/discussions)
- **Contribute**: [Contributing Guidelines](https://github.com/yourusername/Healthtwin-AI/blob/main/docs/CONTRIBUTING.md)
