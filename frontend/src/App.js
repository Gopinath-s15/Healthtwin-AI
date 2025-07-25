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
  const [apiCapabilities, setApiCapabilities] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchTimeline();
    fetchApiCapabilities();
  }, []);

  const fetchApiCapabilities = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/capabilities`);
      setApiCapabilities(response.data);
    } catch (error) {
      console.error('Failed to fetch API capabilities:', error);
    }
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

  const handleFileSelect = (selectedFile) => {
    if (selectedFile) {
      // Enhanced file validation
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
      fetchTimeline(); // Refresh timeline
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
        <h4>🔧 Processing Information</h4>
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
        <h4>📋 Prescription Analysis</h4>
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
        <h4>📝 Extracted Content</h4>
        
        {/* Medications */}
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

        {/* Raw Text */}
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
        <h4>🏥 Medical Analysis</h4>
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
        <h4>📊 Quality Metrics</h4>
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏥 HealthTwin AI - Advanced Prescription Processing</h1>
        {apiCapabilities && (
          <div className="capabilities-status">
            <span className={`status-badge ${apiCapabilities.unified_ocr_pipeline ? 'active' : 'basic'}`}>
              {apiCapabilities.unified_ocr_pipeline ? '🚀 Advanced ML Pipeline' : '📝 Basic Mode'}
            </span>
            {apiCapabilities.medical_context_processing && 
              <span className="status-badge active">🏥 Medical AI</span>
            }
            {apiCapabilities.handwriting_recognition && 
              <span className="status-badge active">✍️ Handwriting</span>
            }
            <span className="status-badge active">
              🌐 {apiCapabilities.supported_languages?.length || 1} Languages
            </span>
          </div>
        )}
      </header>

      <main className="main-content">
        <div className="upload-section">
          <h2>📤 Upload Prescription</h2>
          
          {/* Processing Mode Selection */}
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

          {/* Enhanced File Upload */}
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

        {/* Enhanced Upload Results */}
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

                {uploadResult.enhancement_note && (
                  <div className="enhancement-note">
                    <strong>💡 Enhancement Available:</strong> {uploadResult.enhancement_note}
                  </div>
                )}
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

        {/* Enhanced Timeline */}
        <div className="timeline-section">
          <h2>📅 Patient Timeline</h2>
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
      </main>
    </div>
  );
}

export default App;

