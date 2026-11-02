import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const PurifierContext = createContext();

export function PurifierProvider({ children }) {
  const [purifiers, setPurifiers] = useState([]);
  const [selectedPurifier, setSelectedPurifier] = useState(null);
  const [activeSimulation, setActiveSimulation] = useState(null);
  const [readings, setReadings] = useState([]);
  const [latestDiagnosis, setLatestDiagnosis] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadPurifiers = useCallback(async () => {
    try {
      setLoading(true);
      const list = await api.getPurifiers();
      setPurifiers(list);
      if (list.length > 0 && !selectedPurifier) {
        setSelectedPurifier(list[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedPurifier]);

  useEffect(() => {
    loadPurifiers();
  }, []);

  // When selected purifier changes, create or load simulation
  const loadSimulationData = useCallback(async (purifierId) => {
    if (!purifierId) return;
    try {
      setLoading(true);
      // Start or get active simulation for this purifier
      const sim = await api.createSimulation({
        purifier_profile_id: purifierId,
        degradation_type: selectedPurifier?.degradation_type || 'linear',
        duration_days: 60.0,
        random_seed: 42,
      });
      setActiveSimulation(sim);

      // Fetch readings
      const rList = await api.getReadings(sim.id);
      setReadings(rList);

      // Fetch diagnosis
      const diag = await api.predict(sim.id);
      setLatestDiagnosis(diag);

      // Fetch alerts
      const aList = await api.getAlerts(sim.id);
      setAlerts(aList);
    } catch (err) {
      console.warn("Could not load simulation data:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedPurifier]);

  useEffect(() => {
    if (selectedPurifier?.id) {
      loadSimulationData(selectedPurifier.id);
    }
  }, [selectedPurifier?.id]);

  const refreshDiagnosis = async () => {
    if (!activeSimulation?.id) return;
    try {
      const diag = await api.predict(activeSimulation.id);
      setLatestDiagnosis(diag);
      const aList = await api.getAlerts(activeSimulation.id);
      setAlerts(aList);
    } catch (err) {
      console.error("Refresh diagnosis failed:", err);
    }
  };

  const handleInjectFault = async (faultType, startDay, magnitude = 0.5) => {
    if (!activeSimulation?.id) return;
    try {
      await api.injectFault(activeSimulation.id, {
        fault_type: faultType,
        start_day: startDay,
        magnitude: magnitude
      });
      // Re-run simulation with fault
      const sim = await api.createSimulation({
        purifier_profile_id: selectedPurifier.id,
        degradation_type: selectedPurifier.degradation_type,
        fault_type: faultType,
        fault_day: startDay,
        fault_magnitude: magnitude,
        duration_days: 60.0,
      });
      setActiveSimulation(sim);
      const rList = await api.getReadings(sim.id);
      setReadings(rList);
      const diag = await api.predict(sim.id);
      setLatestDiagnosis(diag);
      const aList = await api.getAlerts(sim.id);
      setAlerts(aList);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <PurifierContext.Provider
      value={{
        purifiers,
        selectedPurifier,
        setSelectedPurifier,
        activeSimulation,
        setActiveSimulation,
        readings,
        setReadings,
        latestDiagnosis,
        alerts,
        loading,
        error,
        loadPurifiers,
        refreshDiagnosis,
        handleInjectFault,
        loadSimulationData,
      }}
    >
      {children}
    </PurifierContext.Provider>
  );
}

export function usePurifier() {
  const context = useContext(PurifierContext);
  if (!context) {
    throw new Error('usePurifier must be used within a PurifierProvider');
  }
  return context;
}
