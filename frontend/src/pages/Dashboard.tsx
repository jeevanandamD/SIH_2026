import { useState, useEffect, useCallback } from 'react';
import MapView from '../components/MapView';
import TargetPanel from '../components/TargetPanel';
import PriorityQueue from '../components/PriorityQueue';
import VerifyDialog from '../components/VerifyDialog';
import SonarOverlay from '../components/SonarOverlay';
import { targetApi, detectionApi, statsApi, surveyApi } from '../api/client';
import type {
  GeoJSONCollection,
  GeoJSONFeature,
  TargetRecord,
  PriorityTarget,
  HeatmapPoint,
  DashboardStats,
} from '../types';
import { RISK_COLORS } from '../types';

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
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [loading, setLoading] = useState(true);
  const [isGeneratingDemo, setIsGeneratingDemo] = useState(false);

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
      await loadData();
    } catch {
      console.error('Failed to submit verification');
    }
  };

  const handleViewSonar = (record: TargetRecord) => {
    setSonarDetection(record);
  };

  const handleGenerateDemo = async () => {
    try {
      setIsGeneratingDemo(true);
      await surveyApi.generateDemo();
      await loadData();
    } catch (e) {
      console.error('Failed to generate demo surveys', e);
    } finally {
      setIsGeneratingDemo(false);
    }
  };

  const handleExportMissionPlan = async () => {
    try {
      const plan = await targetApi.exportMissionPlan();
      const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AUV_Mission_Plan_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export plan failed', e);
    }
  };

  // Filter features and priority list
  const filteredGeojson: GeoJSONCollection | null = geojson
    ? {
        ...geojson,
        features: geojson.features.filter((f) =>
          riskFilter === 'ALL' ? true : f.properties.risk_level === riskFilter
        ),
      }
    : null;

  const filteredPriorityTargets = priorityTargets.filter((t) =>
    riskFilter === 'ALL' ? true : t.risk_level === riskFilter
  );

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#0a1628' }}>
      {/* Top Bar */}
      <header
        className="h-14 flex items-center justify-between px-5 border-b flex-shrink-0"
        style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-md"
            style={{ backgroundColor: '#1b3a5e', color: '#60a5fa' }}
          >
            SA
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <span>SONARIS AI</span>
              <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </h1>
            <p className="text-[10px] text-gray-400">Side-Scan Sonar Marine Debris & Risk Prioritization Engine</p>
          </div>
        </div>

        {/* Stats Summary Bar */}
        {stats && (
          <div className="hidden md:flex items-center gap-6 text-xs bg-slate-900/60 px-4 py-1.5 rounded-lg border border-slate-800">
            <div className="text-center">
              <div className="text-gray-400 text-[10px]">Surveys</div>
              <div className="text-white font-bold text-sm">{stats.total_surveys}</div>
            </div>
            <div className="h-6 w-px bg-slate-800" />
            <div className="text-center">
              <div className="text-gray-400 text-[10px]">Targets</div>
              <div className="text-white font-bold text-sm">{stats.total_detections}</div>
            </div>
            <div className="h-6 w-px bg-slate-800" />
            <div
              className="text-center cursor-pointer hover:opacity-80"
              onClick={() => setRiskFilter(riskFilter === 'HIGH' ? 'ALL' : 'HIGH')}
            >
              <div className="text-gray-400 text-[10px]">High Risk</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.HIGH }}>
                {stats.high_risk_count}
              </div>
            </div>
            <div className="h-6 w-px bg-slate-800" />
            <div
              className="text-center cursor-pointer hover:opacity-80"
              onClick={() => setRiskFilter(riskFilter === 'MEDIUM' ? 'ALL' : 'MEDIUM')}
            >
              <div className="text-gray-400 text-[10px]">Medium</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.MEDIUM }}>
                {stats.medium_risk_count}
              </div>
            </div>
            <div className="h-6 w-px bg-slate-800" />
            <div
              className="text-center cursor-pointer hover:opacity-80"
              onClick={() => setRiskFilter(riskFilter === 'LOW' ? 'ALL' : 'LOW')}
            >
              <div className="text-gray-400 text-[10px]">Low</div>
              <div className="font-bold text-sm" style={{ color: RISK_COLORS.LOW }}>
                {stats.low_risk_count}
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Actions */}
        <div className="flex items-center gap-2">
          {/* Risk Filter Select */}
          <div className="flex items-center bg-gray-900/80 rounded-lg p-0.5 border border-gray-700 text-xs">
            {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setRiskFilter(lvl)}
                className={`px-2 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                  riskFilter === lvl
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer border ${
              showHeatmap
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 shadow-sm'
                : 'bg-gray-800/80 text-gray-400 border-gray-700 hover:border-gray-500'
            }`}
          >
            Anomaly Heatmap
          </button>

          <button
            onClick={() => setShowPriority(!showPriority)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer border ${
              showPriority
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/40 shadow-sm'
                : 'bg-gray-800/80 text-gray-400 border-gray-700 hover:border-gray-500'
            }`}
          >
            Priority Queue
          </button>

          {/* Export Dropdown / Buttons */}
          <a
            href="/api/export/csv"
            download
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800/80 text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-colors cursor-pointer"
          >
            Export CSV
          </a>

          <button
            onClick={handleExportMissionPlan}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-700/50 hover:bg-emerald-900/80 transition-colors cursor-pointer"
          >
            AUV Mission Plan
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          <MapView
            geojson={filteredGeojson}
            onFeatureClick={handleFeatureClick}
            selectedId={selectedId}
            heatmapPoints={heatmapPoints}
            showHeatmap={showHeatmap}
          />

          {/* Quick empty state prompt if no surveys */}
          {(!geojson || geojson.features.length === 0) && !loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 z-30">
              <div className="bg-slate-900/90 border border-blue-500/30 p-6 rounded-2xl max-w-md text-center shadow-2xl backdrop-blur-md">
                <div className="w-12 h-12 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-4 text-xl">
                  ⚓
                </div>
                <h3 className="text-base font-bold text-white mb-2">No Active Sonar Surveys Loaded</h3>
                <p className="text-xs text-gray-400 mb-5">
                  Generate realistic side-scan sonar demo surveys (Arabian Sea, Palk Strait, Kochi Harbor) with full AI evidence fusion and risk prioritization.
                </p>
                <button
                  onClick={handleGenerateDemo}
                  disabled={isGeneratingDemo}
                  className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-all shadow-lg cursor-pointer disabled:opacity-50"
                >
                  {isGeneratingDemo ? 'Simulating Acoustic Surveys...' : 'Generate Demo SSS Surveys'}
                </button>
              </div>
            </div>
          )}

          {/* Loading overlay */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 z-50">
              <div className="text-center bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md">
                <div className="w-9 h-9 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <div className="text-xs text-gray-300 font-medium">Computing Multi-Source Evidence Fusion...</div>
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
            <div className="p-3 border-b flex items-center justify-between" style={{ borderColor: '#1b3a5e' }}>
              <div>
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Inspection Priority
                </h2>
                <p className="text-[10px] text-gray-500 mt-0.5">
                  {filteredPriorityTargets.length} targets ranked by composite risk
                </p>
              </div>
              <button
                onClick={loadData}
                className="text-gray-400 hover:text-white text-xs p-1 cursor-pointer"
                title="Refresh targets"
              >
                ↻
              </button>
            </div>
            <PriorityQueue
              targets={filteredPriorityTargets}
              onSelect={handlePrioritySelect}
              selectedId={selectedId}
            />
          </div>
        )}

        {/* Left Sidebar — Target Detail */}
        {selectedTarget && (
          <div
            className="w-84 flex-shrink-0 border-l overflow-y-auto"
            style={{ backgroundColor: '#0f2035', borderColor: '#1b3a5e' }}
          >
            <TargetPanel
              target={selectedTarget}
              onClose={() => {
                setSelectedTarget(null);
                setSelectedId(null);
              }}
              onVerify={(id) => setVerifyDetectionId(id)}
              onViewSonar={handleViewSonar}
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
