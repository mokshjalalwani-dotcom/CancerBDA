import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePatient } from '../context/PatientContext';
import StepProgress from '../components/StepProgress';
import { generateReportPDF } from '../services/api';
import {
  TrendingUp, ShieldCheck, AlertTriangle, Users,
  Lightbulb, RefreshCcw, Heart, Loader2, Activity, FileDown, PlusCircle, Dna, Zap
} from 'lucide-react';

const ResultPage = () => {
  const location = useLocation();
  const { results: contextResults, patientData, resetData } = usePatient();
  const navigate = useNavigate();
  const [isDownloading, setIsDownloading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);

  // Prioritize results from navigation state, then context
  const results = location.state?.results || contextResults;

  const loadingStages = [
    "SEQUENCING GENOMIC SIGNATURES...",
    "MATCHING HISTORICAL COHORTS...",
    "SYNTHESIZING DIAGNOSTIC INTELLIGENCE...",
    "STABILIZING FINAL PROGNOSIS..."
  ];

  console.log("RESULT PAGE: results from state/context is:", results);
  if (results) console.log("RESULT PAGE: keys are:", Object.keys(results));

  useEffect(() => {
    if (!results) {
      const interval = setInterval(() => {
        setLoadingStage(prev => (prev + 1) % loadingStages.length);
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [results]);

  const handleDownloadPDF = async () => {
    if (!results) return;
    setIsDownloading(true);
    try {
      const response = await generateReportPDF({
        ...results,
        patient_info: patientData.generalInfo,
        clinical_info: patientData.clinicalData
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Prognosis_Report_${results.case_id || 'Analysis'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('PDF Download failed:', error);
      alert('Failed to generate PDF. Please ensure the backend is running on the correct port.');
    } finally {
      setIsDownloading(false);
    }
  };

  useEffect(() => {
    // Longer timeout to allow premium loading animation to show (8 seconds)
    const t = setTimeout(() => { 
      if (!results) navigate('/step-2'); 
    }, 8000);
    return () => clearTimeout(t);
  }, [results, navigate]);

  const handleStartOver = () => { resetData(); navigate('/step-1'); };

  if (!results || typeof results !== 'object') {
    return (
      <div className="premium-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', maxWidth: '400px' }}>
          <div style={{ position: 'relative', width: '80px', height: '80px', margin: '0 auto 2rem' }}>
            <div style={{ position: 'absolute', inset: 0, border: '4px solid rgba(196, 30, 74, 0.15)', borderRadius: '50%' }}></div>
            <div style={{ position: 'absolute', inset: 0, border: '4px solid var(--accent)', borderRadius: '50%', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }}></div>
            <div style={{ position: 'absolute', inset: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
              <Dna size={32} className="animate-pulse" />
            </div>
          </div>
          <h2 style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--accent)', letterSpacing: '0.2em', marginBottom: '1rem', textTransform: 'uppercase' }}>
            {loadingStages[loadingStage]}
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', lineHeight: 1.5, opacity: 0.8, marginBottom: '2rem' }}>
            Our neural networks are comparing your unique genomic profile against 11,402 validated clinical cases.
          </p>
          <button 
            onClick={() => navigate('/step-2')}
            style={{ 
              background: 'rgba(255, 255, 255, 0.05)', 
              border: '1px solid var(--border)', 
              color: 'var(--text-dim)', 
              padding: '0.5rem 1rem', 
              borderRadius: '0.5rem', 
              fontSize: '0.75rem', 
              fontWeight: 600, 
              cursor: 'pointer' 
            }}
          >
            Cancel & Go Back
          </button>
        </div>
      </div>
    );
  }

  const s = results?.survival_probability ?? 0;
  const r = results?.recurrence_probability ?? 0;
  const a = results?.aggressiveness_score ?? 0;
  const patients = Array.isArray(results?.similar_patients) ? results.similar_patients : [];
  const interpretation = results?.treatment_insight?.interpretation || "Synthesizing genomic patterns...";
  const summary = results?.treatment_insight?.diagnostic_summary;

  const riskColor = (v, inv) => { 
    if (v === undefined) return 'var(--text-mute)';
    const x = inv ? 100 - v : v; 
    return x < 30 ? '#34d399' : x < 60 ? '#fbbf24' : '#f87171'; 
  };

  return (
    <div className="premium-page" style={{ padding: '2rem 1rem' }}>
      <div className="premium-container animate-up" style={{ maxWidth: '800px' }}>
        <StepProgress currentStep={3} />

        <div className="premium-card interactive-card stagger-1" style={{ padding: '2.5rem', gap: '0' }}>
          {/* Symmetric Header */}
          <div className="page-header" style={{ marginBottom: '3rem' }}>
            <h2 className="page-title glow-text" style={{ fontSize: '2.75rem', marginBottom: '0.75rem', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>Prognosis Analysis</h2>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
              <div style={{ padding: '0.4rem 1rem', background: 'var(--accent-soft)', borderRadius: '100px', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.875rem', color: 'var(--accent-light)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{patientData?.generalInfo?.fullName || "Patient Profile"}</span>
              </div>
              <span style={{ color: 'var(--text-mute)', opacity: 0.3 }}>—</span>
              <div style={{ padding: '0.4rem 1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '100px', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-dim)', fontWeight: 600 }}>ID: {results?.case_id || "REAL-TIME-ANALYSIS"}</span>
              </div>
            </div>
          </div>

          {/* Metrics Grid - Balanced and Real-time */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem', marginBottom: '3.5rem' }}>
            {[
              { label: 'SURVIVAL PROBABILITY', value: s !== undefined ? `${s}%` : '--', icon: Heart, color: '#E56B8A', risk: riskColor(s, true), conf: results?.survival_confidence },
              { label: 'AGGRESSIVENESS INDEX', value: a !== undefined ? `${a}/100` : '--', icon: Activity, color: '#D94468', risk: riskColor(a, false), conf: null },
              { label: 'RECURRENCE RISK', value: r !== undefined ? `${r}%` : '--', icon: TrendingUp, color: '#F099AC', risk: riskColor(r, false), conf: results?.recurrence_confidence },
            ].map(({ label, value, icon: Icon, color, risk, conf }) => (
              <div key={label} className="metric-card glow-border" style={{ padding: '1.75rem' }}>
                <div style={{ width: '44px', height: '44px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
                  <Icon size={22} style={{ color }} />
                </div>
                <div style={{ fontSize: '0.625rem', fontWeight: 800, color: 'var(--text-mute)', textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem' }}>{label}</div>
                <div className="glow-text" style={{ fontSize: '2.5rem', fontWeight: 900, color: risk, lineHeight: 1 }}>{value}</div>
                {conf != null && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                    <ShieldCheck size={12} style={{ opacity: 0.6 }} /> Confidence: <span style={{ color: conf > 70 ? '#34d399' : conf > 30 ? '#fbbf24' : '#f87171' }}>{conf}%</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Diagnostic Intelligence - PRIORITY POSITION */}
          <div style={{ 
            padding: '2.5rem', 
            background: 'rgba(196, 30, 74, 0.05)',
            borderRadius: '1.5rem',
            border: '1px solid var(--accent-soft)',
            marginBottom: '3rem',
            position: 'relative',
            overflow: 'hidden'
          }} className="animate-up stagger-2">
            <div style={{ position: 'absolute', top: 0, right: 0, padding: '1rem' }}>
               <ShieldCheck size={24} color="var(--accent)" style={{ opacity: 0.3 }} />
            </div>

            <h3 style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--text-main)', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Zap size={20} color="var(--accent)" /> Diagnostic Intelligence
            </h3>
            
            <p style={{ fontSize: '1.125rem', color: 'var(--text-main)', lineHeight: 1.7, marginBottom: '2rem', fontWeight: 500 }}>
              {interpretation}
            </p>

            {summary && (
              <div style={{ padding: '1.25rem', background: 'rgba(20, 14, 30, 0.4)', borderRadius: '1rem', borderLeft: '3px solid var(--accent)', marginBottom: '2rem' }}>
                <div style={{ fontSize: '0.625rem', fontWeight: 800, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>Biological Summary</div>
                <p style={{ fontSize: '0.9375rem', color: 'var(--text-dim)', lineHeight: 1.6, margin: 0, fontStyle: 'italic' }}>
                  "{summary}"
                </p>
              </div>
            )}

            <div style={{ display: 'flex', gap: '1.25rem' }}>
              <button 
                className="btn-premium download-btn-animation"
                onClick={handleDownloadPDF}
                disabled={isDownloading}
                style={{ flex: 1.2, height: '4rem', fontSize: '0.9375rem', letterSpacing: '0.02em' }}
              >
                <FileDown size={22} /> {isDownloading ? 'SYNTHESIZING REPORT...' : 'DOWNLOAD CLINICAL REPORT'}
              </button>
              <button 
                className="secondary-button interactive-card"
                onClick={handleStartOver}
                style={{ 
                  flex: 0.8, 
                  height: '4rem', 
                  borderRadius: '0.875rem', 
                  fontWeight: 700, 
                  fontSize: '0.9375rem',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.75rem'
                }}
              >
                <PlusCircle size={22} /> NEW ANALYSIS
              </button>
            </div>
          </div>

          {/* Similarity Synthesis - Centered Flex */}
          <div className="animate-up stagger-3" style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
               <div style={{ height: '1px', flex: 1, background: 'linear-gradient(90deg, transparent, var(--border))' }}></div>
               <Users size={18} color="var(--text-mute)" />
               <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em', color: 'var(--text-mute)' }}>Similarity Synthesis</span>
               <div style={{ height: '1px', flex: 1, background: 'linear-gradient(270deg, transparent, var(--border))' }}></div>
            </div>
            
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'center' }}>
              {patients.length > 0 ? patients.slice(0, 3).map((p, i) => (
                <div key={i} className="metric-card interactive-card" style={{ minWidth: '220px', flex: '1', textAlign: 'left', padding: '1.25rem', background: 'rgba(20, 14, 30, 0.4)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 700 }}>{p.case_id}</span>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 900, color: '#E56B8A' }}>
                      {((p.similarity || 0) * 100).toFixed(0)}% Match
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                     {p.high_risk_flag === 1 && <span className="status-badge high-risk" style={{ fontSize: '0.625rem' }}>High Risk</span>}
                     {p.recurrence_label === 1 && <span className="status-badge recurrence" style={{ fontSize: '0.625rem' }}>Recurrence</span>}
                  </div>
                </div>
              )) : (
                <div style={{ color: 'var(--text-mute)', fontSize: '0.875rem', fontStyle: 'italic', padding: '2rem' }}>No matching cohorts identified.</div>
              )}
            </div>
          </div>
        </div>

        {/* Genomic Recovery Table - The "Summary at the end" */}
        {results?.treatment_insight?.genomic_recovery_insights?.length > 0 && (
          <div className="premium-card animate-up stagger-4" style={{ marginTop: '1.25rem', padding: '2rem' }}>
             <h4 style={{ fontSize: '0.875rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '1.5rem', color: 'var(--text-mute)', display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
               <Dna size={16} /> Genomic Recovery Benchmarks
             </h4>
            <div style={{ background: 'var(--bg-field)', borderRadius: '1.25rem', overflow: 'hidden', border: '1px solid var(--border)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                    <th style={{ padding: '1.25rem', textAlign: 'left', color: 'var(--text-dim)', fontWeight: 700, fontSize: '0.75rem' }}>Dominant Marker</th>
                    <th style={{ padding: '1.25rem', textAlign: 'right', color: 'var(--text-dim)', fontWeight: 700, fontSize: '0.75rem' }}>Cohort Survival Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {results?.treatment_insight?.genomic_recovery_insights?.map((g, idx) => (
                    <tr key={idx} className="recovery-row" style={{ borderTop: '1px solid var(--border)' }}>
                      <td style={{ padding: '1.25rem', fontWeight: 700, color: 'var(--accent)' }}>{g?.gene_id}</td>
                      <td style={{ padding: '1.25rem', textAlign: 'right' }}>
                        <span style={{ 
                          padding: '0.375rem 0.75rem', borderRadius: '6px', fontWeight: 800, fontSize: '0.875rem',
                          background: g?.recovery_rate > 70 ? 'rgba(52, 211, 153, 0.1)' : 'rgba(251, 191, 36, 0.1)',
                          color: g?.recovery_rate > 70 ? '#34d399' : '#fbbf24'
                        }}>
                          {g?.recovery_rate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div style={{ marginTop: '3rem', padding: '1rem', borderTop: '1px solid var(--border)', opacity: 0.4 }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--text-mute)', textAlign: 'center', lineHeight: 1.8 }}>
            <strong>Confidential Medical Research Report:</strong> This synthesis is AI-generated for oncology research. 
            Final diagnosis and therapeutic planning must be verified by a board-certified specialist.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResultPage;
