import axios from 'axios';

// Use the environment variable if available (e.g., set in Vercel/Netlify), otherwise default to our live Render API
let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

// Safety net: If Render gives us just the service name (e.g. cancer-ai-api-sg4l), 
// append the domain and ensure https protocol.
if (API_BASE_URL && !API_BASE_URL.includes('.') && !API_BASE_URL.includes('localhost')) {
  API_BASE_URL = `${API_BASE_URL}.onrender.com`;
}

if (API_BASE_URL && !API_BASE_URL.startsWith('http')) {
  API_BASE_URL = `https://${API_BASE_URL}`;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = () => api.get('/health');

export const extractReport = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/extract-report', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const predictAll = (data) => api.post('/predict/all', data);

export const generateReportPDF = (data) => api.post('/generate-report-pdf', data, {
  responseType: 'blob'
});

export const getSimilarPatients = (caseId) => api.post('/similar-patients', { case_id: caseId });

export default api;
