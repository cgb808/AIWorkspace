import React, { useEffect, useState } from 'react';
import { fetchMetricsSummary } from '../lib/ragApi';

interface QueryStats { total:number; cache_hits: Record<string,number>; last_latency_ms?: number; p50_ms?:number; p95_ms?:number; p99_ms?:number; }

export const MetricsPanel: React.FC = () => {
  const [stats, setStats] = useState<QueryStats|undefined>();
  const [error, setError] = useState<string|undefined>();
  useEffect(()=>{
    let active = true;
    const load = async () => {
      try { const data = await fetchMetricsSummary(); if (active) setStats(data.query_stats); }
      catch (e:any){ if(active) setError(e?.message); }
    };
    load();
    const id = setInterval(load, 10000);
    return ()=>{ active = false; clearInterval(id); };
  },[]);
  return (
    <div className="panel">
      <h3>Metrics</h3>
      {error && <div className="error">{error}</div>}
      {!stats && !error && <div>Loading…</div>}
      {stats && (
        <div className="metrics-grid">
          <div>Total Queries: {stats.total}</div>
          <div>Cache Hits: full={stats.cache_hits?.full||0} feature={stats.cache_hits?.feature||0} none={stats.cache_hits?.none||0}</div>
          <div>Last Latency: {stats.last_latency_ms?.toFixed(1)} ms</div>
          <div>P50: {stats.p50_ms?.toFixed(1)} ms | P95: {stats.p95_ms?.toFixed(1)} ms | P99: {stats.p99_ms?.toFixed(1)} ms</div>
        </div>
      )}
    </div>
  );
};