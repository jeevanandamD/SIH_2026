import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { GeoJSONCollection, GeoJSONFeature } from '../types';
import { RISK_COLORS } from '../types';

interface MapViewProps {
  geojson: GeoJSONCollection | null;
  onFeatureClick: (feature: GeoJSONFeature) => void;
  selectedId: string | null;
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
          border: 2px solid rgba(255,255,255,0.8);
          border-radius: 50%;
          box-shadow: 0 0 10px ${color}88;
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
        box-shadow: 0 0 20px ${color}, 0 0 40px ${color}66;
        transform: scale(1.2);
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function MapEvents({
  onFeatureClick,
}: {
  onFeatureClick: (f: GeoJSONFeature) => void;
}) {
  return null;
}

function FlyToMarker({ selectedId, geojson }: { selectedId: string | null; geojson: GeoJSONCollection | null }) {
  const map = useMap();

  useEffect(() => {
    if (!selectedId || !geojson) return;
    const feature = geojson.features.find(
      (f) => f.properties.detection_id === selectedId
    );
    if (feature) {
      const [lng, lat] = feature.geometry.coordinates;
      map.flyTo([lat, lng], Math.max(map.getZoom(), 14), { duration: 1 });
    }
  }, [selectedId, geojson, map]);

  return null;
}

export default function MapView({ geojson, onFeatureClick, selectedId }: MapViewProps) {
  const defaultCenter: [number, number] = [12.9716, 77.5946]; // Bangalore fallback

  const featuresWithCoords = geojson?.features.filter(
    (f) => f.geometry.coordinates[0] !== 0 && f.geometry.coordinates[1] !== 0
  ) || [];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={5}
      className="h-full w-full"
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <FlyToMarker selectedId={selectedId} geojson={geojson} />
      {featuresWithCoords.map((feature) => {
        const { detection_id, risk_level, target_id, object_class, confidence } =
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
              <div className="text-sm">
                <div className="font-bold text-base">{target_id}</div>
                <div className="text-gray-300">{object_class}</div>
                <div className="mt-1">
                  <span className="text-gray-400">Confidence:</span>{' '}
                  <span className="font-mono">{(confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Risk:</span>{' '}
                  <span
                    className="font-bold"
                    style={{ color: RISK_COLORS[risk_level] }}
                  >
                    {risk_level}
                  </span>
                </div>
                <div className="text-gray-500 text-xs mt-1">
                  {lat.toFixed(6)}, {lng.toFixed(6)}
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
