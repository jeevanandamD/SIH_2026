import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { surveyApi } from '../api/client';
import type { Survey } from '../types';

interface SurveyViewProps {
  onProcess: (surveyId: string) => void;
}

export default function SurveyView({ onProcess }: SurveyViewProps) {
  const navigate = useNavigate();
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [generatingDemo, setGeneratingDemo] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadSurveys();
  }, []);

  const loadSurveys = async () => {
    try {
      setLoading(true);
      const data = await surveyApi.list();
      setSurveys(data);
    } catch {
      console.error('Failed to load surveys');
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async (surveyId: string) => {
    try {
      setProcessing(surveyId);
      await surveyApi.process(surveyId);
      await loadSurveys();
      onProcess(surveyId);
      navigate('/');
    } catch {
      console.error('Failed to process survey');
    } finally {
      setProcessing(null);
    }
  };

  const handleDelete = async (surveyId: string) => {
    if (!window.confirm('Are you sure you want to delete this survey and its detections?')) {
      return;
    }
    try {
      await surveyApi.delete(surveyId);
      await loadSurveys();
      onProcess(surveyId);
    } catch {
      console.error('Failed to delete survey');
    }
  };

  const handleGenerateDemo = async () => {
    try {
      setGeneratingDemo(true);
      await surveyApi.generateDemo();
      await loadSurveys();
      onProcess('');
      navigate('/');
    } catch {
      console.error('Failed to generate demo surveys');
    } finally {
      setGeneratingDemo(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name.replace(/\.[^/.]+$/, ''));
    formData.append('vessel_id', 'Autonomous Survey Towfish SSS-01');
    formData.append('area_name', 'Offshore Survey Track A');
    formData.append('sonar_type', 'EdgeTech 4200 Dual-Frequency (400/900 kHz)');

    try {
      setUploading(true);
      const created = await surveyApi.create(formData);
      // Auto process uploaded survey
      if (created && created.survey_id) {
        await surveyApi.process(created.survey_id);
      }
      await loadSurveys();
      onProcess(created.survey_id);
      navigate('/');
    } catch {
      console.error('Failed to upload survey');
    } finally {
      setUploading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#22c55e';
      case 'processing': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#60a5fa';
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8" style={{ backgroundColor: '#0a1628' }}>
      <div className="max-w-5xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1 tracking-tight">Sonar Survey Mission Management</h1>
            <p className="text-xs text-gray-400">
              Ingest raw Side-Scan Sonar (SSS) datasets, execute multi-stage evidence fusion, and inspect targets.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerateDemo}
              disabled={generatingDemo}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-lg transition-all cursor-pointer disabled:opacity-50 flex items-center gap-2"
            >
              {generatingDemo ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Synthesizing Surveys...</span>
                </>
              ) : (
                <>
                  <span>⚡ Load Realistic Demo Surveys</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Upload Area */}
        <div
          className="border-2 border-dashed rounded-2xl p-8 mb-8 text-center transition-all hover:border-blue-500/60 bg-slate-900/40 relative overflow-hidden"
          style={{ borderColor: '#1b3a5e' }}
        >
          <input
            type="file"
            accept=".zip,.tar,.gz,.png,.jpg,.jpeg,.tif,.tiff"
            onChange={handleUpload}
            className="hidden"
            id="survey-upload"
            disabled={uploading}
          />
          <label htmlFor="survey-upload" className="cursor-pointer block">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto mb-3 text-2xl border border-blue-500/30">
              {uploading ? '⏳' : '📥'}
            </div>
            <div className="text-sm font-semibold text-white mb-1">
              {uploading ? 'Uploading & Processing SSS Survey...' : 'Drop Side-Scan Sonar dataset here or browse files'}
            </div>
            <div className="text-xs text-gray-400">
              Accepts compressed surveys (<span className="text-blue-400">.zip</span>, <span className="text-blue-400">.tar.gz</span>) or individual sonar waterfall images (<span className="text-blue-400">.png</span>, <span className="text-blue-400">.jpg</span>, <span className="text-blue-400">.tif</span>)
            </div>
          </label>
        </div>

        {/* Survey List */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
              Survey Missions ({surveys.length})
            </h2>
            <button
              onClick={loadSurveys}
              className="text-xs text-gray-400 hover:text-white cursor-pointer"
            >
              ↻ Refresh
            </button>
          </div>

          {loading ? (
            <div className="text-center py-16 text-gray-400">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <div className="text-xs">Loading surveys...</div>
            </div>
          ) : surveys.length === 0 ? (
            <div className="text-center py-16 bg-slate-900/30 rounded-2xl border border-slate-800">
              <div className="text-3xl mb-2">🌊</div>
              <div className="text-sm font-medium text-gray-300 mb-1">No active surveys in database</div>
              <div className="text-xs text-gray-500 mb-4">Upload a sonar file or generate demo missions to explore.</div>
              <button
                onClick={handleGenerateDemo}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold cursor-pointer"
              >
                Generate Demo Surveys
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {surveys.map((survey) => (
                <div
                  key={survey.survey_id}
                  className="rounded-2xl p-5 border transition-all hover:border-slate-600 shadow-lg"
                  style={{
                    backgroundColor: '#0f2035',
                    borderColor: '#1b3a5e',
                  }}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-base font-bold text-white tracking-wide">{survey.name}</h3>
                        <span
                          className="text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider"
                          style={{
                            color: statusColor(survey.status),
                            backgroundColor: `${statusColor(survey.status)}18`,
                            border: `1px solid ${statusColor(survey.status)}40`,
                          }}
                        >
                          {survey.status}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-400 mt-3 pt-3 border-t border-slate-800">
                        <div>
                          <span className="text-gray-500 block text-[10px] uppercase">Survey Area</span>
                          <span className="text-gray-200 font-medium">{survey.area_name || 'Offshore Sector'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[10px] uppercase">Vessel / AUV</span>
                          <span className="text-gray-200 font-medium truncate block">{survey.vessel_id || 'AUV Platform'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[10px] uppercase">Sonar Sensor</span>
                          <span className="text-gray-200 font-medium truncate block">{survey.sonar_type || 'Side-Scan Sonar'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[10px] uppercase">Images / Detections</span>
                          <span className="text-blue-400 font-semibold">
                            {survey.image_count || 0} scans &bull; {survey.detection_count || 0} targets
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-slate-800">
                      {survey.status === 'uploaded' && (
                        <button
                          onClick={() => handleProcess(survey.survey_id)}
                          disabled={processing === survey.survey_id}
                          className="px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all disabled:opacity-50 cursor-pointer hover:bg-emerald-600"
                          style={{ backgroundColor: '#155e3a' }}
                        >
                          {processing === survey.survey_id ? 'Processing...' : 'Run Pipeline'}
                        </button>
                      )}
                      {survey.status === 'completed' && (
                        <button
                          onClick={() => {
                            onProcess(survey.survey_id);
                            navigate('/');
                          }}
                          className="px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all cursor-pointer hover:bg-blue-600 shadow"
                          style={{ backgroundColor: '#1b3a5e' }}
                        >
                          Explore GIS View &rarr;
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(survey.survey_id)}
                        className="px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 border border-rose-900/40 transition-colors cursor-pointer"
                        title="Delete Survey"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
