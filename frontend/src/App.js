import React, { useState } from 'react';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ocrResults, setOcrResults] = useState(null);
  const [timeline, setTimeline] = useState([]);

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setUploadStatus('Please select an image file');
        return;
      }
      
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setUploadStatus('File too large. Maximum size is 10MB');
        return;
      }
      
      setSelectedFile(file);
      setUploadStatus('');
      setOcrResults(null);
    }
  };

  // Upload and process prescription
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus('Please select a file first');
      return;
    }

    setIsLoading(true);
    setUploadStatus('Processing prescription...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://127.0.0.1:8000/patient/upload-prescription', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setOcrResults(result);
        setUploadStatus('Prescription processed successfully!');
        
        // Add to timeline
        const newEntry = {
          id: Date.now(),
          date: new Date().toISOString().split('T')[0],
          type: 'prescription',
          doctor: result.extracted_data.doctor_name,
          medications: result.extracted_data.medications.split(', ').filter(med => med !== 'Not extracted'),
          diagnosis: result.extracted_data.diagnosis,
          confidence: result.confidence,
          status: 'processed'
        };
        
        setTimeline(prev => [newEntry, ...prev]);
      } else {
        setUploadStatus(result.message || 'Failed to process prescription');
        setOcrResults(result);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('Network error. Please check if the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  // Load timeline data
  const loadTimeline = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/patient/timeline');
      const result = await response.json();
      
      if (result.success) {
        setTimeline(result.timeline);
      }
    } catch (error) {
      console.error('Failed to load timeline:', error);
    }
  };

  // Load timeline on component mount
  React.useEffect(() => {
    loadTimeline();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏥 HealthTwin AI</h1>
        <p>AI-Powered Prescription Processing & Medical Timeline</p>
      </header>

      <main className="main-content">
        {/* Upload Section */}
        <section className="upload-section">
          <h2>📋 Upload Prescription</h2>
          
          <div className="upload-area">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="file-label">
              {selectedFile ? selectedFile.name : 'Choose prescription image...'}
            </label>
            
            <button
              onClick={handleUpload}
              disabled={!selectedFile || isLoading}
              className="upload-btn"
            >
              {isLoading ? '🔄 Processing...' : '🚀 Process Prescription'}
            </button>
          </div>

          {uploadStatus && (
            <div className={`status-message ${ocrResults?.success ? 'success' : 'error'}`}>
              {uploadStatus}
            </div>
          )}
        </section>

        {/* OCR Results Section */}
        {ocrResults && (
          <section className="results-section">
            <h2>🤖 AI Extraction Results</h2>
            
            <div className="results-grid">
              <div className="result-card">
                <h3>📊 Processing Info</h3>
                <p><strong>Method:</strong> {ocrResults.extraction_method}</p>
                <p><strong>Confidence:</strong> 
                  <span className={`confidence ${ocrResults.confidence?.toLowerCase()}`}>
                    {ocrResults.confidence}
                  </span>
                </p>
              </div>

              <div className="result-card">
                <h3>👨‍⚕️ Medical Details</h3>
                <p><strong>Doctor:</strong> {ocrResults.extracted_data.doctor_name}</p>
                <p><strong>Clinic:</strong> {ocrResults.extracted_data.clinic_name}</p>
                <p><strong>Date:</strong> {ocrResults.extracted_data.prescription_date}</p>
              </div>

              <div className="result-card">
                <h3>💊 Medications</h3>
                <p>{ocrResults.extracted_data.medications}</p>
              </div>

              <div className="result-card">
                <h3>🩺 Diagnosis</h3>
                <p>{ocrResults.extracted_data.diagnosis}</p>
              </div>

              {ocrResults.extracted_data.raw_text && (
                <div className="result-card full-width">
                  <h3>📝 Raw Extracted Text</h3>
                  <div className="raw-text">
                    {ocrResults.extracted_data.raw_text}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Timeline Section */}
        <section className="timeline-section">
          <h2>📅 Medical Timeline</h2>
          
          {timeline.length > 0 ? (
            <div className="timeline">
              {timeline.map((entry) => (
                <div key={entry.id} className="timeline-entry">
                  <div className="timeline-date">{entry.date}</div>
                  <div className="timeline-content">
                    <h4>{entry.type === 'prescription' ? '💊 Prescription' : '🏥 ' + entry.type}</h4>
                    <p><strong>Doctor:</strong> {entry.doctor}</p>
                    {entry.medications && (
                      <p><strong>Medications:</strong> {Array.isArray(entry.medications) ? entry.medications.join(', ') : entry.medications}</p>
                    )}
                    {entry.diagnosis && <p><strong>Diagnosis:</strong> {entry.diagnosis}</p>}
                    {entry.notes && <p><strong>Notes:</strong> {entry.notes}</p>}
                    <span className={`status ${entry.status}`}>{entry.status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">No medical records yet. Upload a prescription to get started!</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;

