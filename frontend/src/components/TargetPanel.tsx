import type { TargetRecord } from '../types';
import { RISK_COLORS, RISK_LABELS } from '../types';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';

interface TargetPanelProps {
  target: TargetRecord | null;
  onClose: () => void;
  onVerify: (detectionId: string) => void;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="font-mono" style={{ color }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="w-full h-2 rounded-full overflow-hidden" style={{ backgroundColor: `${color}22` }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${value * 100}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function TargetPanel({ target, onClose, onVerify }: TargetPanelProps) {
  if (!target) return null;

  const { detection, anomaly, acoustic_features, risk_assessment } = target;
  const riskLevel = risk_assessment?.risk_level || 'LOW';
  const riskColor = RISK_COLORS[riskLevel];

  const scoreData = [
    { name: 'Confidence', value: detection.confidence * 100, color: '#60a5fa' },
    { name: 'Anomaly', value: (anomaly?.anomaly_score || 0) * 100, color: '#f59e0b' },
    { name: 'Evidence', value: (risk_assessment?.evidence_score || 0) * 100, color: '#8b5cf6' },
    { name: 'Risk', value: (risk_assessment?.risk_score || 0) * 100, color: riskColor },
  ];

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#0f2035' }}>
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">{detection.target_id}</h2>
            <p className="text-sm text-gray-400">{detection.object_class}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none p-1"
          >
            &times;
          </button>
        </div>
        <div className="mt-2">
          <span
            className="inline-block px-3 py-1 rounded-full text-xs font-bold"
            style={{
              backgroundColor: `${riskColor}22`,
              color: riskColor,
              border: `1px solid ${riskColor}44`,
            }}
          >
            {RISK_LABELS[riskLevel]}
          </span>
        </div>
      </div>

      {/* Scores */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Detection Scores
        </h3>
        <ScoreBar label="Confidence" value={detection.confidence} color="#60a5fa" />
        <ScoreBar
          label="Anomaly Score"
          value={anomaly?.anomaly_score || 0}
          color="#f59e0b"
        />
        <ScoreBar
          label="Evidence Score"
          value={risk_assessment?.evidence_score || 0}
          color="#8b5cf6"
        />
        <ScoreBar
          label="Risk Score"
          value={risk_assessment?.risk_score || 0}
          color={riskColor}
        />
      </div>

      {/* Acoustic Features */}
      {acoustic_features && (
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Acoustic Features
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Target Intensity</div>
              <div className="font-mono text-white">
                {acoustic_features.target_intensity.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Target Area</div>
              <div className="font-mono text-white">
                {acoustic_features.target_area.toFixed(0)} px
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Shadow Length</div>
              <div className="font-mono text-white">
                {acoustic_features.shadow_length.toFixed(1)} px
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Shadow Area</div>
              <div className="font-mono text-white">
                {acoustic_features.shadow_area.toFixed(0)} px
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Target/Shadow</div>
              <div className="font-mono text-white">
                {acoustic_features.target_shadow_ratio.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2">
              <div className="text-gray-500">Seabed Texture</div>
              <div className="font-mono text-white">
                {acoustic_features.seabed_texture.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded p-2 col-span-2">
              <div className="text-gray-500">Seabed Contrast</div>
              <div className="font-mono text-white">
                {acoustic_features.seabed_contrast.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Score Chart */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Score Comparison
        </h3>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={scoreData} layout="vertical" margin={{ left: 0, right: 10 }}>
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#6b7280' }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              width={80}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
              {scoreData.map((entry, idx) => (
                <Cell key={idx} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Location */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Location
        </h3>
        <div className="text-sm space-y-1">
          <div className="flex justify-between">
            <span className="text-gray-400">Latitude</span>
            <span className="font-mono text-white">
              {detection.latitude?.toFixed(6) || 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Longitude</span>
            <span className="font-mono text-white">
              {detection.longitude?.toFixed(6) || 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Depth</span>
            <span className="font-mono text-white">
              {detection.depth != null ? `${detection.depth.toFixed(1)} m` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 mt-auto">
        <div className="flex gap-2">
          <button
            className="flex-1 px-3 py-2 rounded text-sm font-medium text-white transition-colors"
            style={{ backgroundColor: '#1b3a5e' }}
          >
            View Sonar
          </button>
          <button
            onClick={() => onVerify(detection.detection_id)}
            className="flex-1 px-3 py-2 rounded text-sm font-medium text-white transition-colors"
            style={{ backgroundColor: '#155e3a' }}
          >
            Verify
          </button>
        </div>
      </div>
    </div>
  );
}
