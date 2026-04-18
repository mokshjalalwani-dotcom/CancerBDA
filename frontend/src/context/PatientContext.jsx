import React, { createContext, useContext, useState } from 'react';

const PatientContext = createContext();

export const usePatient = () => {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error('usePatient must be used within a PatientProvider');
  }
  return context;
};

export const PatientProvider = ({ children }) => {
  const [patientData, setPatientData] = useState({
    generalInfo: {
      fullName: '',
      age: '',
      gender: '',
      contactNumber: '',
      hospitalId: ''
    },
    clinicalData: {
      tumorStage: '',
      tumorGrade: '',
      metastasis: 'No',
      geneA: '',
      geneB: '',
      geneC: '',
      reportFile: null
    }
  });

  const [results, setResults] = useState(null);

  const updateGeneralInfo = (data) => {
    setPatientData(prev => ({
      ...prev,
      generalInfo: { ...prev.generalInfo, ...data }
    }));
  };

  const updateClinicalData = (data) => {
    setPatientData(prev => ({
      ...prev,
      clinicalData: { ...prev.clinicalData, ...data }
    }));
  };

  const resetData = () => {
    setPatientData({
      generalInfo: { fullName: '', age: '', gender: '', contactNumber: '', hospitalId: '' },
      clinicalData: { tumorStage: '', tumorGrade: '', metastasis: 'No', geneA: '', geneB: '', geneC: '', reportFile: null }
    });
    setResults(null);
  };

  return (
    <PatientContext.Provider value={{ 
      patientData, 
      updateGeneralInfo, 
      updateClinicalData, 
      results, 
      setResults,
      resetData
    }}>
      {children}
    </PatientContext.Provider>
  );
};
