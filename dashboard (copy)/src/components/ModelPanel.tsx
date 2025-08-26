import React, { useEffect, useState } from 'react';
import { fetchModels, ModelRegistryEntry } from '../lib/ragApi';

export const ModelPanel: React.FC = () => {
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|undefined>();

  const load = async () => {
    setLoading(true); setError(undefined);
    try { setModels(await fetchModels()); } catch (e:any){ setError(e?.message); }
    finally { setLoading(false); }
  };
  useEffect(()=>{ load(); const id = setInterval(load, 20000); return ()=>clearInterval(id); }, []);

  return (
    <div className="panel">
      <h3>Models</h3>
      {loading && <div>Loading…</div>}
      {error && <div className="error">Error: {error}</div>}
      <table>
        <thead><tr><th>Name</th><th>Family</th><th>Quant</th><th>Role</th><th>Ctx</th><th>Loaded</th><th>TPS</th></tr></thead>
        <tbody>
          {models.map(m => (
            <tr key={m.name} className={m.loaded ? 'ok':'warn'}>
              <td>{m.name}</td>
              <td>{m.family}</td>
              <td>{m.quant||'-'}</td>
              <td>{m.role||'-'}</td>
              <td>{m.context_len||'-'}</td>
              <td>{m.loaded? 'yes':'no'}</td>
              <td>{m.throughput_tps? m.throughput_tps.toFixed(1): '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};