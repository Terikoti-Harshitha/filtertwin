import React, { useState, useEffect } from 'react';
import {
  Wrench,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  FileCheck
} from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import api from '../services/api';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Maintenance() {
  const { selectedPurifier, latestDiagnosis, loadSimulationData } = usePurifier();

  const [guides, setGuides] = useState([]);
  const [selectedGuide, setSelectedGuide] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [technicianNotes, setTechnicianNotes] = useState('Standard cartridge replacement completed and lines flushed.');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const gList = await api.getGuides();
        setGuides(gList);
        if (gList.length > 0) setSelectedGuide(gList[0]);

        const rList = await api.getMaintenanceHistory(selectedPurifier?.id);
        setRecords(rList);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, [selectedPurifier?.id]);

  const toggleStep = (stepNumber) => {
    if (completedSteps.includes(stepNumber)) {
      setCompletedSteps(completedSteps.filter(s => s !== stepNumber));
    } else {
      setCompletedSteps([...completedSteps, stepNumber]);
    }
  };

  const handleRecordMaintenance = async () => {
    if (!selectedPurifier?.id || !selectedGuide) return;
    setLoading(true);
    setSubmitSuccess(false);
    try {
      await api.recordMaintenance({
        purifier_profile_id: selectedPurifier.id,
        guide_id: selectedGuide.id,
        replacement_type: selectedGuide.filter_type,
        technician_notes: technicianNotes,
        checklist_completed: completedSteps,
        reset_baseline_flow: 2.1,
        reset_baseline_rejection: 96.5,
      });

      setSubmitSuccess(true);
      setCompletedSteps([]);

      // Refresh records
      const rList = await api.getMaintenanceHistory(selectedPurifier.id);
      setRecords(rList);

      // Re-baseline simulation
      await loadSimulationData(selectedPurifier.id);
    } catch (err) {
      alert(`Error recording maintenance: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const allStepsRequired = selectedGuide?.checklist_steps?.map(s => s.step_number) || [];
  const isComplete = allStepsRequired.length > 0 && allStepsRequired.every(num => completedSteps.includes(num));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Guided Maintenance Center</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Standard manufacturer replacement procedures, interactive checklist verification, and baseline reset.
          </p>
        </div>

        {/* Guide Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium">Procedure Guide:</label>
          <select
            value={selectedGuide?.id || ''}
            onChange={(e) => {
              const g = guides.find(x => x.id === e.target.value);
              if (g) {
                setSelectedGuide(g);
                setCompletedSteps([]);
              }
            }}
            className="bg-slate-900 border border-slate-700 text-xs rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500 font-medium"
          >
            {guides.map(g => (
              <option key={g.id} value={g.id}>{g.title}</option>
            ))}
          </select>
        </div>
      </div>

      {submitSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Maintenance successfully verified and persisted! Operational telemetry baseline has been reset.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Interactive Step-by-Step Checklist */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-5 lg:col-span-2">
          <div>
            <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
              <Wrench className="w-4 h-4 text-teal-400" />
              <span>{selectedGuide?.title || 'Maintenance Checklist'}</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {selectedGuide?.description} • Estimated duration: ~{selectedGuide?.estimated_minutes} minutes
            </p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono text-slate-400">
              <span>Checklist Progress</span>
              <span className="font-bold text-teal-400">
                {completedSteps.length} / {allStepsRequired.length} Steps Completed
              </span>
            </div>
            <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 rounded-full transition-all duration-300"
                style={{ width: `${allStepsRequired.length > 0 ? (completedSteps.length / allStepsRequired.length) * 100 : 0}%` }}
              ></div>
            </div>
          </div>

          {/* Checklist Items */}
          <div className="space-y-3">
            {selectedGuide?.checklist_steps?.map((step) => {
              const checked = completedSteps.includes(step.step_number);
              return (
                <div
                  key={step.step_number}
                  onClick={() => toggleStep(step.step_number)}
                  className={`p-4 rounded-2xl border transition cursor-pointer flex items-start gap-3.5 ${
                    checked
                      ? 'bg-teal-950/20 border-teal-500/40 text-white'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition ${
                    checked ? 'bg-teal-500 border-teal-500 text-slate-950' : 'border-slate-700 bg-slate-900'
                  }`}>
                    {checked && <CheckCircle2 className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                  <div>
                    <div className="text-xs font-bold flex items-center gap-2">
                      <span className="text-slate-500 font-mono">Step {step.step_number}:</span>
                      <span>{step.title}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{step.instruction}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Technician Sign-off */}
          <div className="pt-4 border-t border-slate-800 space-y-3">
            <label className="text-xs font-medium text-slate-300">Technician Sign-Off Notes</label>
            <textarea
              rows="2"
              value={technicianNotes}
              onChange={(e) => setTechnicianNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-3 text-slate-200 focus:outline-none focus:border-teal-500 font-sans"
              placeholder="Record serial numbers, flush observations, or filter lot info..."
            ></textarea>

            <button
              onClick={handleRecordMaintenance}
              disabled={!isComplete || loading}
              className="w-full py-3 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <FileCheck className="w-4 h-4" />
              <span>{isComplete ? 'Confirm Replacement & Reset Baseline' : 'Complete All Steps to Sign Off'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Historical Maintenance Log */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-400" />
            <span>Replacement History Log</span>
          </h2>

          <div className="space-y-3">
            {records.length > 0 ? (
              records.map((r) => (
                <div key={r.id} className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{r.replacement_type}</span>
                    <span className="text-[10px] text-teal-400 font-mono">
                      {new Date(r.completed_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{r.technician_notes}</p>
                  <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-900 flex justify-between">
                    <span>Baseline Flow: {r.reset_baseline_flow} LPM</span>
                    <span>Rejection: {r.reset_baseline_rejection}%</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 italic">No previous maintenance events recorded.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
