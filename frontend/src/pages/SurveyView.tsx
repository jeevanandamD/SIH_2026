import { useState, useEffect } from 'react';
import { surveyApi } from '../api/client';
import type { Survey } from '../types';

interface SurveyViewProps {
  onProcess: (surveyId: string) => void;
}

export default function SurveyView({ onProcess }: SurveyViewProps) {
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);

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
    } catch {
      console.error('Failed to process survey');
    } finally {
      setProcessing(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name.replace(/\.[^/.]+$/, ''));

    try {
      await surveyApi.create(formData);
      await loadSurveys();
    } catch {
      console.error('Failed to upload survey');
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#22c55e';
      case 'processing': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: '#0a1628' }}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-1">Survey Management</h1>
          <p className="text-sm text-gray-400">Upload, manage, and process sonar surveys</p>
        </div>

        {/* Upload Area */}
        <div
          className="border-2 border-dashed rounded-xl p-8 mb-8 text-center transition-colors hover:border-blue-500/50"
          style={{ borderColor: '#1b3a5e' }}
        >
          <input
            type="file"
            accept=".zip,.tar,.gz,.png,.jpg"
            onChange={handleUpload}
            className="hidden"
            id="survey-upload"
          />
          <label htmlFor="survey-upload" className="cursor-pointer">
            <div className="text-4xl mb-3 text-gray-600">+</div>
            <div className="text-sm text-gray-400">
              Drop sonar survey data here or <span className="text-blue-400">browse</span>
            </div>
            <div className="text-[10px] text-gray-600 mt-1">
              Accepts .zip, .tar.gz, or individual sonar images
            </div>
          </label>
        </div>

        {/* Survey List */}
        <div>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Surveys ({surveys.length})
          </h2>

          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading surveys...</div>
          ) : surveys.length === 0 ? (
            <div className="text-center py-12 text-gray-600">
              No surveys yet. Upload sonar data to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {surveys.map((survey) => (
                <div
                  key={survey.survey_id}
                  className="rounded-xl p-4 border"
                  style={{
                    backgroundColor: '#0f2035',
                    borderColor: '#1b3a5e',
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="text-sm font-bold text-white">{survey.name}</h3>
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase"
                          style={{
                            color: statusColor(survey.status),
                            backgroundColor: `${statusColor(survey.status)}15`,
                            border: `1px solid ${statusColor(survey.status)}33`,
                          }}
                        >
                          {survey.status}
                        </span>
                      </div>
                      <div className="flex gap-4 mt-1 text-xs text-gray-500">
                        {survey.area_name && <span>Area: {survey.area_name}</span>}
                        {survey.sonar_type && <span>Sonar: {survey.sonar_type}</span>}
                        {survey.image_count != null && <span>Images: {survey.image_count}</span>}
                        {survey.detection_count != null && (
                          <span>Detections: {survey.detection_count}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {survey.status === 'uploaded' && (
                        <button
                          onClick={() => handleProcess(survey.survey_id)}
                          disabled={processing === survey.survey_id}
                          className="px-4 py-2 rounded-lg text-xs font-medium text-white transition-colors disabled:opacity-50"
                          style={{ backgroundColor: '#155e3a' }}
                        >
                          {processing === survey.survey_id ? 'Processing...' : 'Process'}
                        </button>
                      )}
                      {survey.status === 'completed' && (
                        <button
                          onClick={() => onProcess(survey.survey_id)}
                          className="px-4 py-2 rounded-lg text-xs font-medium text-white transition-colors"
                          style={{ backgroundColor: '#1b3a5e' }}
                        >
                          View Results
                        </button>
                      )}
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
