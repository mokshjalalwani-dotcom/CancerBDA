import React from 'react';
import { Check } from 'lucide-react';

const StepProgress = ({ currentStep }) => {
  const steps = [
    { id: 1, name: 'General Info' },
    { id: 2, name: 'Clinical Data' },
    { id: 3, name: 'Results' },
  ];

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <div className={`step-indicator ${
                currentStep > step.id ? 'step-completed' : currentStep === step.id ? 'step-active' : 'step-inactive'
              }`}>
                {currentStep > step.id ? <Check size={18} strokeWidth={3} /> : step.id}
              </div>
              <span style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                letterSpacing: '0.08em',
                color: currentStep === step.id ? '#E56B8A' : currentStep > step.id ? '#34d399' : '#475569'
              }}>
                {step.name}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div style={{
                width: '6rem',
                height: '2px',
                borderRadius: '1px',
                marginTop: '-1.25rem',
                background: currentStep > step.id ? '#10b981' : 'rgba(99,102,241,0.1)'
              }} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default StepProgress;
