import React, { useEffect, useState } from 'react';

interface Entry { q: string; ts: number; ms: number; }

interface Props { onSelect: (q:string)=>void }
export const QueryHistoryPanel: React.FC<Props> = ({onSelect}) => {
  const [items, setItems] = useState<Entry[]>([]);
  useEffect(()=>{
    const raw = localStorage.getItem('rag_history');
    if (raw) setItems(JSON.parse(raw));
  },[]);
  const clear = () => { localStorage.removeItem('rag_history'); setItems([]); };
  return (
    <div className="panel">
      <h3>History <button onClick={clear} style={{float:'right'}}>Clear</button></h3>
      <ul className="history">
        {items.slice().reverse().map((e:Entry,i:number)=>(
          <li key={i}>
            <button onClick={()=>onSelect(e.q)} title={new Date(e.ts).toLocaleString()}>{e.q}</button>
            <span className="ms">{e.ms} ms</span>
          </li>
        ))}
      </ul>
    </div>
  );
};