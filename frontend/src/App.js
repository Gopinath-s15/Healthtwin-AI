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
      // Validate file type - support images and PDFs
      const isImage = file.type.startsWith('image/');
      const isPDF = file.type === 'application/pdf';

      if (!isImage && !isPDF) {
        setUploadStatus('Please select an image file (JPG, PNG, etc.) or PDF file');
        return;
      }

      // Validate file size - different limits for images vs PDFs
      const maxSize = isPDF ? 50 * 1024 * 1024 : 10 * 1024 * 1024; // 50MB for PDF, 10MB for images
      const sizeLabel = isPDF ? '50MB' : '10MB';

      if (file.size > maxSize) {
        setUploadStatus(`File too large. Maximum size is ${sizeLabel} for ${isPDF ? 'PDF' : 'image'} files`);
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

      if (!response.ok) {
        // Handle HTTP errors (400, 500, etc.)
        const errorResult = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setUploadStatus(`Upload failed: ${errorResult.detail || errorResult.message || 'Unknown error'}`);
        setOcrResults({
          success: false,
          error: errorResult.detail || errorResult.message || 'Upload failed',
          extraction_method: 'Failed',
          confidence: 'Low'
        });
        return;
      }

      const result = await response.json();

      if (result.success) {
        setOcrResults(result);
        setUploadStatus('Prescription processed successfully!');

        // Add to timeline (only if extracted_data exists)
        if (result.extracted_data) {
          const newEntry = {
            id: Date.now(),
            date: new Date().toISOString().split('T')[0],
            type: 'prescription',
            doctor: result.extracted_data.doctor_name || 'Unknown',
            medications: result.extracted_data.medications ?
              result.extracted_data.medications.split(', ').filter(med => med !== 'Not extracted') : [],
            diagnosis: result.extracted_data.diagnosis || 'Not specified',
            confidence: result.confidence || result.confidence_level || 'Unknown',
            status: 'processed'
          };

          setTimeline(prev => [newEntry, ...prev]);
        }
      } else {
        setUploadStatus(result.message || result.error || 'Failed to process prescription');
        setOcrResults(result);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('Network error. Please check if the backend is running.');
      setOcrResults({
        success: false,
        error: 'Network error occurred',
        extraction_method: 'Failed',
        confidence: 'Low'
      });
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
              accept="image/*,.pdf,application/pdf"
              onChange={handleFileSelect}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="file-label">
              {selectedFile ? selectedFile.name : 'Choose prescription image or PDF...'}
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

              {ocrResults.extracted_data ? (
                <>
                  <div className="result-card">
                    <h3>👨‍⚕️ Medical Details</h3>
                    <p><strong>Doctor:</strong> {ocrResults.extracted_data.doctor_name || 'Not found'}</p>
                    <p><strong>Clinic:</strong> {ocrResults.extracted_data.clinic_name || 'Not found'}</p>
                    <p><strong>Date:</strong> {ocrResults.extracted_data.prescription_date || 'Not found'}</p>
                  </div>

                  <div className="result-card">
                    <h3>💊 Medications</h3>
                    <p>{ocrResults.extracted_data.medications || 'Not found'}</p>
                  </div>

                  <div className="result-card">
                    <h3>🩺 Diagnosis</h3>
                    <p>{ocrResults.extracted_data.diagnosis || 'Not found'}</p>
                  </div>

                  {ocrResults.extracted_data.raw_text && (
                    <div className="result-card full-width">
                      <h3>📝 Raw Extracted Text</h3>
                      <div className="raw-text">
                        {ocrResults.extracted_data.raw_text}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="result-card">
                  <h3>❌ Processing Failed</h3>
                  <p><strong>Error:</strong> {ocrResults.error || ocrResults.message || 'Unknown error occurred'}</p>
                  {ocrResults.success === false && (
                    <p>Please try uploading a different image or PDF file.</p>
                  )}
                </div>
              )}

              {ocrResults.pdf_info && (
                <div className="result-card">
                  <h3>📄 PDF Information</h3>
                  <p><strong>Total Pages:</strong> {ocrResults.pdf_info.total_pages}</p>
                  <p><strong>Processed Pages:</strong> {ocrResults.pdf_info.processed_pages}</p>
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

