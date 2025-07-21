# HealthTwin AI - Intelligent Medical Records Platform

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/yourusername/Healthtwin-AI)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/Healthtwin-AI?style=social)](https://github.com/yourusername/Healthtwin-AI/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/yourusername/Healthtwin-AI?style=social)](https://github.com/yourusername/Healthtwin-AI/network/members)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18.2.0-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)

## 🏥 Overview

HealthTwin AI is an advanced medical records management platform that combines secure patient data management with AI-powered prescription processing. The platform provides a comprehensive digital twin for patients' medical history, enabling healthcare providers to make informed decisions while maintaining the highest standards of data security and privacy.

## ✨ Key Features

### 🔐 **Enhanced Authentication System**
- **Secure Patient Authentication**: JWT-based authentication with bcrypt password hashing
- **Role-Based Access Control**: Separate authentication for patients and healthcare providers
- **Session Management**: Secure token-based sessions with configurable expiration

### 👨‍⚕️ **Doctor Interface**
- **Patient Search & Management**: Advanced search capabilities for healthcare providers
- **Medical Record Access**: Secure access to patient timelines and medical history
- **Treatment Documentation**: Add and manage medical entries, prescriptions, and follow-ups

### 🤖 **AI-Powered Features** (Ready for Integration)
- **OCR Processing**: Extract text from handwritten prescriptions
- **NLP Analysis**: Parse medical terminology and medication information
- **Drug Interaction Alerts**: Intelligent monitoring for medication conflicts
- **Health Insights**: AI-generated recommendations and trend analysis

### 📱 **Modern Web Interface**
- **Responsive Design**: Mobile-friendly React frontend
- **Real-time Updates**: Live data synchronization
- **Intuitive UX**: User-friendly interface for both patients and healthcare providers

### 🔒 **Security & Compliance**
- **HIPAA-Ready Architecture**: Designed with healthcare compliance in mind
- **Data Encryption**: Secure storage and transmission of sensitive medical data
- **Audit Logging**: Comprehensive logging for compliance and monitoring

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **npm or yarn**
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Healthtwin-AI.git
   cd Healthtwin-AI
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run database migration
   python migrate_database.py
   
   # Start the backend server
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access the Application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
Healthtwin-AI/
├── app/                          # FastAPI Backend
│   ├── main.py                   # Main application file
│   ├── auth.py                   # Authentication & authorization
│   ├── database.py               # Database management
│   └── __init__.py
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── App.js               # Main React component
│   │   ├── index.js             # Entry point
│   │   └── index.css            # Styles
│   ├── public/                  # Static assets
│   ├── package.json             # Node.js dependencies
│   └── README.md                # Frontend documentation
├── docs/                        # Documentation
│   ├── API.md                   # API documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── CONTRIBUTING.md          # Contribution guidelines
├── scripts/                     # Utility scripts
│   ├── migrate_database.py      # Database migration
│   └── test_enhanced_api.py     # API testing
├── docker/                      # Docker configuration
│   ├── Dockerfile.backend       # Backend container
│   ├── Dockerfile.frontend      # Frontend container
│   └── docker-compose.yml       # Multi-container setup
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── LICENSE                      # License information
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./healthtwin.db

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads

# AI Services (Optional)
OPENAI_API_KEY=your-openai-key
OCR_SERVICE_URL=your-ocr-service-url
```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/patient/register` | Register new patient |
| POST | `/auth/patient/login` | Patient login |
| POST | `/auth/doctor/register` | Register new doctor |
| POST | `/auth/doctor/login` | Doctor login |

### Patient Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patient/profile` | Get patient profile |
| GET | `/patient/timeline` | Get patient timeline |
| POST | `/patient/upload-prescription` | Upload prescription |

### Doctor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/doctor/patients` | Search patients |
| GET | `/doctor/patient/{id}/timeline` | Get patient timeline |
| POST | `/doctor/patient/{id}/timeline` | Add medical entry |

For detailed API documentation, see [docs/API.md](docs/API.md)

## 🧪 Testing

```bash
# Run backend tests
python test_enhanced_api.py

# Run frontend tests
cd frontend
npm test

# Run all tests
npm run test:all
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -f docker/Dockerfile.backend -t healthtwin-backend .
docker build -f docker/Dockerfile.frontend -t healthtwin-frontend ./frontend
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Healthtwin-AI/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/Healthtwin-AI/wiki)

## 🗺️ Roadmap

- [ ] **Phase 1**: ✅ Enhanced Authentication & Doctor Interface
- [ ] **Phase 2**: 🔄 AI-Powered Prescription Processing
- [ ] **Phase 3**: 📋 Intelligent Medical Analysis
- [ ] **Phase 4**: 🌐 Multi-language Support
- [ ] **Phase 5**: 📊 Advanced Analytics Dashboard
- [ ] **Phase 6**: 📱 Mobile Application

## 👥 Team

- **Backend Development**: FastAPI, SQLite, Authentication
- **Frontend Development**: React, Modern UI/UX
- **AI Integration**: OCR, NLP, Medical Analysis
- **DevOps**: Docker, CI/CD, Deployment

---

**Built with ❤️ for better healthcare management**
