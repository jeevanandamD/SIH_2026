import axios from 'axios';
import type {
  Survey,
  TargetRecord,
  GeoJSONCollection,
  DashboardStats,
  PriorityTarget,
  HeatmapPoint,
  ExpertFeedback,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const surveyApi = {
  list: async (): Promise<Survey[]> => {
    const { data } = await api.get('/surveys');
    return data;
  },

  get: async (id: string): Promise<Survey> => {
    const { data } = await api.get(`/surveys/${id}`);
    return data;
  },

  create: async (formData: FormData): Promise<Survey> => {
    const { data } = await api.post('/surveys', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  process: async (id: string): Promise<{ status: string }> => {
    const { data } = await api.post(`/surveys/${id}/process`);
    return data;
  },

  getDetections: async (id: string): Promise<TargetRecord[]> => {
    const { data } = await api.get(`/surveys/${id}/detections`);
    return data;
  },
};

export const detectionApi = {
  get: async (id: string): Promise<TargetRecord> => {
    const { data } = await api.get(`/detections/${id}`);
    return data;
  },

  verify: async (
    id: string,
    feedback: { expert_label: string; correction?: string; comments?: string }
  ): Promise<ExpertFeedback> => {
    const { data } = await api.post(`/detections/${id}/verify`, feedback);
    return data;
  },
};

export const targetApi = {
  geojson: async (): Promise<GeoJSONCollection> => {
    const { data } = await api.get('/targets/geojson');
    return data;
  },

  priority: async (): Promise<PriorityTarget[]> => {
    const { data } = await api.get('/targets/priority');
    return data;
  },

  heatmap: async (): Promise<HeatmapPoint[]> => {
    const { data } = await api.get('/targets/heatmap');
    return data;
  },
};

export const statsApi = {
  get: async (): Promise<DashboardStats> => {
    const { data } = await api.get('/stats');
    return data;
  },
};
