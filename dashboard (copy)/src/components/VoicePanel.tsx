import React from 'react';

export const VoicePanel: React.FC = () => (
  <div className="panel">
    <h3>Voice Input</h3>
    <iframe title="voice" src="/static/voice.html" style={{width:'100%', height:300, border:'1px solid #ccc'}} />
  </div>
);