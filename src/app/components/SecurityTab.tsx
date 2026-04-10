import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

// Simulation Utilities
const jitter = (val: number, range: number) => val + (Math.random() - 0.5) * range;
const randomIP = () => `${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;

interface BreachEvent {
  id: number;
  time: string;
  source: string;
  type: string;
  status: 'BLOCKED' | 'MONITORING' | 'QUARANTINED';
}

export function SecurityTab() {
  const [shieldLevel, setShieldLevel] = useState(100);
  const [activeThreats, setActiveThreats] = useState(0);
  const [breaches, setBreaches] = useState<BreachEvent[]>([]);
  const [ports, setPorts] = useState(new Array(16).fill(true));
  const [integrity, setIntegrity] = useState(99.98);

  // Security Simulation Engine
  useEffect(() => {
    const t = setInterval(() => {
      // Jitter metrics
      setShieldLevel(s => Math.max(92, Math.min(100, s + (Math.random() - 0.5) * 2)));
      setIntegrity(i => Math.max(99.90, Math.min(100, i + (Math.random() - 0.5) * 0.05)));
      setActiveThreats(Math.floor(Math.random() * 4));
      
      // Random Port Activity
      setPorts(prev => prev.map(() => Math.random() > 0.05));

      // Occasional Breach Event
      if (Math.random() > 0.7) {
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
        const types = ['PORT_SCAN', 'BRUTE_FORCE', 'MALFORMED_PKT', 'UNAUTH_ACCESS'];
        
        const newBreach: BreachEvent = {
          id: Date.now(),
          time: timeStr,
          source: randomIP(),
          type: types[Math.floor(Math.random() * types.length)],
          status: Math.random() > 0.3 ? 'BLOCKED' : 'QUARANTINED'
        };
        setBreaches(prev => [newBreach, ...prev.slice(0, 14)]);
      }
    }, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* 1. Shield Status & Integrity Matrix */}
      <div className="grid grid-cols-3 gap-2 h-32">
        <WinFrame title="SHIELD_CAPACITY" accentColor="#FF4444" badge="ACTIVE">
          <div className="p-3 flex flex-col justify-center h-full">
            <span style={{ fontFamily: VT, fontSize: '38px', color: '#FF4444', textShadow: '0 0 10px #FF4444' }}>
              {shieldLevel.toFixed(1)}%
            </span>
            <SegmentedBar value={shieldLevel} segments={25} color="#FF4444" height={8} className="mt-1" />
          </div>
        </WinFrame>

        <WinFrame title="THREAT_LEVEL" accentColor="#FF6B00">
          <div className="p-3 flex flex-col items-center justify-center h-full">
             <div className="flex gap-1 mb-2">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} style={{ 
                    width: 12, height: 12, 
                    background: i <= activeThreats ? '#FF6B00' : '#1A1A1A',
                    boxShadow: i <= activeThreats ? '0 0 6px #FF6B00' : 'none'
                  }} />
                ))}
             </div>
             <span style={{ fontSize: '9px', color: '#FF6B00' }}>{activeThreats} ACTIVE VECTOR(S)</span>
          </div>
        </WinFrame>

        <WinFrame title="CORE_INTEGRITY" accentColor="#22C55E">
          <div className="p-3 flex flex-col justify-center h-full">
            <span style={{ fontFamily: VT, fontSize: '32px', color: '#22C55E' }}>{integrity.toFixed(3)}%</span>
            <span style={{ fontSize: '8px', color: '#333', letterSpacing: '0.1em' }}>STABILITY_INDEX</span>
          </div>
        </WinFrame>
      </div>

      <div className="flex gap-2 flex-1">
        {/* 2. Sentinel Breach Log */}
        <WinFrame title="SENTINEL_BREACH_LOG" accentColor="#FF4444" className="flex-1">
          <div className="overflow-y-auto h-full p-1 no-scrollbar">
            <table className="w-full text-left" style={{ fontFamily: MONO, fontSize: '8px' }}>
              <thead className="sticky top-0 bg-[#141414] text-[#555] border-b border-[#2A2A2A]">
                <tr>
                  <th className="p-1 font-normal">TIMESTAMP</th>
                  <th className="p-1 font-normal">ORIGIN_VECTOR</th>
                  <th className="p-1 font-normal">BREACH_TYPE</th>
                  <th className="p-1 font-normal text-right">MITIGATION</th>
                </tr>
              </thead>
              <tbody>
                {breaches.map(b => (
                  <tr key={b.id} className="border-b border-[#1A1A1A] hover:bg-[#FF444408]">
                    <td className="p-1 text-[#444]">{b.time}</td>
                    <td className="p-1 text-[#FF6B00]">{b.source}</td>
                    <td className="p-1 text-[#FF4444]">{b.type}</td>
                    <td className="p-1 text-right" style={{ color: b.status === 'BLOCKED' ? '#22C55E' : '#FF4444' }}>
                      {b.status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </WinFrame>

        {/* 3. Port Sentinel Matrix */}
        <WinFrame title="PORT_SENTINEL" accentColor="#06B6D4" className="w-56">
          <div className="p-3 grid grid-cols-4 gap-2 h-full content-start">
            {ports.map((open, i) => (
              <div key={i} className="flex flex-col items-center gap-1">
                <div style={{ 
                  width: 14, height: 14, 
                  background: open ? '#1A1A1A' : '#FF4444',
                  border: `1px solid ${open ? '#2A2A2A' : '#FF4444'}`,
                  boxShadow: open ? 'none' : '0 0 6px #FF4444'
                }} />
                <span style={{ fontSize: '6px', color: '#333' }}>P_{80 + i}</span>
              </div>
            ))}
            <div className="col-span-4 mt-4 pt-4 border-t border-[#1A1A1A]">
              <div style={{ 
                background: 'repeating-linear-gradient(45deg, #000, #000 3px, rgba(255,107,0,0.1) 3px, rgba(255,107,0,0.1) 6px)',
                border: '1px solid #FF6B0044',
                padding: '4px', textAlign: 'center'
              }}>
                <span style={{ fontSize: '7px', color: '#FF6B00', letterSpacing: '0.1em' }}>FIREWALL_ACTIVE</span>
              </div>
            </div>
          </div>
        </WinFrame>
      </div>
    </div>
  );
}
