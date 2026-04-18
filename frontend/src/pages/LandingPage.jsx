import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Activity, Shield, Users, Sparkles } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="premium-page" style={{ position: 'relative' }}>
      {/* Animated Background Orbs */}
      <div style={{ position: 'absolute', top: '-10%', left: '-5%', width: '40vw', height: '40vw', background: 'rgba(196,30,74,0.08)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 8s infinite alternate' }} />
      <div style={{ position: 'absolute', bottom: '10%', right: '-5%', width: '35vw', height: '35vw', background: 'rgba(229,107,138,0.06)', borderRadius: '50%', filter: 'blur(100px)', pointerEvents: 'none', animation: 'pulse 10s infinite alternate-reverse' }} />
      <div style={{ position: 'absolute', top: '40%', right: '15%', width: '15vw', height: '15vw', background: 'rgba(196,30,74,0.04)', borderRadius: '50%', filter: 'blur(60px)', pointerEvents: 'none', animation: 'pulse 12s infinite alternate' }} />

      <div className="premium-container animate-up" style={{ maxWidth: '860px' }}>
        {/* Symmetric Hero */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1.25rem', background: 'var(--accent-soft)', border: '1px solid var(--border)', borderRadius: '100px', color: 'var(--accent)', fontSize: '0.625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2em' }}>
              <Sparkles size={12} style={{ color: '#E56B8A' }} /> Precision Oncology AI
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-mute)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              Operational Status: Active — {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </div>
          </div>

          <h1 className="glow-text" style={{ fontSize: 'clamp(3rem, 6vw, 4.5rem)', fontWeight: 900, lineHeight: 1, letterSpacing: '-0.04em', marginBottom: '1.5rem' }}>
            Predicting the<br />
            <span className="medical-gradient-text" style={{ filter: 'drop-shadow(0 0 15px rgba(196,30,74,0.3))' }}>Future of Care</span>
          </h1>

          <p style={{ fontSize: '1rem', color: 'var(--text-dim)', maxWidth: '520px', margin: '0 auto 2.5rem', lineHeight: 1.6, fontWeight: 500 }}>
            Advanced machine learning for breast cancer prognosis. Analyze genomic signatures and clinical markers with state-of-the-art accuracy.
          </p>

          <button onClick={() => navigate('/step-1')} className="btn-premium" style={{ width: 'auto', padding: '1rem 2.5rem' }}>
            Start New Analysis <ArrowRight size={20} />
          </button>
        </div>

        {/* Symmetric Features Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
          {[
            { icon: Activity, color: '#E56B8A', bg: 'rgba(196,30,74,0.08)', title: 'Survival Analysis', desc: '5-year survival from deep genomic profiling.' },
            { icon: Shield, color: '#F099AC', bg: 'rgba(229,107,138,0.08)', title: 'Recurrence Risk', desc: '94.2% precision using advanced ML models.' },
            { icon: Users, color: '#D94468', bg: 'rgba(217,68,104,0.08)', title: 'Similarity Search', desc: '11,000+ historical genomic records compared.' },
          ].map(({ icon: Icon, color, bg, title, desc }) => (
            <div key={title} className="metric-card glow-border" style={{ textAlign: 'left', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ width: '48px', height: '48px', background: bg, borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={20} style={{ color }} />
              </div>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>{title}</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-dim)', lineHeight: 1.6, fontWeight: 500 }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
