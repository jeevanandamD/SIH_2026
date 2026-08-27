import { useState } from 'react';

interface VerifyDialogProps {
  detectionId: string | null;
  onClose: () => void;
  onSubmit: (detectionId: string, data: {
    expert_label: string;
    correction?: string;
    comments?: string;
  }) => void;
}

const LABELS = [
  { value: 'correct', label: 'Correct', color: '#22c55e' },
  { value: 'incorrect', label: 'Incorrect', color: '#ef4444' },
  { value: 'natural_feature', label: 'Natural Feature', color: '#6b7280' },
  { value: 'marine_debris', label: 'Marine Debris', color: '#f59e0b' },
  { value: 'wreckage', label: 'Wreckage', color: '#8b5cf6' },
  { value: 'new_category', label: 'New Category', color: '#06b6d4' },
];

export default function VerifyDialog({ detectionId, onClose, onSubmit }: VerifyDialogProps) {
  const [selectedLabel, setSelectedLabel] = useState('');
  const [correction, setCorrection] = useState('');
  const [comments, setComments] = useState('');

  if (!detectionId) return null;

  const handleSubmit = () => {
    if (!selectedLabel) return;
    onSubmit(detectionId, {
      expert_label: selectedLabel,
      correction: correction || undefined,
      comments: comments || undefined,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Dialog */}
      <div
        className="relative rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        style={{ backgroundColor: '#0f2035', border: '1px solid #1b3a5e' }}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Verify Detection</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-xl leading-none"
            >
              &times;
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            ID: <span className="font-mono">{detectionId}</span>
          </p>
        </div>

        {/* Label Selection */}
        <div className="p-4">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">
            Classification
          </label>
          <div className="grid grid-cols-2 gap-2">
            {LABELS.map((label) => (
              <button
                key={label.value}
                onClick={() => setSelectedLabel(label.value)}
                className={`p-2 rounded-lg text-sm text-left transition-all border ${
                  selectedLabel === label.value
                    ? 'border-opacity-50 bg-opacity-15'
                    : 'border-gray-700 bg-gray-800/30 hover:bg-gray-800/60'
                }`}
                style={
                  selectedLabel === label.value
                    ? {
                        borderColor: label.color,
                        backgroundColor: `${label.color}15`,
                        color: label.color,
                      }
                    : undefined
                }
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: label.color }}
                  />
                  <span>{label.label}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Correction (if incorrect/new) */}
        {(selectedLabel === 'incorrect' || selectedLabel === 'new_category') && (
          <div className="px-4 pb-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
              Correct Label
            </label>
            <input
              type="text"
              value={correction}
              onChange={(e) => setCorrection(e.target.value)}
              placeholder="Enter correct classification..."
              className="w-full px-3 py-2 rounded-lg text-sm text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
              style={{ backgroundColor: '#0a1628' }}
            />
          </div>
        )}

        {/* Comments */}
        <div className="px-4 pb-2">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
            Comments
          </label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Optional notes..."
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-sm text-white border border-gray-700 focus:border-blue-500 focus:outline-none resize-none"
            style={{ backgroundColor: '#0a1628' }}
          />
        </div>

        {/* Footer */}
        <div className="p-4 flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedLabel}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ backgroundColor: selectedLabel ? '#155e3a' : '#1b3a5e' }}
          >
            Submit Verification
          </button>
        </div>
      </div>
    </div>
  );
}
