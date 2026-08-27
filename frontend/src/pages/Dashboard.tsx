import { useState, useEffect, useCallback } from 'react';
import MapView from '../components/MapView';
import TargetPanel from '../components/TargetPanel';
import PriorityQueue from '../components/PriorityQueue';
import VerifyDialog from '../components/VerifyDialog';
import SonarOverlay from '../components/SonarOverlay';
import Heatmap from '../components/Heatmap';
import { targetApi, detectionApi, statsApi } from '../api/client';
import type {
  GeoJSONCollection,
  GeoJSONFeature,
  TargetRecord,
  PriorityTarget,
  HeatmapPoint,
  DashboardStats,
} from '../types';
import { RISK_COLORS } from '../types';

type Tab = 'priority' | 'surveys';

export default function Dashboard() {
  const [geojson, setGeojson] = useState<GeoJSONCollection | null>(null);
  const [priorityTargets, setPriorityTargets] = useState<PriorityTarget[]>([]);
  const [heatmapPoints, setHeatmapPoints] = useState<HeatmapPoint[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<TargetRecord | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [verifyDetectionId, setVerifyDetectionId] = useState<string | null>(null);
  const [sonarDetection, setSonarDetection] = useState<TargetRecord | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showPriority, setShowPriority] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('priority');
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [geo, priority, heat, s] = await Promise.all([
        targetApi.geojson().catch(() => null),
        targetApi.priority().catch(() => []),
        targetApi.heatmap().catch(() => []),
        statsApi.get().catch(() => null),
      ]);
      setGeojson(geo);
      setPriorityTargets(priority);
      setHeatmapPoints(heat);
      setStats(s);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFeatureClick = async (feature: GeoJSONFeature) => {
    const id = feature.properties.detection_id;
    setSelectedId(id);
    try {
      const record = await detectionApi.get(id);
      setSelectedTarget(record);
    } catch {
      console.error('Failed to load target', id);
    }
  };

  const handlePrioritySelect = async (detectionId: string) => {
    setSelectedId(detectionId);
    try {
      const record = await detectionApi.get(detectionId);
      setSelectedTarget(record);
    } catch {
      console.error('Failed to load target', detectionId);
    }
  };

  const handleVerify = async (
    detectionId: string,
    data: { expert_label: string; correction?: string; comments?: string }
  ) => {
    try {
      await detectionApi.verify(detectionId, data);
      // Refresh data after verification
      await loadData();
    } catch {
      console.error('Failed to submit verification');
    }
  };

  const handleViewSonar = (record: TargetRecord) => {
    setSonarDetection(record);
  };

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: '#0a1628' }}>
      {/* Top Bar */}
      <header
        className="h-14 flex items-center justify-between px-5 border-b flex-shrink-0"
        style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
            style={{ backgroundColor: '#1b3a5e', color: '#60a5fa' }}
          >
            SA
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide">SONARIS AI</h1>
            <p className="text-[10px] text-gray-500">Underwater Intelligence Platform</p>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="flex items-center gap-6 text-xs">
            <div className="text-center">
              <div className="text-gray-500">Surveys</div>
              <div className="text-white font-bold text-sm">{stats.total_surveys}</div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">Detections</div>
              <div className="text-white font-bold text-sm">{stats.total_detections}</div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">High Risk</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.HIGH }}>
                {stats.high_risk_count}
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">Medium</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.MEDIUM }}>
                {stats.medium_risk_count}
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">Low</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.LOW }}>
                {stats.low_risk_count}
              </div>
            </div>
          </div>
        )}

        {/* Map Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              showHeatmap
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-500'
            }`}
          >
            Heatmap
          </button>
          <button
            onClick={() => setShowPriority(!showPriority)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              showPriority
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-500'
            }`}
          >
            Priority Queue
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          <MapView
            geojson={geojson}
            onFeatureClick={handleFeatureClick}
            selectedId={selectedId}
          />

          {/* Heatmap layer */}
          <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 400 }}>
            <Heatmap points={heatmapPoints} visible={showHeatmap} />
          </div>

          {/* Loading overlay */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 z-50">
              <div className="text-center">
                <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <div className="text-sm text-gray-400">Loading detections...</div>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar — Priority Queue */}
        {showPriority && (
          <div
            className="w-72 flex-shrink-0 border-l flex flex-col"
            style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
          >
            <div className="p-3 border-b" style={{ borderColor: '#1b3a5e' }}>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Inspection Priority
              </h2>
              <p className="text-[10px] text-gray-600 mt-0.5">
                {priorityTargets.length} targets ranked by risk
              </p>
            </div>
            <PriorityQueue
              targets={priorityTargets}
              onSelect={handlePrioritySelect}
              selectedId={selectedId}
            />
          </div>
        )}

        {/* Left Sidebar — Target Detail */}
        {selectedTarget && (
          <div
            className="w-80 flex-shrink-0 border-l overflow-y-auto"
            style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
          >
            <TargetPanel
              target={selectedTarget}
              onClose={() => {
                setSelectedTarget(null);
                setSelectedId(null);
              }}
              onVerify={(id) => setVerifyDetectionId(id)}
            />
          </div>
        )}
      </div>

      {/* Modals */}
      <VerifyDialog
        detectionId={verifyDetectionId}
        onClose={() => setVerifyDetectionId(null)}
        onSubmit={handleVerify}
      />

      <SonarOverlay
        detection={sonarDetection?.detection || null}
        onClose={() => setSonarDetection(null)}
      />
    </div>
  );
}
