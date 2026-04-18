import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import StepProgress from '../components/StepProgress';
import { predictAll, extractReport } from '../services/api';
import { ArrowLeft, Dna, Activity, FileText, Upload, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const StepTwo = () => {
  const { patientData, updateClinicalData, setResults } = usePatient();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setExtracting(true);
    setError(null);
    updateClinicalData({ reportFile: file });

    try {
      const response = await extractReport(file);
      const extractedData = response.data;
      
      // Update context with extracted values
      updateClinicalData({
        tumorStage: extractedData.tumorStage || '',
        tumorGrade: extractedData.tumorGrade || '',
        metastasis: extractedData.metastasis || 'No',
        geneA: extractedData.geneA || '',
        geneB: extractedData.geneB || '',
        geneC: extractedData.geneC || '',
        extractedGenes: extractedData.extracted_genes || {}
      });
    } catch (err) {
      console.error("Extraction Error:", err);
      setError("Failed to extract data from PDF. Please ensure it's a valid medical report.");
    } finally {
      setExtracting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!patientData.clinicalData.reportFile) {
      setError("Please upload a medical report PDF to proceed.");
      return;
    }

    setLoading(true);
    try {
      // Build dynamic genomic payload
      const genesPayload = { ...patientData.clinicalData.extractedGenes };
      
      // Fallback/Legacy markers if not already in extractedGenes
      if (patientData.clinicalData.geneA) genesPayload["Gene_A"] = parseFloat(patientData.clinicalData.geneA);
      if (patientData.clinicalData.geneB) genesPayload["Gene_B"] = parseFloat(patientData.clinicalData.geneB);
      if (patientData.clinicalData.geneC) genesPayload["Gene_C"] = parseFloat(patientData.clinicalData.geneC);

      const payload = { genes: genesPayload };
      const response = await predictAll(payload);
      setResults(response.data);
      navigate('/results', { state: { results: response.data } });
    } catch (err) {
      setError("Analysis system is temporarily unavailable. Please ensure the backend server is running and check your network connection.");
    } finally { setLoading(false); }
  };

  return (
    <div className="premium-page" style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Animated Background Orbs */}
      <div style={{ position: 'absolute', top: '-10%', left: '-5%', width: '40vw', height: '40vw', background: 'rgba(196,30,74,0.08)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 8s infinite alternate' }} />
      <div style={{ position: 'absolute', bottom: '10%', right: '-5%', width: '35vw', height: '35vw', background: 'rgba(229,107,138,0.06)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 10s infinite alternate-reverse' }} />
      <div className="premium-container animate-up">
        {/* Symmetric Back & Progress */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', marginTop: '0.5rem' }}>
          <button type="button" onClick={() => navigate('/step-1')} className="page-subtitle" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', cursor: 'pointer', outline: 'none' }}>
            <ArrowLeft size={14} /> Back to profile
          </button>
          <span className="page-subtitle" style={{ fontSize: '0.625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Phase 02/03</span>
        </div>
        
        <StepProgress currentStep={2} />

        <div className="premium-card">
          <div className="page-header">
            <div className="header-icon" style={{ background: 'rgba(52, 211, 153, 0.1)', color: '#34d399' }}>
              <Activity size={24} />
            </div>
            <h2 className="page-title glow-text">Clinical Data</h2>
            <p className="page-subtitle">Biomarkers & tumor classification</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              {/* Upload Area - The Primary Action */}
              <div className="field-wrapper">
                <label className="field-label" style={{ marginBottom: '0.5rem' }}>Molecular Diagnosis Report (PDF)</label>
                <div style={{ position: 'relative', height: '120px' }}>
                  <input 
                    type="file" 
                    accept=".pdf" 
                    style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', zIndex: 2 }} 
                    onChange={handleFileUpload} 
                    disabled={extracting}
                  />
                  <div style={{ 
                    height: '100%',
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center',
                    gap: '0.75rem', 
                    padding: '1.5rem', 
                    background: 'rgba(30, 41, 59, 0.4)', 
                    border: '2px dashed var(--border)', 
                    borderRadius: '1rem',
                    transition: 'all 0.3s ease'
                  }}>
                    {extracting ? (
                      <Loader2 className="animate-spin" size={32} style={{ color: '#E56B8A' }} />
                    ) : (
                      <Upload size={32} style={{ color: 'var(--text-mute)' }} />
                    )}
                    <span style={{ fontSize: '0.875rem', fontWeight: 500, color: patientData.clinicalData.reportFile ? 'var(--text-main)' : 'var(--text-mute)' }}>
                      {patientData.clinicalData.reportFile ? patientData.clinicalData.reportFile.name : 'Click or drag PDF report to upload'}
                    </span>
                  </div>
                </div>
                {error && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', color: '#f87171', fontSize: '0.75rem' }}>
                    <AlertCircle size={14} /> {error}
                  </div>
                )}
              </div>

              {/* Status Indicator & Extracted Data Summary */}
              {patientData.clinicalData.reportFile && !extracting && (
                <div className="animate-fade-in" style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                    <CheckCircle2 size={16} /> Data Extracted Successfully
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div style={{ fontSize: '0.625rem', color: 'var(--text-mute)', textTransform: 'uppercase' }}>Clinical Markers</div>
                      <div style={{ fontSize: '0.8125rem', color: 'var(--text-main)' }}>
                        Stage: <span style={{ color: '#E56B8A' }}>{patientData.clinicalData.tumorStage || 'N/A'}</span> • 
                        Grade: <span style={{ color: '#E56B8A' }}>{patientData.clinicalData.tumorGrade || 'N/A'}</span> • 
                        Metastasis: <span style={{ color: '#E56B8A' }}>{patientData.clinicalData.metastasis}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div style={{ fontSize: '0.625rem', color: 'var(--text-mute)', textTransform: 'uppercase' }}>Genomic Insights</div>
                      <div style={{ fontSize: '0.8125rem', color: 'var(--text-main)' }}>
                        Markers: <span style={{ color: '#34d399' }}>{Object.keys(patientData.clinicalData.extractedGenes || {}).length + (patientData.clinicalData.geneA ? 1 : 0) + (patientData.clinicalData.geneB ? 1 : 0) + (patientData.clinicalData.geneC ? 1 : 0)} Identified</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div style={{ marginTop: '0.5rem' }}>
                <button 
                  type="submit" 
                  className="btn-premium" 
                  style={{ padding: '0.875rem 2rem', opacity: patientData.clinicalData.reportFile ? 1 : 0.5 }} 
                  disabled={loading || extracting}
                >
                  {loading ? <><Loader2 className="animate-spin" size={18} /> Analyzing...</> : <>Run ML Prognosis <Activity size={18} /></>}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default StepTwo;
