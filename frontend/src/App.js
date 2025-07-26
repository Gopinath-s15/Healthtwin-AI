import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingMode, setProcessingMode] = useState('standard');
  const [dragActive, setDragActive] = useState(false);

  const [currentView, setCurrentView] = useState('patient'); 
  const [patientId, setPatientId] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [patientData, setPatientData] = useState(null);
  const [prescriptionPhotos, setPrescriptionPhotos] = useState([]);


  const [currentPage, setCurrentPage] = useState('landing'); 
  const [darkMode, setDarkMode] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userCredentials, setUserCredentials] = useState({ email: '', password: '' });
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    fetchTimeline();
    generateSamplePatientId();
  }, []);

  const generatePatientId = () => {
    const prefix = 'HT';
    const numbers = Math.floor(100000 + Math.random() * 900000);
    return `${prefix}${numbers}`;
  };

  const generateSamplePatientId = () => {
    if (!patientId) {
      setPatientId(generatePatientId());
    }
  };

  
  const sendOtp = async () => {
    if (!phoneNumber || phoneNumber.length !== 10) {
      alert('Please enter a valid 10-digit phone number');
      return;
    }

    const generatedOtp = Math.floor(1000 + Math.random() * 9000);
    console.log(`OTP sent to ${phoneNumber}: ${generatedOtp}`); 
    alert(`OTP sent to ${phoneNumber}: ${generatedOtp} (Demo mode)`);
    setShowOtpInput(true);
  };

  const verifyOtp = () => {
    if (otp.length === 4) {
      
      const retrievedId = generatePatientId();
      setPatientId(retrievedId);
      alert(`Your Patient ID is: ${retrievedId}`);
      setShowOtpInput(false);
      setOtp('');
      setPhoneNumber('');
    } else {
      alert('Please enter a valid 4-digit OTP');
    }
  };

  const searchPatientById = async (searchId) => {
   
    
    const mockPatientData = {
      id: searchId,
      name: 'John Doe',
      age: 35,
      phone: '+91 98765 43210',
      lastVisit: '2024-01-15',
      medications: [
        { name: 'Paracetamol', dosage: '500mg', frequency: 'Twice daily', prescribed: '2024-01-15' },
        { name: 'Vitamin D3', dosage: '1000 IU', frequency: 'Once daily', prescribed: '2024-01-10' }
      ],
      prescriptionHistory: [
        { date: '2024-01-15', doctor: 'Dr. Smith', condition: 'Fever', medications: 2 },
        { date: '2024-01-10', doctor: 'Dr. Johnson', condition: 'Routine checkup', medications: 1 }
      ]
    };

    setPatientData(mockPatientData);
  };



  const fetchTimeline = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/patient/timeline`);
      if (response.data.success) {
        setTimeline(response.data.timeline);
      }
    } catch (error) {
      console.error('Failed to fetch timeline:', error);
    }
  };

 
  const handleLogin = (e) => {
    e.preventDefault();
   
    if (userCredentials.email && userCredentials.password) {
      setIsAuthenticated(true);
      setCurrentPage('patientId');
    }
  };

  const handleRegister = (e) => {
    e.preventDefault();
  
    if (userCredentials.email && userCredentials.password) {
      setIsAuthenticated(true);
      setCurrentPage('patientId');
    }
  };

 
  const navigateToHome = () => {
    setCurrentPage('home');
  };

  const navigateToResults = () => {
    setCurrentPage('results');
  };

  const navigateToPatientId = () => {
    setCurrentPage('patientId');
  };

  const navigateToLanding = () => {
    setCurrentPage('landing');
    setIsAuthenticated(false);
  };

  const handleFileSelect = (selectedFile) => {
    if (selectedFile) {
     
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'application/pdf'];
      const maxSize = 10 * 1024 * 1024; // 10MB

      if (!allowedTypes.includes(selectedFile.type)) {
        alert('Please select a valid image (JPEG, PNG, WebP) or PDF file');
        return;
      }

      if (selectedFile.size > maxSize) {
        alert('File size must be less than 10MB');
        return;
      }

      setFile(selectedFile);
      setUploadResult(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const uploadPrescription = async () => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/patient/upload-prescription?processing_mode=${processingMode}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setUploadResult(response.data);

      
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const newPhoto = {
            id: Date.now(),
            name: file.name,
            dataUrl: e.target.result,
            uploadDate: new Date().toISOString(),
            patientId: patientId,
            processingResult: response.data
          };
          setPrescriptionPhotos(prev => [newPhoto, ...prev]);
        };
        reader.readAsDataURL(file);
      }

      fetchTimeline(); 
    
      if (response.data.success) {
        setCurrentPage('results');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadResult({
        success: false,
        error: error.response?.data?.detail || 'Upload failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderProcessingInfo = (result) => {
    if (!result.processing_info) return null;

    return (
      <div className="processing-info">
        <h4>Processing Information</h4>
        <div className="info-grid">
          <div className="info-item">
            <strong>Method:</strong> {result.processing_info.method}
          </div>
          <div className="info-item">
            <strong>Mode:</strong> {result.processing_info.mode}
          </div>
          <div className="info-item">
            <strong>Processing Time:</strong> {result.processing_info.processing_time?.toFixed(2)}s
          </div>
          <div className="info-item">
            <strong>Engines Used:</strong> {result.processing_info.engines_used?.join(', ') || 'Basic'}
          </div>
        </div>
      </div>
    );
  };

  const renderPrescriptionAnalysis = (result) => {
    if (!result.prescription_analysis) return null;

    return (
      <div className="prescription-analysis">
        <h4>Prescription Analysis</h4>
        <div className="analysis-grid">
          <div className="analysis-item">
            <strong>Type:</strong> 
            <span className={`type-badge ${result.prescription_analysis.type}`}>
              {result.prescription_analysis.type}
            </span>
            <span className="confidence">
              ({(result.prescription_analysis.type_confidence * 100).toFixed(1)}%)
            </span>
          </div>
          <div className="analysis-item">
            <strong>Languages:</strong> {result.prescription_analysis.languages_detected?.join(', ')}
            {result.prescription_analysis.is_multilingual && 
              <span className="multilingual-badge">Multilingual</span>
            }
          </div>
        </div>
      </div>
    );
  };

  const renderExtractedContent = (result) => {
    if (!result.extracted_content) return null;

    return (
      <div className="extracted-content">
        <h4>Extracted Content</h4>
        
        {             }
        {result.extracted_content.medications?.length > 0 && (
          <div className="content-section">
            <h5>💊 Medications</h5>
            <div className="medications-list">
              {result.extracted_content.medications.map((med, index) => (
                <div key={index} className="medication-item">
                  <span className="med-name">{med.name || med}</span>
                  {med.dosage && <span className="med-dosage">{med.dosage}</span>}
                  {med.confidence && (
                    <span className="med-confidence">
                      {(med.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {result.extracted_content.instructions?.length > 0 && (
          <div className="content-section">
            <h5>📋 Instructions</h5>
            <ul className="instructions-list">
              {result.extracted_content.instructions.map((instruction, index) => (
                <li key={index}>{instruction}</li>
              ))}
            </ul>
          </div>
        )}

        {}
        <div className="content-section">
          <h5>📄 Raw Extracted Text</h5>
          <div className="raw-text">
            {result.extracted_content.raw_text || 'No text extracted'}
          </div>
          <div className="confidence-bar">
            <span>Confidence: {(result.extracted_content.confidence * 100).toFixed(1)}%</span>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{width: `${result.extracted_content.confidence * 100}%`}}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMedicalAnalysis = (result) => {
    if (!result.medical_analysis || result.medical_analysis.error) return null;

    return (
      <div className="medical-analysis">
        <h4>Medical Analysis</h4>
        <div className="analysis-content">
          {result.medical_analysis.drug_interactions && (
            <div className="analysis-item">
              <strong>Drug Interactions:</strong> {result.medical_analysis.drug_interactions}
            </div>
          )}
          {result.medical_analysis.dosage_validation && (
            <div className="analysis-item">
              <strong>Dosage Validation:</strong> {result.medical_analysis.dosage_validation}
            </div>
          )}
          {result.medical_analysis.completeness_score && (
            <div className="analysis-item">
              <strong>Completeness Score:</strong> 
              {(result.medical_analysis.completeness_score * 100).toFixed(1)}%
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderQualityMetrics = (result) => {
    if (!result.quality_metrics) return null;

    return (
      <div className="quality-metrics">
        <h4>Quality Metrics</h4>
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">Overall Confidence</span>
            <div className="metric-bar">
              <div 
                className="metric-fill confidence" 
                style={{width: `${result.quality_metrics.overall_confidence * 100}%`}}
              ></div>
            </div>
            <span className="metric-value">
              {(result.quality_metrics.overall_confidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Text Clarity</span>
            <div className="metric-bar">
              <div 
                className="metric-fill clarity" 
                style={{width: `${result.quality_metrics.text_clarity * 100}%`}}
              ></div>
            </div>
            <span className="metric-value">
              {(result.quality_metrics.text_clarity * 100).toFixed(1)}%
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Completeness</span>
            <div className="metric-bar">
              <div 
                className="metric-fill completeness" 
                style={{width: `${result.quality_metrics.completeness * 100}%`}}
              ></div>
            </div>
            <span className="metric-value">
              {(result.quality_metrics.completeness * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderDigitalizationSection = (result) => {
    if (!result.extracted_content) return null;

    const generateDigitalPrescription = () => {
      const medications = result.extracted_content.medications || [];
      const patientInfo = result.extracted_content.patient_info || {};
      const doctorInfo = result.extracted_content.doctor_info || {};

      return {
        header: {
          clinic: doctorInfo.clinic_name || "Medical Clinic",
          doctor: doctorInfo.name || "Dr. [Name]",
          date: new Date().toLocaleDateString(),
          prescriptionId: `RX-${Date.now()}`
        },
        patient: {
          name: patientInfo.name || "[Patient Name]",
          age: patientInfo.age || "[Age]",
          gender: patientInfo.gender || "[Gender]",
          id: patientId
        },
        medications: medications.map(med => ({
          name: med.name || "[Medication]",
          dosage: med.dosage || "[Dosage]",
          frequency: med.frequency || "[Frequency]",
          duration: med.duration || "[Duration]",
          instructions: med.instructions || "[Instructions]"
        })),
        footer: {
          doctorSignature: "Dr. [Signature]",
          license: doctorInfo.license || "[License No.]"
        }
      };
    };

    const digitalRx = generateDigitalPrescription();

    return (
      <div className="digitalization-section">
        <h4>Digital Prescription</h4>
        <div className="digital-prescription">
          <div className="prescription-header">
            <div className="clinic-info">
              <h3>{digitalRx.header.clinic}</h3>
              <p>{digitalRx.header.doctor}</p>
              <p>Date: {digitalRx.header.date}</p>
              <p>Rx ID: {digitalRx.header.prescriptionId}</p>
            </div>
          </div>

          <div className="patient-details">
            <h4>Patient Information:</h4>
            <p><strong>Name:</strong> {digitalRx.patient.name}</p>
            <p><strong>Age:</strong> {digitalRx.patient.age}</p>
            <p><strong>Gender:</strong> {digitalRx.patient.gender}</p>
            <p><strong>Patient ID:</strong> {digitalRx.patient.id}</p>
          </div>

          <div className="medications-list">
            <h4>Prescribed Medications:</h4>
            {digitalRx.medications.map((med, index) => (
              <div key={index} className="medication-item">
                <div className="med-name">{index + 1}. {med.name}</div>
                <div className="med-details">
                  <span><strong>Dosage:</strong> {med.dosage}</span>
                  <span><strong>Frequency:</strong> {med.frequency}</span>
                  <span><strong>Duration:</strong> {med.duration}</span>
                </div>
                {med.instructions && (
                  <div className="med-instructions">
                    <strong>Instructions:</strong> {med.instructions}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="prescription-footer">
            <div className="signature-section">
              <p><strong>Doctor's Signature:</strong> {digitalRx.footer.doctorSignature}</p>
              <p><strong>License No:</strong> {digitalRx.footer.license}</p>
            </div>
          </div>
        </div>

        <div className="digitalization-actions">
          <button
            className="action-button primary"
            onClick={() => {
              const printContent = document.querySelector('.digital-prescription').innerHTML;
              const printWindow = window.open('', '_blank');
              printWindow.document.write(`
                <html>
                  <head>
                    <title>Digital Prescription</title>
                    <style>
                      body { font-family: Arial, sans-serif; padding: 20px; }
                      .prescription-header { border-bottom: 2px solid #333; margin-bottom: 20px; }
                      .medication-item { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
                      .med-name { font-weight: bold; font-size: 16px; }
                      .med-details { margin: 5px 0; }
                      .med-details span { margin-right: 15px; }
                    </style>
                  </head>
                  <body>${printContent}</body>
                </html>
              `);
              printWindow.document.close();
              printWindow.print();
            }}
          >
            Print Digital Prescription
          </button>
          <button
            className="action-button secondary"
            onClick={() => {
              const dataStr = JSON.stringify(digitalRx, null, 2);
              const dataBlob = new Blob([dataStr], {type: 'application/json'});
              const url = URL.createObjectURL(dataBlob);
              const link = document.createElement('a');
              link.href = url;
              link.download = `prescription_${digitalRx.header.prescriptionId}.json`;
              link.click();
            }}
          >
            Download as JSON
          </button>
        </div>
      </div>
    );
  };

 
  const renderLandingPage = () => (
    <div className="landing-page">
      <div className="auth-container">
        <div className="app-branding">
          <h1>HealthTwin AI</h1>
          <p>Advanced Prescription Processing System</p>
        </div>

        <div className="auth-forms">
          <div className="auth-tabs">
            <button
              className={`auth-tab ${currentView === 'login' ? 'active' : ''}`}
              onClick={() => setCurrentView('login')}
            >
              Sign In
            </button>
            <button
              className={`auth-tab ${currentView === 'register' ? 'active' : ''}`}
              onClick={() => setCurrentView('register')}
            >
              Register
            </button>
          </div>

          <form onSubmit={currentView === 'login' ? handleLogin : handleRegister} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={userCredentials.email}
                onChange={(e) => setUserCredentials({...userCredentials, email: e.target.value})}
                placeholder="Enter your email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={userCredentials.password}
                onChange={(e) => setUserCredentials({...userCredentials, password: e.target.value})}
                placeholder="Enter your password"
                required
              />
            </div>

            <button type="submit" className="auth-submit-btn">
              {currentView === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );

  // Patient ID Page Component
  const renderPatientIdPage = () => (
    <div className="patient-id-page">
      <div className="patient-id-container">
        <h1>Your HealthTwin ID</h1>
        <h2>HealthTwin Patient ID</h2>

        <div className="patient-id-display">
          <div className="id-card">
            <div className="id-number">HT491713</div>
            <div className="id-message">Keep this ID safe - it's your medical ID</div>
          </div>
        </div>

        <div className="navigation-buttons">
          <button onClick={navigateToHome} className="proceed-btn">
            Continue to Application
          </button>
          <button onClick={navigateToLanding} className="logout-btn">
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );

  const renderNavigation = () => (
    <nav className="navigation">
      <div className="nav-container">
        <button
          className={`nav-button ${currentView === 'patient' ? 'active' : ''}`}
          onClick={() => setCurrentView('patient')}
        >
          👤 Patient Portal
        </button>
        <button
          className={`nav-button ${currentView === 'doctor' ? 'active' : ''}`}
          onClick={() => setCurrentView('doctor')}
        >
          👨‍⚕️ Doctor Portal
        </button>
        <button
          className={`nav-button ${currentView === 'timeline' ? 'active' : ''}`}
          onClick={() => setCurrentView('timeline')}
        >
          📅 Project Timeline
        </button>
      </div>
    </nav>
  );

  const renderPatientIdSection = () => (
    <div className="patient-id-section">
      <h2>🆔 Your HealthTwin ID</h2>
      <div className="id-display">
        <div className="patient-id-card">
          <div className="id-header">
            <span className="id-icon">🏥</span>
            <span className="id-title">HealthTwin Patient ID</span>
          </div>
          <div className="id-number">{patientId}</div>
          <div className="id-subtitle">Keep this ID safe - it's your medical identity</div>
        </div>
      </div>

      <div className="id-recovery">
        <h3>🔄 Forgot your ID? Recover via SMS</h3>
        <div className="recovery-form">
          <input
            type="tel"
            placeholder="Enter your 10-digit phone number"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            maxLength="10"
            className="phone-input"
          />
          <button onClick={sendOtp} className="otp-button">
            📱 Send OTP
          </button>
        </div>

        {showOtpInput && (
          <div className="otp-section">
            <input
              type="text"
              placeholder="Enter 4-digit OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              maxLength="4"
              className="otp-input"
            />
            <button onClick={verifyOtp} className="verify-button">
              ✅ Verify OTP
            </button>
          </div>
        )}
      </div>
    </div>
  );

  
  const renderDoctorPortal = () => (
    <div className="doctor-portal">
      <h2>👨‍⚕️ Doctor Portal</h2>
      <div className="doctor-search">
        <h3>🔍 Search Patient by ID</h3>
        <div className="search-form">
          <input
            type="text"
            placeholder="Enter Patient ID (e.g., HT123456)"
            className="patient-search-input"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                searchPatientById(e.target.value);
              }
            }}
          />
          <button
            onClick={(e) => {
              const input = e.target.previousElementSibling;
              searchPatientById(input.value);
            }}
            className="search-button"
          >
            🔍 Search
          </button>
        </div>
      </div>

      {patientData && (
        <div className="patient-details">
          <h3>📋 Patient Information</h3>
          <div className="patient-card">
            <div className="patient-header">
              <h4>{patientData.name}</h4>
              <span className="patient-id-badge">{patientData.id}</span>
            </div>
            <div className="patient-info">
              <p><strong>Age:</strong> {patientData.age}</p>
              <p><strong>Phone:</strong> {patientData.phone}</p>
              <p><strong>Last Visit:</strong> {patientData.lastVisit}</p>
            </div>

            <div className="current-medications">
              <h4>💊 Current Medications</h4>
              {patientData.medications.map((med, index) => (
                <div key={index} className="medication-card">
                  <span className="med-name">{med.name}</span>
                  <span className="med-details">{med.dosage} - {med.frequency}</span>
                  <span className="med-date">Prescribed: {med.prescribed}</span>
                </div>
              ))}
            </div>

            <div className="prescription-history">
              <h4>📜 Prescription History</h4>
              {patientData.prescriptionHistory.map((record, index) => (
                <div key={index} className="history-item">
                  <div className="history-date">{record.date}</div>
                  <div className="history-details">
                    <p><strong>Doctor:</strong> {record.doctor}</p>
                    <p><strong>Condition:</strong> {record.condition}</p>
                    <p><strong>Medications:</strong> {record.medications} prescribed</p>
                  </div>
                </div>
              ))}
            </div>

            {}
            <div className="prescription-photos">
              <h4>📸 Prescription Images</h4>
              <p className="photos-subtitle">Reference images for verification and review</p>
              {prescriptionPhotos.length > 0 ? (
                <div className="photos-grid">
                  {prescriptionPhotos.map((photo) => (
                    <div key={photo.id} className="photo-card">
                      <div className="photo-header">
                        <span className="photo-name">{photo.name}</span>
                        <span className="photo-date">
                          {new Date(photo.uploadDate).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="photo-container">
                        <img
                          src={photo.dataUrl}
                          alt={photo.name}
                          className="prescription-image"
                          onClick={() => {
                            
                            const modal = document.createElement('div');
                            modal.className = 'image-modal';
                            modal.innerHTML = `
                              <div class="modal-content">
                                <span class="close-modal">&times;</span>
                                <img src="${photo.dataUrl}" alt="${photo.name}" style="max-width: 90vw; max-height: 90vh;">
                                <div class="modal-info">
                                  <h3>${photo.name}</h3>
                                  <p>Uploaded: ${new Date(photo.uploadDate).toLocaleString()}</p>
                                  <p>Patient ID: ${photo.patientId}</p>
                                </div>
                              </div>
                            `;
                            document.body.appendChild(modal);

                            modal.querySelector('.close-modal').onclick = () => {
                              document.body.removeChild(modal);
                            };
                            modal.onclick = (e) => {
                              if (e.target === modal) {
                                document.body.removeChild(modal);
                              }
                            };
                          }}
                        />
                      </div>
                      <div className="photo-info">
                        <p><strong>Patient ID:</strong> {photo.patientId}</p>
                        <p><strong>Confidence:</strong>
                          {photo.processingResult?.extracted_content?.confidence ?
                            `${(photo.processingResult.extracted_content.confidence * 100).toFixed(1)}%` :
                            'N/A'
                          }
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-photos">
                  <p>📷 No prescription images uploaded yet</p>
                  <p className="no-photos-subtitle">Images will appear here when patients upload prescriptions</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className={`App ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      {}
      <div className="medical-icons">
        <div className="medical-icon">🏥</div>
        <div className="medical-icon">💊</div>
        <div className="medical-icon">🩺</div>
        <div className="medical-icon">📋</div>
        <div className="medical-icon">⚕️</div>
      </div>

      {}
      {currentPage === 'landing' && renderLandingPage()}
      {currentPage === 'patientId' && renderPatientIdPage()}
      {currentPage === 'home' && (
        <>
          <header className="App-header">
            <h1>HealthTwin AI - Prescription Scanner</h1>
            <p>Advanced AI-powered prescription digitization with multi-language support</p>

            {}
            <div className="theme-toggle">
              <button
                className={`theme-button ${darkMode ? 'dark' : 'light'}`}
                onClick={() => setDarkMode(!darkMode)}
                aria-label="Toggle theme"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
            </div>
          </header>

      {renderNavigation()}

      <main className="main-content">
        {currentView === 'patient' && (
          <>
            {renderPatientIdSection()}

            <div className="upload-section">
              <h2>📤 Upload Prescription</h2>
          
          {}
          <div className="processing-mode">
            <label>Processing Mode:</label>
            <select 
              value={processingMode} 
              onChange={(e) => setProcessingMode(e.target.value)}
              disabled={loading}
            >
              <option value="fast">⚡ Fast (Printed text only)</option>
              <option value="standard">🔄 Standard (Printed + Handwriting)</option>
              <option value="comprehensive">🚀 Comprehensive (All engines)</option>
            </select>
          </div>

          {}
          <div 
            className={`file-upload-area ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={(e) => handleFileSelect(e.target.files[0])}
              accept="image/*,.pdf"
              disabled={loading}
              id="file-input"
              style={{display: 'none'}}
            />
            <label htmlFor="file-input" className="file-upload-label">
              {file ? (
                <div className="file-selected">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
              ) : (
                <div className="file-placeholder">
                  <span className="upload-icon">📁</span>
                  <p>Drag & drop your prescription here or click to browse</p>
                  <p className="file-types">Supports: JPEG, PNG, WebP, PDF (max 10MB)</p>
                </div>
              )}
            </label>
          </div>

          <button 
            onClick={uploadPrescription} 
            disabled={!file || loading}
            className="upload-button"
          >
            {loading ? '🔄 Processing...' : '🚀 Process Prescription'}
          </button>
        </div>

        {}
        {uploadResult && (
          <div className="upload-result">
            <h2>📊 Processing Results</h2>
            
            {uploadResult.success ? (
              <div className="result-success">
                <div className="result-header">
                  <span className="success-icon">✅</span>
                  <span className="result-message">{uploadResult.message}</span>
                </div>

                {renderProcessingInfo(uploadResult)}
                {renderPrescriptionAnalysis(uploadResult)}
                {renderExtractedContent(uploadResult)}
                {renderMedicalAnalysis(uploadResult)}
                {renderQualityMetrics(uploadResult)}
              </div>
            ) : (
              <div className="result-error">
                <span className="error-icon">❌</span>
                <span className="error-message">
                  {uploadResult.error || 'Processing failed'}
                </span>
              </div>
            )}
          </div>
        )}

            {}
            <div className="timeline-section">
              <h2>📅 Recent Activity</h2>
              {timeline.length > 0 ? (
                <div className="timeline">
                  {timeline.map((item) => (
                    <div key={item.id} className="timeline-item">
                      <div className="timeline-date">{new Date(item.date).toLocaleDateString()}</div>
                      <div className="timeline-content">
                        <h3>{item.title}</h3>
                        <p>{item.description}</p>

                        {item.medications && (
                          <div className="timeline-medications">
                            <strong>Medications:</strong>
                            {Array.isArray(item.medications) && item.medications.length > 0 ? (
                              <ul>
                                {item.medications.map((med, index) => (
                                  <li key={index}>
                                    {typeof med === 'object' ?
                                      `${med.name} ${med.dosage} - ${med.frequency}` :
                                      med
                                    }
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <span>No medications found</span>
                            )}
                          </div>
                        )}

                        {item.processing_info && (
                          <div className="timeline-processing">
                            <strong>Processing:</strong> {item.processing_info.method}
                            {item.processing_info.languages_detected &&
                              ` (${item.processing_info.languages_detected.join(', ')})`
                            }
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-timeline">No prescriptions processed yet</p>
              )}
            </div>
          </>
        )}

        {currentView === 'doctor' && renderDoctorPortal()}

        {currentView === 'timeline' && (
          <div className="project-timeline">
            <h2>🚀 HealthTwin AI - Project Development Timeline</h2>
            <div className="development-timeline">
              <div className="timeline-item">
                <div className="timeline-date">Phase 1</div>
                <div className="timeline-content">
                  <h3>🏗️ Foundation & Core Setup</h3>
                  <p>Basic OCR implementation with FastAPI backend and React frontend</p>
                  <ul>
                    <li>✅ FastAPI backend with CORS configuration</li>
                    <li>✅ React frontend with file upload</li>
                    <li>✅ Basic Tesseract OCR integration</li>
                    <li>✅ File validation and error handling</li>
                  </ul>
                </div>
              </div>

              <div className="timeline-item">
                <div className="timeline-date">Phase 2</div>
                <div className="timeline-content">
                  <h3>🤖 Advanced AI/ML Integration</h3>
                  <p>Enhanced OCR with multiple engines and medical intelligence</p>
                  <ul>
                    <li>✅ TrOCR for handwriting recognition</li>
                    <li>✅ EasyOCR for multi-language support</li>
                    <li>✅ medSpaCy for medical entity recognition</li>
                    <li>✅ Unified OCR pipeline with confidence scoring</li>
                  </ul>
                </div>
              </div>

              <div className="timeline-item">
                <div className="timeline-date">Phase 3</div>
                <div className="timeline-content">
                  <h3>🏥 Healthcare Features</h3>
                  <p>Patient ID system and medical workflow integration</p>
                  <ul>
                    <li>✅ Unique Patient ID generation (HealthTwin ID)</li>
                    <li>✅ SMS OTP recovery system</li>
                    <li>✅ Doctor portal for patient lookup</li>
                    <li>✅ Prescription history tracking</li>
                  </ul>
                </div>
              </div>

              <div className="timeline-item">
                <div className="timeline-date">Phase 4</div>
                <div className="timeline-content">
                  <h3>🎨 UI/UX Enhancement</h3>
                  <p>Modern health-tech themed interface with animations</p>
                  <ul>
                    <li>✅ Health-tech color scheme and branding</li>
                    <li>✅ Smooth animations and transitions</li>
                    <li>✅ Responsive design for mobile devices</li>
                    <li>✅ Interactive navigation between portals</li>
                  </ul>
                </div>
              </div>

              <div className="timeline-item">
                <div className="timeline-date">Future</div>
                <div className="timeline-content">
                  <h3>🚀 Planned Enhancements</h3>
                  <p>Advanced features for production deployment</p>
                  <ul>
                    <li>🔄 Real SMS integration with Twilio/AWS SNS</li>
                    <li>🔄 Database integration for persistent storage</li>
                    <li>🔄 Advanced drug interaction checking</li>
                    <li>🔄 Integration with hospital management systems</li>
                    <li>🔄 Blockchain for secure medical records</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {}
      <nav className="bottom-navigation">
        <button onClick={navigateToPatientId} className="nav-btn">
          Patient ID
        </button>
        <button onClick={() => setCurrentPage('home')} className="nav-btn active">
          Home
        </button>
        <button onClick={navigateToLanding} className="nav-btn">
          Sign Out
        </button>
      </nav>
      </>
      )}

      {currentPage === 'results' && (
        <div className="results-page">
          <header className="App-header">
            <h1>Processing Results</h1>
            <div className="theme-toggle">
              <button
                className={`theme-button ${darkMode ? 'dark' : 'light'}`}
                onClick={() => setDarkMode(!darkMode)}
                aria-label="Toggle theme"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
            </div>
          </header>

          <main className="main-content">
            {uploadResult && (
              <div className="upload-result">
                <h2>Processing Results</h2>

                {uploadResult.success ? (
                  <div className="result-success">
                    <div className="result-header">
                      <span className="success-icon">✅</span>
                      <span className="result-message">{uploadResult.message}</span>
                    </div>

                    {renderProcessingInfo(uploadResult)}
                    {renderPrescriptionAnalysis(uploadResult)}
                    {renderExtractedContent(uploadResult)}
                    {renderMedicalAnalysis(uploadResult)}
                    {renderQualityMetrics(uploadResult)}
                    {renderDigitalizationSection(uploadResult)}
                  </div>
                ) : (
                  <div className="result-error">
                    <span className="error-icon">❌</span>
                    <span className="error-message">
                      {uploadResult.error || 'Processing failed'}
                    </span>
                  </div>
                )}
              </div>
            )}
          </main>

          {}
          <nav className="bottom-navigation">
            <button onClick={navigateToHome} className="nav-btn">
              Home
            </button>
            <button onClick={() => setCurrentPage('results')} className="nav-btn active">
              Results
            </button>
            <button onClick={navigateToPatientId} className="nav-btn">
              Patient ID
            </button>
          </nav>
        </div>
      )}
    </div>
  );
}

export default App;

