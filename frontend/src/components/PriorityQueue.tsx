import type { PriorityTarget } from '../types';
import { RISK_COLORS } from '../types';

interface PriorityQueueProps {
  targets: PriorityTarget[];
  onSelect: (detectionId: string) => void;
  selectedId: string | null;
}

export default function PriorityQueue({ targets, onSelect, selectedId }: PriorityQueueProps) {
  if (targets.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        No targets detected yet.
      </div>
    );
  }

  return (
    <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
      <div className="p-3 space-y-2">
        {targets.map((target) => {
          const riskColor = RISK_COLORS[target.risk_level];
          const isActive = target.detection_id === selectedId;

          return (
            <button
              key={target.detection_id}
              onClick={() => onSelect(target.detection_id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                isActive
                  ? 'border-blue-500/50 bg-blue-500/10'
                  : 'border-gray-700/50 bg-gray-800/30 hover:bg-gray-800/60 hover:border-gray-600/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{
                    backgroundColor: `${riskColor}22`,
                    color: riskColor,
                    border: `1px solid ${riskColor}44`,
                  }}
                >
                  {target.priority}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white truncate">
                      {target.target_id}
                    </span>
                    <span
                      className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                      style={{
                        backgroundColor: `${riskColor}22`,
                        color: riskColor,
                      }}
                    >
                      {target.risk_level}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 truncate">
                    {target.object_class}
                  </div>
                  <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
                    <span>
                      Conf: <span className="text-gray-300 font-mono">{(target.confidence * 100).toFixed(0)}%</span>
                    </span>
                    <span>
                      Evidence: <span className="text-gray-300 font-mono">{(target.evidence_score * 100).toFixed(0)}%</span>
                    </span>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
