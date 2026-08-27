import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import Heatmap from './Heatmap';
import type { GeoJSONCollection, GeoJSONFeature, HeatmapPoint } from '../types';
import { RISK_COLORS } from '../types';

interface MapViewProps {
  geojson: GeoJSONCollection | null;
  onFeatureClick: (feature: GeoJSONFeature) => void;
  selectedId: string | null;
  heatmapPoints?: HeatmapPoint[];
  showHeatmap?: boolean;
}

function createRiskIcon(riskLevel: string): L.DivIcon {
  const color = RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || '#6b7280';
  const size = riskLevel === 'HIGH' ? 18 : 14;
  const pulseClass = riskLevel === 'HIGH' ? 'pulse-ring' : '';

  return L.divIcon({
    className: '',
    html: `
      <div style="position: relative; display: flex; align-items: center; justify-content: center;">
        <div class="${pulseClass}" style="
          position: absolute;
          width: ${size + 12}px;
          height: ${size + 12}px;
          border-radius: 50%;
          border: 2px solid ${color};
          opacity: 0.4;
        "></div>
        <div style="
          width: ${size}px;
          height: ${size}px;
          background: ${color};
          border: 2px solid rgba(255,255,255,0.9);
          border-radius: 50%;
          box-shadow: 0 0 12px ${color}aa;
        "></div>
      </div>
    `,
    iconSize: [size + 12, size + 12],
    iconAnchor: [(size + 12) / 2, (size + 12) / 2],
  });
}

function createSelectedIcon(riskLevel: string): L.DivIcon {
  const color = RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || '#6b7280';

  return L.divIcon({
    className: '',
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 20px ${color}, 0 0 40px ${color}88;
        transform: scale(1.25);
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function MapBoundsController({
  geojson,
  selectedId,
}: {
  geojson: GeoJSONCollection | null;
  selectedId: string | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedId && geojson) {
      const feature = geojson.features.find(
        (f) => f.properties.detection_id === selectedId
      );
      if (feature) {
        const [lng, lat] = feature.geometry.coordinates;
        map.flyTo([lat, lng], Math.max(map.getZoom(), 15), { duration: 1.2 });
      }
    } else if (geojson && geojson.features.length > 0) {
      const validCoords = geojson.features
        .map((f) => f.geometry.coordinates)
        .filter(([lng, lat]) => lat !== 0 && lng !== 0);

      if (validCoords.length > 0) {
        const bounds = L.latLngBounds(
          validCoords.map(([lng, lat]) => [lat, lng] as [number, number])
        );
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 14 });
      }
    }
  }, [selectedId, geojson, map]);

  return null;
}

export default function MapView({
  geojson,
  onFeatureClick,
  selectedId,
  heatmapPoints = [],
  showHeatmap = false,
}: MapViewProps) {
  const defaultCenter: [number, number] = [15.4208, 73.7845]; // Arabian Sea default

  const featuresWithCoords =
    geojson?.features.filter(
      (f) => f.geometry.coordinates[0] !== 0 && f.geometry.coordinates[1] !== 0
    ) || [];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={6}
      className="h-full w-full"
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <MapBoundsController selectedId={selectedId} geojson={geojson} />
      
      {/* Heatmap Layer inside MapContainer */}
      <Heatmap points={heatmapPoints} visible={showHeatmap} />

      {featuresWithCoords.map((feature) => {
        const { detection_id, risk_level, target_id, object_class, confidence, depth, risk_score } =
          feature.properties;
        const [lng, lat] = feature.geometry.coordinates;
        const isSelected = detection_id === selectedId;

        return (
          <Marker
            key={detection_id}
            position={[lat, lng]}
            icon={isSelected ? createSelectedIcon(risk_level) : createRiskIcon(risk_level)}
            eventHandlers={{
              click: () => onFeatureClick(feature),
            }}
          >
            <Popup className="dark-popup">
              <div className="text-xs p-1">
                <div className="font-bold text-sm text-white">{target_id}</div>
                <div className="text-blue-400 capitalize font-medium">{object_class.replace('_', ' ')}</div>
                <div className="mt-2 space-y-1 text-gray-300">
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-400">Risk Level:</span>
                    <span
                      className="font-bold uppercase"
                      style={{ color: RISK_COLORS[risk_level] }}
                    >
                      {risk_level} ({(risk_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-400">Confidence:</span>
                    <span className="font-mono">{(confidence * 100).toFixed(1)}%</span>
                  </div>
                  {depth != null && (
                    <div className="flex justify-between gap-3">
                      <span className="text-gray-400">Bathymetry:</span>
                      <span className="font-mono">{depth.toFixed(1)} m depth</span>
                    </div>
                  )}
                </div>
                <div className="text-gray-500 font-mono text-[10px] mt-2 pt-1 border-t border-gray-700">
                  {lat.toFixed(5)}°N, {lng.toFixed(5)}°E
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
