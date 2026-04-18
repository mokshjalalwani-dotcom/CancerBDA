import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import StepProgress from '../components/StepProgress';
import { ArrowRight, User, Phone, Building2, Calendar } from 'lucide-react';

const StepOne = () => {
  const { patientData, updateGeneralInfo } = usePatient();
  const navigate = useNavigate();

  const handleChange = (e) => updateGeneralInfo({ [e.target.name]: e.target.value });
  const handleSubmit = (e) => { e.preventDefault(); navigate('/step-2'); };

  return (
    <div className="premium-page" style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Animated Background Orbs */}
      <div style={{ position: 'absolute', top: '-10%', left: '-5%', width: '40vw', height: '40vw', background: 'rgba(196,30,74,0.08)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 8s infinite alternate' }} />
      <div style={{ position: 'absolute', bottom: '10%', right: '-5%', width: '35vw', height: '35vw', background: 'rgba(229,107,138,0.06)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 10s infinite alternate-reverse' }} />
      <div className="premium-container animate-up">
        <StepProgress currentStep={1} />

        <div className="premium-card">
          {/* Symmetric Header */}
          <div className="page-header">
            <div className="header-icon">
              <User size={24} />
            </div>
            <h2 className="page-title glow-text">Patient Profile</h2>
            <p className="page-subtitle">Personal information & identification</p>
          </div>

          <form onSubmit={handleSubmit} autoComplete="off">
             <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              {/* Full Name - Spans both columns for visual weight at top */}
              <div className="field-wrapper">
                <label className="field-label">Full Name</label>
                <input 
                  type="text" 
                  name="fullName" 
                  placeholder="e.g. Johnathan Doe" 
                  className="premium-input-box" 
                  value={patientData.generalInfo.fullName} 
                  onChange={handleChange} 
                  required 
                />
              </div>

              {/* Perfectly Symmetric Mid Grid */}
              <div className="form-grid">
                <div className="field-wrapper">
                  <label className="field-label">Age</label>
                  <input 
                    type="number" 
                    name="age" 
                    placeholder="Years" 
                    className="premium-input-box" 
                    value={patientData.generalInfo.age} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
                <div className="field-wrapper">
                  <label className="field-label">Gender</label>
                  <select 
                    name="gender" 
                    className="premium-input-box" 
                    value={patientData.generalInfo.gender} 
                    onChange={handleChange} 
                    required
                  >
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              {/* Perfectly Symmetric Bottom Grid */}
              <div className="form-grid">
                <div className="field-wrapper">
                  <label className="field-label">Contact Number</label>
                  <input 
                    type="tel" 
                    name="contactNumber" 
                    placeholder="+1 (555) 000-0000" 
                    className="premium-input-box" 
                    value={patientData.generalInfo.contactNumber} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
                <div className="field-wrapper">
                  <label className="field-label">Hospital ID</label>
                  <input 
                    type="text" 
                    name="hospitalId" 
                    placeholder="HOSP-77421" 
                    className="premium-input-box" 
                    value={patientData.generalInfo.hospitalId} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
              </div>

              <div style={{ marginTop: '0.25rem' }}>
                <button type="submit" className="btn-premium" style={{ padding: '0.875rem 2rem' }}>
                  Next Step: Clinical Data <ArrowRight size={18} />
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default StepOne;
