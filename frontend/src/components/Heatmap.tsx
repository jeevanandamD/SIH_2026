import { CircleMarker, LayerGroup } from 'react-leaflet';
import type { HeatmapPoint } from '../types';

interface HeatmapProps {
  points: HeatmapPoint[];
  visible: boolean;
}

export default function Heatmap({ points, visible }: HeatmapProps) {
  if (!visible || points.length === 0) return null;

  return (
    <LayerGroup>
      {points.map((point, idx) => {
        const radius = 20 + point.intensity * 40;
        const opacity = 0.15 + point.intensity * 0.25;

        return (
          <CircleMarker
            key={idx}
            center={[point.latitude, point.longitude]}
            radius={radius}
            fillColor="#f59e0b"
            fillOpacity={opacity}
            stroke={false}
          />
        );
      })}
    </LayerGroup>
  );
}
