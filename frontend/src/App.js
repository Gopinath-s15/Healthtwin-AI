import React, { useState } from "react";

const API = "http://localhost:8000"; // Change if backend is remote

function App() {
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [healthtwinId, setHealthtwinId] = useState("");
  const [file, setFile] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Helper function to handle API errors
  const handleApiError = (error, defaultMessage) => {
    console.error("API Error:", error);
    if (error.message === "Failed to fetch") {
      return "Unable to connect to server. Please check if the backend is running.";
    }
    return defaultMessage;
  };

  // Clear messages after a delay
  const clearMessages = () => {
    setTimeout(() => {
      setError("");
      setSuccess("");
    }, 5000);
  };

  const register = async () => {
    if (!phone.trim()) {
      setError("Phone number is required");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: phone.trim(), name: name.trim() || null }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Registration failed`);
      }

      setHealthtwinId(data.healthtwin_id);
      setSuccess("Registration successful! You can now upload prescriptions.");
      setPhone("");
      setName("");
      clearMessages();
    } catch (error) {
      setError(handleApiError(error, "Registration failed. Please try again."));
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  const upload = async () => {
    if (!file) {
      setError("Please select a file to upload");
      clearMessages();
      return;
    }

    if (!healthtwinId) {
      setError("Please register first before uploading");
      clearMessages();
      return;
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError("Please select a valid image file (JPG, PNG, GIF, BMP, TIFF, WebP)");
      clearMessages();
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError("File size must be less than 10MB");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API}/upload-prescription?patient_id=${healthtwinId}`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Upload failed`);
      }

      setSuccess("Prescription uploaded successfully!");
      setFile(null);
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';

      // Refresh timeline
      await fetchTimeline();
      clearMessages();
    } catch (error) {
      setError(handleApiError(error, "Upload failed. Please try again."));
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  const fetchTimeline = async () => {
    if (!healthtwinId) {
      setError("Please register first to view timeline");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API}/timeline/${healthtwinId}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Failed to fetch timeline`);
      }

      setTimeline(data.timeline || []);
      if (data.timeline && data.timeline.length === 0) {
        setSuccess("No medical records found. Upload a prescription to get started.");
        clearMessages();
      }
    } catch (error) {
      setError(handleApiError(error, "Failed to load timeline. Please try again."));
      setTimeline([]);
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-center text-blue-600">HealthTwin AI Demo</h1>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          <strong>Success:</strong> {success}
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
            Processing...
          </div>
        </div>
      )}

      {/* Registration Section */}
      <div className="bg-white shadow-md rounded px-6 py-4 mb-6">
        <h2 className="text-xl font-semibold mb-4">Patient Registration</h2>
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <input
            className="border border-gray-300 rounded px-3 py-2 flex-1"
            placeholder="Phone Number *"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            disabled={loading}
            required
          />
          <input
            className="border border-gray-300 rounded px-3 py-2 flex-1"
            placeholder="Name (Optional)"
            value={name}
            onChange={e => setName(e.target.value)}
            disabled={loading}
          />
          <button
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-6 py-2 rounded transition-colors"
            onClick={register}
            disabled={loading || !phone.trim()}
          >
            Register
          </button>
        </div>
      </div>

      {/* Upload Section */}
      {healthtwinId && (
        <div className="bg-white shadow-md rounded px-6 py-4 mb-6">
          <h2 className="text-xl font-semibold mb-4">Upload Prescription</h2>
          <div className="mb-2">
            <span className="text-sm text-gray-600">Your HealthTwin ID:</span>
            <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{healthtwinId}</span>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 items-start">
            <input
              type="file"
              accept="image/*"
              onChange={e => setFile(e.target.files[0])}
              disabled={loading}
              className="flex-1 border border-gray-300 rounded px-3 py-2"
            />
            <button
              className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white px-6 py-2 rounded transition-colors"
              onClick={upload}
              disabled={loading || !file}
            >
              Upload
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Supported formats: JPG, PNG, GIF, BMP, TIFF, WebP (Max 10MB)
          </p>
        </div>
      )}

      {/* Timeline Section */}
      <div className="bg-white shadow-md rounded px-6 py-4 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Medical Timeline</h2>
          <button
            className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white px-4 py-2 rounded transition-colors"
            onClick={fetchTimeline}
            disabled={loading || !healthtwinId}
          >
            Refresh Timeline
          </button>
        </div>

        {!healthtwinId && (
          <p className="text-gray-500 text-center py-4">Please register first to view your medical timeline.</p>
        )}

        {healthtwinId && timeline.length === 0 && !loading && (
          <p className="text-gray-500 text-center py-4">No medical records found. Upload a prescription to get started.</p>
        )}

        <div className="space-y-4">
          {timeline.map((entry, i) => (
            <div key={i} className="border border-gray-200 rounded p-4 hover:shadow-md transition-shadow">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="mb-2"><strong>Doctor:</strong> {entry.doctor}</div>
                  <div className="mb-2"><strong>Diagnosis:</strong> {entry.diagnosis}</div>
                  <div className="mb-2"><strong>Medications:</strong> {entry.medications}</div>
                  <div className="text-sm text-gray-600"><strong>Date:</strong> {entry.created_at}</div>
                </div>
                {entry.img && (
                  <div className="flex justify-center md:justify-end">
                    <img
                      src={`${API}/uploads/${entry.img}`}
                      alt="prescription"
                      className="max-w-32 max-h-32 object-contain border rounded cursor-pointer hover:shadow-lg transition-shadow"
                      onClick={() => window.open(`${API}/uploads/${entry.img}`, '_blank')}
                      title="Click to view full size"
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
