import React, { useState } from 'react';
import { ragQuery, RAGQueryResultItem } from '../lib/ragApi';

export const RAGQueryPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<RAGQueryResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState<any>({});
  const [error, setError] = useState<string|undefined>();
  const [sortKey, setSortKey] = useState<string>('fused_score');
  const [sortDir, setSortDir] = useState<'asc'|'desc'>('desc');

  const run = async (): Promise<void> => {
    if (!query.trim()) return;
    setLoading(true); setError(undefined);
    try {
      const resp = await ragQuery(query.trim());
      setResults(resp.items || []);
      setMeta({ fusion_weights: resp.fusion_weights, took_ms: resp.took_ms });
      // Append to local history
      try {
        const raw = localStorage.getItem('rag_history');
        const arr: any[] = raw ? JSON.parse(raw) : [];
        arr.push({ q: query.trim(), ts: Date.now(), ms: resp.took_ms || 0 });
        localStorage.setItem('rag_history', JSON.stringify(arr.slice(-200)));
      } catch { /* ignore storage errors */ }
    } catch (e: any) { setError(e?.message); }
    finally { setLoading(false); }
  };

  const sorted = [...results].sort((a,b)=>{
    const av = (a as any)[sortKey] ?? 0;
    const bv = (b as any)[sortKey] ?? 0;
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  const changeSort = (key: string) => {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc':'asc'); else { setSortKey(key); setSortDir('desc'); }
  };

  return (
    <div className="panel">
      <h3>RAG Query Tester</h3>
      <div className="row">
  <input style={{flex:1}} placeholder="Enter query" value={query} onChange={(e:React.ChangeEvent<HTMLInputElement>)=>setQuery(e.target.value)} onKeyDown={(e:React.KeyboardEvent<HTMLInputElement>)=> e.key==='Enter' && run()} />
        <button onClick={run} disabled={loading}>{loading ? 'Running…' : 'Go'}</button>
      </div>
      {error && <div className="error">Error: {error}</div>}
      {meta && <div className="meta">Fusion Weights: {meta.fusion_weights ? `ltr=${meta.fusion_weights.ltr} concept=${meta.fusion_weights.conceptual}` : '-'} | Took: {meta.took_ms} ms</div>}
      <table className="results-table">
        <thead>
          <tr>
            <th onClick={()=>changeSort('fused_score')}>Fused</th>
            <th onClick={()=>changeSort('conceptual_score')}>Concept</th>
            <th onClick={()=>changeSort('ltr_score')}>LTR</th>
            <th onClick={()=>changeSort('distance')}>Dist</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r,i)=>(
            <tr key={i}>
              <td>{r.fused_score?.toFixed(4)}</td>
              <td>{r.conceptual_score?.toFixed(4)}</td>
              <td>{r.ltr_score?.toFixed(4)}</td>
              <td>{r.distance?.toFixed?.(4)}</td>
              <td><pre>{r.text_preview || r.content}</pre></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
