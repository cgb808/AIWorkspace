import React from 'react';
import { HealthPanel } from './components/HealthPanel';
import { RAGQueryPanel } from './components/RAGQueryPanel';
import { ModelPanel } from './components/ModelPanel';
import { VoicePanel } from './components/VoicePanel';
import { QueryHistoryPanel } from './components/QueryHistoryPanel';
import { MetricsPanel } from './components/MetricsPanel';

export const App: React.FC = () => {
  return (
    <div className="app">
      <header>
        <h1>ZenGlow RAG Dashboard</h1>
      </header>
      <main>
        <div className="grid">
          <HealthPanel />
          <ModelPanel />
          <RAGQueryPanel />
          <VoicePanel />
          <MetricsPanel />
          <QueryHistoryPanel onSelect={(q: string)=>{ /* placeholder: could lift state */ }} />
        </div>
      </main>
      <footer>
        <small>Build: experimental | &copy; ZenGlow</small>
      </footer>
    </div>
  );
};
