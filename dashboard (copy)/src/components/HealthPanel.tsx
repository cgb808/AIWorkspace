import React, { useEffect, useState } from 'react';
import { fetchHealth, HealthStatus } from '../lib/ragApi';

export const HealthPanel: React.FC = () => {
  const [data, setData] = useState<HealthStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|undefined>();

  const load = async () => {
    setLoading(true); setError(undefined);
    try { setData(await fetchHealth()); } catch (e: any) { setError(e?.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, []);

  return (
    <div className="panel">
      <h3>Health</h3>
      {loading && <div>Loading…</div>}
      {error && <div className="error">Error: {error}</div>}
      <table>
        <thead><tr><th>Service</th><th>Status</th><th>Detail</th></tr></thead>
        <tbody>
          {data.map(h => (
            <tr key={h.service} className={h.ok ? 'ok' : 'fail'}>
              <td>{h.service}</td>
              <td>{h.ok ? 'OK' : 'FAIL'}</td>
              <td><pre style={{whiteSpace:'pre-wrap'}}>{typeof h.detail === 'string' ? h.detail : JSON.stringify(h.detail, null, 2)}</pre></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
