import { useState } from 'react';
import type { Detection } from '../types';

interface SonarOverlayProps {
  detection: Detection | null;
  onClose: () => void;
}

export default function SonarOverlay({ detection, onClose }: SonarOverlayProps) {
  const [showBBox, setShowBBox] = useState(true);
  const [zoom, setZoom] = useState(1);

  if (!detection) return null;

  const { bbox, image_path, object_class, confidence, target_id } = detection;
  const imgSrc = image_path || `/api/detections/${detection.detection_id}/crop`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} />
      <div
        className="relative rounded-2xl shadow-2xl max-w-3xl w-full mx-auto overflow-hidden flex flex-col max-h-[92vh] border"
        style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between flex-shrink-0 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-bold text-sm">
              SSS
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>Waterfall Acoustic Imagery</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 font-mono">
                  {target_id}
                </span>
              </h2>
              <p className="text-xs text-gray-400">
                Target: <span className="text-blue-300 capitalize">{object_class.replace('_', ' ')}</span> | Detection Confidence: <span className="font-mono text-emerald-400">{(confidence * 100).toFixed(1)}%</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowBBox(!showBBox)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors cursor-pointer border ${
                showBBox
                  ? 'bg-blue-600/30 text-blue-300 border-blue-500/50'
                  : 'bg-gray-800 text-gray-400 border-gray-700'
              }`}
            >
              {showBBox ? 'BBox Visible' : 'BBox Hidden'}
            </button>
            <button
              onClick={() => setZoom(zoom === 1 ? 1.5 : zoom === 1.5 ? 2 : 1)}
              className="px-3 py-1 rounded text-xs font-medium bg-gray-800 text-gray-300 border border-gray-700 hover:border-gray-500 cursor-pointer"
            >
              Zoom {zoom}x
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl leading-none p-1 ml-2 cursor-pointer"
            >
              &times;
            </button>
          </div>
        </div>

        {/* Image Display Area */}
        <div className="p-4 flex-1 overflow-auto flex items-center justify-center bg-black/70">
          <div
            className="relative rounded-xl overflow-hidden shadow-inner border border-slate-800 transition-transform duration-200"
            style={{
              backgroundColor: '#070f1a',
              transform: `scale(${zoom})`,
              transformOrigin: 'center center',
            }}
          >
            <img
              src={imgSrc}
              alt={`Side-scan sonar waterfall scan for ${target_id}`}
              className="max-h-[60vh] w-auto object-contain block select-none"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = `/api/detections/${detection.detection_id}/crop`;
              }}
            />

            {/* Nadir Water Column Line Overlay */}
            <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-0 border-r border-cyan-500/20 pointer-events-none">
              <span className="absolute top-2 left-1 text-[8px] text-cyan-400/50 uppercase tracking-widest font-mono">
                NADIR
              </span>
            </div>

            {/* Bounding Box Overlay */}
            {showBBox && bbox && (
              <div
                className="absolute border-2 transition-all"
                style={{
                  left: `${(Math.max(0, bbox.x1) / 640) * 100}%`,
                  top: `${(Math.max(0, bbox.y1) / 640) * 100}%`,
                  width: `${(Math.max(10, bbox.x2 - bbox.x1) / 640) * 100}%`,
                  height: `${(Math.max(10, bbox.y2 - bbox.y1) / 640) * 100}%`,
                  borderColor: '#38bdf8',
                  backgroundColor: 'rgba(56, 189, 248, 0.15)',
                  boxShadow: '0 0 15px rgba(56, 189, 248, 0.4)',
                }}
              >
                <div
                  className="absolute -top-5 left-0 text-[10px] font-bold px-1.5 py-0.2 rounded shadow flex items-center gap-1 whitespace-nowrap"
                  style={{ backgroundColor: '#0284c7', color: '#ffffff' }}
                >
                  <span>{object_class.replace('_', ' ')}</span>
                  <span className="font-mono opacity-80">{(confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Metadata */}
        <div className="px-4 py-3 bg-slate-900/90 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-4 font-mono text-[11px]">
            <span>Dual-Channel SSS</span>
            <span>Range: 100m Port / 100m Stbd</span>
            {bbox && (
              <span>
                Coordinates: [{bbox.x1.toFixed(0)}, {bbox.y1.toFixed(0)}, {bbox.x2.toFixed(0)}, {bbox.y2.toFixed(0)}]
              </span>
            )}
          </div>
          <div>
            <span className="text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Preprocessed & Georeferenced
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
