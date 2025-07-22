import React, { useState, useEffect } from "react";

const API = "http://localhost:8000"; // Change if backend is remote

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

  // Login form state
  const [loginData, setLoginData] = useState({
    patient_id: "",
    password: ""
  });

  // Registration form state (enhanced with password)
  const [registerData, setRegisterData] = useState({
    phone: "",
    name: "",
    password: "",
    confirmPassword: ""
  });

  // Legacy state (for backward compatibility)
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [healthtwinId, setHealthtwinId] = useState("");
  
  // App state
  const [file, setFile] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isDefaultData, setIsDefaultData] = useState(false);
  const [timelineMessage, setTimelineMessage] = useState("");

  // Check for existing token on app load
  useEffect(() => {
    const savedToken = localStorage.getItem('healthtwin_token');
    const savedUser = localStorage.getItem('healthtwin_user');
    
    if (savedToken && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setToken(savedToken);
        setCurrentUser(userData);
        setIsAuthenticated(true);
        setHealthtwinId(userData.user_id);
      } catch (err) {
        console.error("Error parsing saved user data:", err);
        localStorage.removeItem('healthtwin_token');
        localStorage.removeItem('healthtwin_user');
      }
    }
  }, []);

  // Enhanced error handling function
  const handleApiError = (error, defaultMessage) => {
    console.error("API Error:", error);
    if (error.message === "Failed to fetch") {
      return "Unable to connect to server. Please check if the backend is running.";
    }
    if (error.message.includes("404")) {
      return "Patient not found. Please register first.";
    }
    if (error.message.includes("401")) {
      logout(); // Auto logout on 401
      return "Session expired. Please log in again.";
    }
    if (error.message.includes("403")) {
      return "Access denied. Please check your credentials.";
    }
    return defaultMessage;
  };

  // Clear messages with enhanced timing
  const clearMessages = () => {
    setTimeout(() => {
      setError("");
      setSuccess("");
    }, 5000);
  };

  // Create authenticated request headers
  const getAuthHeaders = () => {
    const headers = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  };

  // Login function
  const login = async () => {
    if (!loginData.patient_id.trim() || !loginData.password.trim()) {
      setError("Patient ID and password are required");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API}/auth/patient/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Login failed`);
      }

      // Store authentication data
      const userData = {
        user_id: data.user_id,
        user_type: data.user_type,
        access_token: data.access_token
      };

      localStorage.setItem('healthtwin_token', data.access_token);
      localStorage.setItem('healthtwin_user', JSON.stringify(userData));
      
      setToken(data.access_token);
      setCurrentUser(userData);
      setIsAuthenticated(true);
      setHealthtwinId(data.user_id);
      setSuccess("Login successful! Welcome back.");
      
      // Clear login form
      setLoginData({ patient_id: "", password: "" });
      
      // Auto-fetch timeline
      setTimeout(() => fetchTimeline(), 1000);
      clearMessages();
    } catch (error) {
      setError(handleApiError(error, "Login failed. Please check your credentials."));
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  // Enhanced registration function
  const register = async () => {
    if (!registerData.phone.trim() || !registerData.password.trim()) {
      setError("Phone number and password are required");
      clearMessages();
      return;
    }

    if (registerData.password !== registerData.confirmPassword) {
      setError("Passwords do not match");
      clearMessages();
      return;
    }

    if (registerData.password.length < 6) {
      setError("Password must be at least 6 characters long");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API}/auth/patient/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: registerData.phone.trim(),
          name: registerData.name.trim() || null,
          password: registerData.password
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Registration failed`);
      }

      // Store authentication data
      const userData = {
        user_id: data.user_id,
        user_type: data.user_type,
        access_token: data.access_token
      };

      localStorage.setItem('healthtwin_token', data.access_token);
      localStorage.setItem('healthtwin_user', JSON.stringify(userData));
      
      setToken(data.access_token);
      setCurrentUser(userData);
      setIsAuthenticated(true);
      setHealthtwinId(data.user_id);
      setSuccess("Registration successful! You are now logged in.");
      
      // Clear registration form
      setRegisterData({ phone: "", name: "", password: "", confirmPassword: "" });
      
      // Auto-fetch timeline
      setTimeout(() => fetchTimeline(), 1000);
      clearMessages();
    } catch (error) {
      setError(handleApiError(error, "Registration failed. Please try again."));
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('healthtwin_token');
    localStorage.removeItem('healthtwin_user');
    setToken(null);
    setCurrentUser(null);
    setIsAuthenticated(false);
    setHealthtwinId("");
    setTimeline([]);
    setFile(null);
    setSuccess("Logged out successfully");
    clearMessages();
  };

  // Enhanced upload function with authentication
  const uploadFile = async () => {
    if (!isAuthenticated) {
      setError("Please log in to upload prescriptions");
      clearMessages();
      return;
    }

    if (!file) {
      setError("Please select a file to upload");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API}/patient/upload-prescription`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Upload failed`);
      }

      setSuccess("Prescription uploaded successfully! Your personal data is now showing.");
      setFile(null);
      setIsDefaultData(false);
      setTimelineMessage("");
      
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';

      // Refresh timeline to show user data
      await fetchTimeline();
      clearMessages();
    } catch (error) {
      setError(handleApiError(error, "Upload failed. Please try again."));
      clearMessages();
    } finally {
      setLoading(false);
    }
  };

  // Enhanced timeline fetch with authentication
  const fetchTimeline = async () => {
    if (!isAuthenticated) {
      setError("Please log in to view your timeline");
      clearMessages();
      return;
    }

    setLoading(true);
    setError("");
    setTimelineMessage("");

    try {
      const res = await fetch(`${API}/patient/timeline`, {
        method: "GET",
        headers: getAuthHeaders(),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}: Failed to fetch timeline`);
      }

      setTimeline(data.timeline || []);
      setIsDefaultData(data.is_default_data || false);
      setTimelineMessage(data.message || "");

      if (data.timeline && data.timeline.length === 0) {
        setSuccess("No medical records found. Upload a prescription to get started.");
        clearMessages();
      } else if (data.is_default_data) {
        setSuccess(data.message || "Showing sample prescriptions for demo.");
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

  // Legacy registration function (for backward compatibility)
  const legacyRegister = async () => {
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

  return (
    <div className="min-h-screen bg-gray-100 py-6 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-600 mb-2">HealthTwin AI</h1>
          <p className="text-gray-600">Your Digital Medical Twin - Enhanced with Authentication</p>
          
          {/* Authentication Status */}
          {isAuthenticated && currentUser && (
            <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg">
              <p className="text-green-800">
                ✅ Logged in as Patient ID: <span className="font-mono">{currentUser.user_id}</span>
                <button 
                  onClick={logout}
                  className="ml-4 text-red-600 hover:text-red-800 underline"
                >
                  Logout
                </button>
              </p>
            </div>
          )}
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {/* Authentication Section */}
        {!isAuthenticated && (
          <div className="bg-white shadow-md rounded px-6 py-4 mb-6">
            <div className="flex justify-center mb-4">
              <button
                className={`px-4 py-2 mr-2 rounded ${authMode === 'login' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setAuthMode('login')}
              >
                Sign In
              </button>
              <button
                className={`px-4 py-2 rounded ${authMode === 'register' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setAuthMode('register')}
              >
                Register
              </button>
            </div>

            {authMode === 'login' ? (
              // Login Form
              <div>
                <h2 className="text-xl font-semibold mb-4">Sign In to HealthTwin</h2>
                <div className="space-y-4">
                  <input
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Patient ID *"
                    value={loginData.patient_id}
                    onChange={e => setLoginData({...loginData, patient_id: e.target.value})}
                    disabled={loading}
                    required
                  />
                  <input
                    type="password"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Password *"
                    value={loginData.password}
                    onChange={e => setLoginData({...loginData, password: e.target.value})}
                    disabled={loading}
                    required
                  />
                  <button
                    className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-6 py-2 rounded transition-colors"
                    onClick={login}
                    disabled={loading || !loginData.patient_id.trim() || !loginData.password.trim()}
                  >
                    {loading ? "Signing In..." : "Sign In"}
                  </button>
                </div>
              </div>
            ) : (
              // Registration Form
              <div>
                <h2 className="text-xl font-semibold mb-4">Create HealthTwin Account</h2>
                <div className="space-y-4">
                  <input
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Phone Number *"
                    value={registerData.phone}
                    onChange={e => setRegisterData({...registerData, phone: e.target.value})}
                    disabled={loading}
                    required
                  />
                  <input
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Full Name (Optional)"
                    value={registerData.name}
                    onChange={e => setRegisterData({...registerData, name: e.target.value})}
                    disabled={loading}
                  />
                  <input
                    type="password"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Password (min 6 characters) *"
                    value={registerData.password}
                    onChange={e => setRegisterData({...registerData, password: e.target.value})}
                    disabled={loading}
                    required
                  />
                  <input
                    type="password"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Confirm Password *"
                    value={registerData.confirmPassword}
                    onChange={e => setRegisterData({...registerData, confirmPassword: e.target.value})}
                    disabled={loading}
                    required
                  />
                  <button
                    className="w-full bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white px-6 py-2 rounded transition-colors"
                    onClick={register}
                    disabled={loading || !registerData.phone.trim() || !registerData.password.trim()}
                  >
                    {loading ? "Creating Account..." : "Create Account"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Protected Content - Only show when authenticated */}
        {isAuthenticated && (
          <>
            {/* Upload Section */}
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
                  onClick={uploadFile}
                  disabled={loading || !file}
                >
                  {loading ? "Uploading..." : "Upload"}
                </button>
              </div>
            </div>

            {/* Timeline Section */}
            <div className="bg-white shadow-md rounded px-6 py-4 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Medical Timeline</h2>
                <button
                  className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-4 py-2 rounded transition-colors"
                  onClick={fetchTimeline}
                  disabled={loading}
                >
                  {loading ? "Loading..." : "Refresh Timeline"}
                </button>
              </div>

              {/* Timeline Message */}
              {timelineMessage && (
                <div className={`p-3 rounded mb-4 ${isDefaultData ? 'bg-yellow-100 border border-yellow-300 text-yellow-800' : 'bg-blue-100 border border-blue-300 text-blue-800'}`}>
                  {timelineMessage}
                </div>
              )}

              {/* Enhanced Timeline Entries with Full Details */}
              {timeline.length > 0 ? (
                <div className="space-y-4">
                  {timeline.map((entry, index) => (
                    <div key={entry.id || index} className="border border-gray-200 rounded p-4">
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        {/* Main Details */}
                        <div className="lg:col-span-2">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p><strong>Doctor:</strong> {entry.doctor_name || entry.doctor || "Unknown"}</p>
                              <p><strong>Diagnosis:</strong> {entry.diagnosis || "Not specified"}</p>
                              <p><strong>Medications:</strong> {entry.medications || "Not specified"}</p>
                              <p><strong>Date:</strong> {entry.created_at || "Unknown"}</p>
                            </div>
                            <div>
                              {entry.dosage_instructions && (
                                <p><strong>Dosage:</strong> {entry.dosage_instructions}</p>
                              )}
                              {entry.follow_up_date && (
                                <p><strong>Follow-up:</strong> {entry.follow_up_date}</p>
                              )}
                              {entry.ai_insights && (
                                <p><strong>AI Analysis:</strong> {entry.ai_insights}</p>
                              )}
                            </div>
                          </div>
                          
                          {/* Detailed Notes */}
                          {entry.notes && (
                            <div className="mt-4 p-3 bg-gray-50 rounded">
                              <strong>Prescription Details:</strong>
                              <pre className="text-sm mt-2 whitespace-pre-wrap">{entry.notes}</pre>
                            </div>
                          )}
                          
                          {/* Raw OCR Text */}
                          {entry.extracted_text && (
                            <details className="mt-4">
                              <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                                View Raw OCR Text
                              </summary>
                              <div className="mt-2 p-3 bg-yellow-50 border rounded text-sm">
                                <pre className="whitespace-pre-wrap">{entry.extracted_text}</pre>
                              </div>
                            </details>
                          )}
                        </div>
                        
                        {/* Prescription Image */}
                        {(entry.prescription_img || entry.img) && (
                          <div className="flex justify-center">
                            <img
                              src={`${API}/uploads/${entry.prescription_img || entry.img}`}
                              alt="Prescription"
                              className="max-w-full h-48 object-contain border rounded cursor-pointer hover:shadow-lg transition-shadow"
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                              onClick={() => window.open(`${API}/uploads/${entry.prescription_img || entry.img}`, '_blank')}
                              title="Click to view full size"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No medical records found.</p>
                  <p className="text-sm mt-2">Upload a prescription to get started!</p>
                </div>
              )}
            </div>
          </>
        )}

        {/* Legacy Registration Section (for testing) */}
        {!isAuthenticated && (
          <div className="bg-gray-50 shadow-md rounded px-6 py-4 mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-600">Legacy Registration (No Auth)</h3>
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
                className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white px-6 py-2 rounded transition-colors"
                onClick={legacyRegister}
                disabled={loading || !phone.trim()}
              >
                Legacy Register
              </button>
            </div>
            {healthtwinId && (
              <p className="text-sm text-gray-600">
                Legacy ID: <span className="font-mono bg-gray-200 px-2 py-1 rounded">{healthtwinId}</span>
              </p>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm mt-8">
          <p>HealthTwin AI v2.0.0 - Secure Medical Records Management</p>
          <p className="mt-1">
            {isAuthenticated ? "🔒 Authenticated Session Active" : "🔓 Please sign in to access your medical records"}
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;

