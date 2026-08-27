export interface Survey {
  survey_id: string;
  name: string;
  vessel_id: string | null;
  start_time: string | null;
  end_time: string | null;
  area_name: string | null;
  sonar_type: string | null;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  image_count?: number;
  detection_count?: number;
}

export interface SonarImage {
  image_id: string;
  survey_id: string;
  image_path: string;
  timestamp: string | null;
  latitude: number | null;
  longitude: number | null;
  depth: number | null;
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  detection_id: string;
  image_id: string;
  target_id: string;
  object_class: string;
  confidence: number;
  bbox: BoundingBox;
  segmentation_mask_path: string | null;
  image_path?: string;
  latitude: number | null;
  longitude: number | null;
  depth: number | null;
}

export interface Anomaly {
  anomaly_id: string;
  detection_id: string;
  anomaly_score: number;
  uncertainty: number;
}

export interface AcousticFeatures {
  detection_id: string;
  target_intensity: number;
  target_area: number;
  shadow_area: number;
  shadow_length: number;
  target_shadow_ratio: number;
  seabed_texture: number;
  seabed_contrast: number;
}

export interface RiskAssessment {
  detection_id: string;
  evidence_score: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  priority: number;
}

export interface ExpertFeedback {
  feedback_id: string;
  detection_id: string;
  expert_label: string;
  correction: string | null;
  comments: string | null;
  verified: boolean;
}

export interface TargetRecord {
  detection: Detection;
  anomaly: Anomaly | null;
  acoustic_features: AcousticFeatures | null;
  risk_assessment: RiskAssessment | null;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    detection_id: string;
    target_id: string;
    object_class: string;
    confidence: number;
    anomaly_score: number;
    evidence_score: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
    risk_score: number;
    depth: number | null;
    priority: number;
  };
}

export interface GeoJSONCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface DashboardStats {
  total_surveys: number;
  total_detections: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  processed_surveys: number;
}

export interface PriorityTarget {
  target_id: string;
  detection_id: string;
  object_class: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_score: number;
  evidence_score: number;
  confidence: number;
  latitude: number | null;
  longitude: number | null;
  priority: number;
}

export interface HeatmapPoint {
  latitude: number;
  longitude: number;
  intensity: number;
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export const RISK_COLORS: Record<RiskLevel, string> = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#22c55e',
};

export const RISK_LABELS: Record<RiskLevel, string> = {
  HIGH: 'High Risk',
  MEDIUM: 'Medium Risk',
  LOW: 'Low Risk',
};
