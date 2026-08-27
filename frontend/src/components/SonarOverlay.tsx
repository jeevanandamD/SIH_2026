import type { Detection } from '../types';

interface SonarOverlayProps {
  detection: Detection | null;
  onClose: () => void;
}

export default function SonarOverlay({ detection, onClose }: SonarOverlayProps) {
  if (!detection) return null;

  const { bbox, image_path, object_class, confidence, target_id } = detection;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div
        className="relative rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden"
        style={{ backgroundColor: '#0f2035', border: '1px solid #1b3a5e' }}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Sonar Image — {target_id}</h2>
            <p className="text-xs text-gray-400">
              {object_class} | {(confidence * 100).toFixed(1)}% confidence
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none"
          >
            &times;
          </button>
        </div>

        {/* Image Area */}
        <div className="p-4">
          <div
            className="relative rounded-lg overflow-hidden"
            style={{ backgroundColor: '#0a1628' }}
          >
            {image_path ? (
              <img
                src={image_path}
                alt={`Sonar image of ${target_id}`}
                className="w-full h-auto"
              />
            ) : (
              <div className="w-full h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <div className="text-4xl mb-2">Sonar</div>
                  <div className="text-sm">Image not available</div>
                </div>
              </div>
            )}

            {/* Bounding Box Overlay */}
            {image_path && bbox && (
              <div
                className="absolute border-2 border-dashed"
                style={{
                  left: `${(bbox.x1 / 640) * 100}%`,
                  top: `${(bbox.y1 / 640) * 100}%`,
                  width: `${((bbox.x2 - bbox.x1) / 640) * 100}%`,
                  height: `${((bbox.y2 - bbox.y1) / 640) * 100}%`,
                  borderColor: '#60a5fa',
                  backgroundColor: 'rgba(96, 165, 250, 0.1)',
                }}
              >
                <span
                  className="absolute -top-5 left-0 text-[10px] px-1 py-0.5 rounded"
                  style={{ backgroundColor: '#60a5fa', color: '#0a1628' }}
                >
                  {object_class}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* BBox Info */}
        {bbox && (
          <div className="px-4 pb-4">
            <div className="text-xs text-gray-500 font-mono">
              BBox: [{bbox.x1}, {bbox.y1}, {bbox.x2}, {bbox.y2}]
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
