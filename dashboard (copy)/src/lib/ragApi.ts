import axios from 'axios';
import { RAG_API_BASE } from '../env';

export interface RAGQueryResultItem {
  chunk_id?: number;
  text_preview?: string;
  distance?: number;
  ltr_score?: number;
  conceptual_score?: number;
  fused_score?: number;
  features?: Record<string, number>;
  // legacy compatibility
  id?: string;
  content?: string;
}

export interface RAGQueryResponse {
  query: string;
  items: RAGQueryResultItem[];
  fusion_weights?: { ltr: number; conceptual: number };
  feature_names?: string[];
  took_ms?: number;
}

export async function ragQuery(query: string): Promise<RAGQueryResponse> {
  const started = performance.now();
  const { data } = await axios.post(`${RAG_API_BASE}/rag/query2`, { query });
  const took_ms = Math.round(performance.now() - started);
  const items = data.items || data.results || [];
  return { took_ms, items, ...data };
}

export interface HealthStatus {
  service: string;
  ok: boolean;
  detail?: any;
}

export async function fetchHealth(): Promise<HealthStatus[]> {
  const endpoints = [
    { service: 'api', path: '/health' },
    { service: 'ollama', path: '/health/ollama' },
    { service: 'models', path: '/health/models' }
  ];
  const results: HealthStatus[] = [];
  await Promise.all(endpoints.map(async e => {
    try {
      const { data } = await axios.get(`${RAG_API_BASE}${e.path}`);
      results.push({ service: e.service, ok: true, detail: data });
    } catch (err: any) {
      results.push({ service: e.service, ok: false, detail: err?.message });
    }
  }));
  return results;
}

export interface ModelRegistryEntry {
  name: string; family: string; quant?: string; context_len?: number; role?: string; loaded?: boolean; throughput_tps?: number;
}

export async function fetchModels(): Promise<ModelRegistryEntry[]> {
  const { data } = await axios.get(`${RAG_API_BASE}/health/models`);
  return data.models || [];
}

export async function fetchMetricsSummary(): Promise<any> {
  const { data } = await axios.get(`${RAG_API_BASE}/metrics/json`);
  return data;
}
