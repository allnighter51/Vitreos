import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

interface TransmissionLog {
  id: number;
  timestamp: string;
  status: 'SUCCESS' | 'FAILED';
  payload: string;
}

export function RemoteTab() {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookStatus, setWebhookStatus] = useState<'CONNECTED' | 'DISCONNECTED'>('DISCONNECTED');
  const [transmissions, setTransmissions] = useState<TransmissionLog[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [rpcEnabled, setRpcEnabled] = useState(false);
  const [rpcPulse, setRpcPulse] = useState(false);

  // RPC pulse animation
  useEffect(() => {
    if (!rpcEnabled) return;
    const interval = setInterval(() => setRpcPulse(p => !p), 800);
    return () => clearInterval(interval);
  }, [rpcEnabled]);

  const toggleRpc = () => {
    const newState = !rpcEnabled;
    setRpcEnabled(newState);
    
    // Send toggle command to backend
    const ws = new WebSocket('ws://localhost:8000/sentinel');
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'TOGGLE_RPC',
        enabled: newState
      }));
      ws.close();
    };
  };

  const sendTestSignal = () => {
    setIsSending(true);
    
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
    
    const payload = {
      content: "🔴 VITREOS SENTINEL ALERT",
      embeds: [{
        title: "System Telemetry Report",
        color: 0xA855F7,
        fields: [
          { name: "CPU Load", value: `${(Math.random() * 40 + 30).toFixed(1)}%`, inline: true },
          { name: "GPU Temp", value: `${(Math.random() * 15 + 65).toFixed(0)}°C`, inline: true },
          { name: "Memory", value: `${(Math.random() * 5 + 20).toFixed(1)}GB`, inline: true }
        ],
        timestamp: new Date().toISOString()
      }]
    };

    setTimeout(() => {
      const newLog: TransmissionLog = {
        id: Date.now(),
        timestamp: timeStr,
        status: webhookUrl.includes('discord.com') ? 'SUCCESS' : 'FAILED',
        payload: JSON.stringify(payload, null, 2)
      };
      
      setTransmissions(prev => [newLog, ...prev.slice(0, 9)]);
      setWebhookStatus(webhookUrl.includes('discord.com') ? 'CONNECTED' : 'DISCONNECTED');
      setIsSending(false);
    }, 1200);
  };

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* 1. Webhook & RPC Configuration */}
      <div className="grid grid-cols-12 gap-2 h-32">
        <WinFrame title="WEBHOOK_ENDPOINT" accentColor="#A855F7" className="col-span-6">
          <div className="p-3 flex flex-col justify-center h-full gap-3">
            <div className="flex items-center gap-2 border border-[#2A2A2A] px-2 py-1 bg-[#050505]">
              <span style={{ color: '#A855F7', fontSize: '9px', fontFamily: MONO }}>URL:</span>
              <input 
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://discord.com/api/webhooks/..."
                className="bg-transparent border-none outline-none text-[9px] text-[#888] flex-1"
                style={{ fontFamily: MONO }}
              />
            </div>
            
            <button
              onClick={sendTestSignal}
              disabled={isSending || !webhookUrl}
              style={{
                background: isSending ? '#1A1A1A' : 'repeating-linear-gradient(45deg, #000, #000 3px, rgba(255,107,0,0.1) 3px, rgba(255,107,0,0.1) 6px)',
                border: `2px solid ${isSending ? '#333' : '#FF6B00'}`,
                color: isSending ? '#333' : '#FF6B00',
                fontFamily: MONO,
                fontSize: '10px',
                padding: '8px 16px',
                letterSpacing: '0.15em',
                textShadow: isSending ? 'none' : '0 0 10px #FF6B00',
                boxShadow: isSending ? 'none' : '0 0 12px #FF6B0044',
                cursor: isSending || !webhookUrl ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {isSending ? 'TRANSMITTING...' : 'SEND TEST SIGNAL'}
            </button>
          </div>
        </WinFrame>

        <WinFrame title="DISCORD_NEURAL_LINK" accentColor="#5865F2" badge="RPC" className="col-span-3">
          <div className="p-3 flex flex-col items-center justify-center h-full gap-2">
            {/* ASCII Discord Logo */}
            <div style={{ fontFamily: MONO, fontSize: '16px', color: rpcEnabled ? '#5865F2' : '#333', lineHeight: 1, textShadow: rpcEnabled && rpcPulse ? '0 0 12px #5865F2' : 'none', transition: 'all 0.3s ease' }}>
              <div>╔═══╗</div>
              <div>║ ◉ ║</div>
              <div>╚═══╝</div>
            </div>
            
            <button
              onClick={toggleRpc}
              style={{
                background: rpcEnabled ? '#5865F222' : '#1A1A1A',
                border: `1px solid ${rpcEnabled ? '#5865F2' : '#2A2A2A'}`,
                color: rpcEnabled ? '#5865F2' : '#444',
                fontFamily: MONO,
                fontSize: '8px',
                padding: '4px 12px',
                letterSpacing: '0.1em',
                textShadow: rpcEnabled ? '0 0 8px #5865F2' : 'none',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {rpcEnabled ? 'NEURAL_LINK_ACTIVE' : 'ACTIVATE_LINK'}
            </button>
            
            <span style={{ fontFamily: MONO, fontSize: '6px', color: '#333', letterSpacing: '0.1em' }}>
              {rpcEnabled ? 'BROADCASTING' : 'STANDBY'}
            </span>
          </div>
        </WinFrame>

        <WinFrame title="WEBHOOK_STATUS" accentColor="#22C55E" className="col-span-3">
          <div className="p-3 flex flex-col items-center justify-center h-full gap-2">
            <div style={{
              width: 48,
              height: 48,
              background: webhookStatus === 'CONNECTED' ? '#22C55E22' : '#FF444422',
              border: `2px solid ${webhookStatus === 'CONNECTED' ? '#22C55E' : '#FF4444'}`,
              boxShadow: webhookStatus === 'CONNECTED' ? '0 0 16px #22C55E44' : '0 0 16px #FF444444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: 24,
                height: 24,
                background: webhookStatus === 'CONNECTED' ? '#22C55E' : '#FF4444',
                boxShadow: `0 0 12px ${webhookStatus === 'CONNECTED' ? '#22C55E' : '#FF4444'}`
              }} />
            </div>
            <span style={{
              fontFamily: MONO,
              fontSize: '10px',
              color: webhookStatus === 'CONNECTED' ? '#22C55E' : '#FF4444',
              letterSpacing: '0.1em',
              textShadow: `0 0 8px ${webhookStatus === 'CONNECTED' ? '#22C55E' : '#FF4444'}`
            }}>
              {webhookStatus}
            </span>
          </div>
        </WinFrame>
      </div>

      {/* 2. Transmission Log */}
      <WinFrame title="TRANSMISSION_LOG // PAYLOAD_ARCHIVE" accentColor="#06B6D4" className="flex-1">
        <div className="overflow-y-auto h-full p-2 no-scrollbar">
          {transmissions.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <span style={{ fontFamily: MONO, fontSize: '9px', color: '#333', letterSpacing: '0.1em' }}>
                NO_TRANSMISSIONS_RECORDED
              </span>
            </div>
          ) : (
            <div className="space-y-3">
              {transmissions.map(t => (
                <div key={t.id} className="border border-[#1A1A1A] bg-[#0A0A0A] p-2">
                  <div className="flex justify-between mb-2 pb-1 border-b border-[#1A1A1A]">
                    <span style={{ fontFamily: MONO, fontSize: '8px', color: '#444' }}>
                      {t.timestamp}
                    </span>
                    <span style={{
                      fontFamily: MONO,
                      fontSize: '8px',
                      color: t.status === 'SUCCESS' ? '#22C55E' : '#FF4444',
                      textShadow: t.status === 'SUCCESS' ? '0 0 6px #22C55E' : '0 0 6px #FF4444'
                    }}>
                      [{t.status}]
                    </span>
                  </div>
                  <pre style={{
                    fontFamily: MONO,
                    fontSize: '7px',
                    color: '#666',
                    lineHeight: '1.4',
                    overflow: 'auto',
                    maxHeight: '120px'
                  }}>
                    {t.payload}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </WinFrame>
    </div>
  );
}
