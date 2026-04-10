import { useState, useEffect } from 'react';
import { SystemPulseLog } from './components/SystemPulseLog';
import { SentinelProvider } from './components/SentinelProvider';

// --- TAB IMPORTS (Phase 1, 2 & 3) ---
import { VitalsTab } from './components/VitalsTab';
import { NetworkTab } from './components/NetworkTab';
import { ProcessesTab } from './components/ProcessesTab';
import { GpuProTab } from './components/GpuProTab';
import { StorageTab } from './components/StorageTab';
import { ConsoleTab } from './components/ConsoleTab';
import { SecurityTab } from './components/SecurityTab';
import { LogbookTab } from './components/LogbookTab';
import { RemoteTab } from './components/RemoteTab';
import { SettingsTab } from './components/SettingsTab';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

type TabName = 'VITALS' | 'NETWORK' | 'PROCESSES' | 'GPU PRO' | 'SECURITY' | 'STORAGE' | 'LOGBOOK' | 'REMOTE' | 'CONSOLE' | 'SETTINGS';

const TABS: TabName[] = ['VITALS', 'NETWORK', 'PROCESSES', 'GPU PRO', 'SECURITY', 'STORAGE', 'LOGBOOK', 'REMOTE', 'CONSOLE', 'SETTINGS'];

const TAB_COLORS: Partial<Record<TabName, string>> = {
  VITALS: '#A855F7',
  NETWORK: '#22C55E',
  PROCESSES: '#06B6D4',
  'GPU PRO': '#FF6B00',
  SECURITY: '#FF4444',
  STORAGE: '#A855F7',
  LOGBOOK: '#6B3FA0',
  REMOTE: '#A855F7',
  CONSOLE: '#22C55E',
  SETTINGS: '#06B6D4',
};

function PlaceholderTab({ name }: { name: string }) {
  const [blink, setBlink] = useState(true);
  useEffect(() => {
    const t = setInterval(() => setBlink(b => !b), 600);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-full" style={{ color: '#1E1E1E' }}>
      <div style={{ fontFamily: MONO, fontSize: '9px', color: '#1E1E1E', lineHeight: 1.4, marginBottom: '24px', textAlign: 'center' }}>
        {'╔══════════════════════════════╗'}<br />
        {'║                              ║'}<br />
        {'║   MODULE OFFLINE / STANDBY   ║'}<br />
        {'║                              ║'}<br />
        {'╚══════════════════════════════╝'}
      </div>
      <div style={{ fontFamily: VT, fontSize: '48px', color: '#1A1A1A', letterSpacing: '0.1em', textShadow: '0 0 20px rgba(168,85,247,0.05)' }}>
        [ {name} ]
      </div>
      <div style={{ fontFamily: MONO, fontSize: '10px', color: '#222', marginTop: '12px', letterSpacing: '0.2em' }}>
        // INITIALIZE MODULE TO ACCESS {blink ? '█' : ' '}
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabName>('VITALS');
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const timeStr = `${String(time.getHours()).padStart(2, '0')}:${String(time.getMinutes()).padStart(2, '0')}:${String(time.getSeconds()).padStart(2, '0')}`;

  const renderTab = () => {
    switch (activeTab) {
      case 'VITALS': return <VitalsTab />;
      case 'NETWORK': return <NetworkTab />;
      case 'PROCESSES': return <ProcessesTab />;
      case 'GPU PRO': return <GpuProTab />;
      case 'SECURITY': return <SecurityTab />;
      case 'STORAGE': return <StorageTab />;
      case 'LOGBOOK': return <LogbookTab />;
      case 'REMOTE': return <RemoteTab />;
      case 'CONSOLE': return <ConsoleTab />;
      case 'SETTINGS': return <SettingsTab />;
      default: return <PlaceholderTab name={activeTab} />;
    }
  };

  return (
    <SentinelProvider>
      <div className="flex flex-col h-screen overflow-hidden select-none" style={{ background: '#0D0D0D', fontFamily: MONO }}>
      
      {/* ─── TOP NAVIGATION BAR (38px) ─── */}
      <div 
        data-tauri-drag-region
        className="flex items-stretch flex-shrink-0" 
        style={{ background: '#111111', borderBottom: '1px solid #2A2A2A', height: '38px' }}
      >
        <div 
          data-tauri-drag-region
          className="flex items-center px-4 flex-shrink-0" 
          style={{ borderRight: '1px solid #2A2A2A', minWidth: '232px' }}
        >
          <span style={{ fontFamily: VT, fontSize: '22px', color: '#A855F7', textShadow: '0 0 10px #A855F7, 0 0 20px #7C3AED', letterSpacing: '0.15em' }}>
            VITREOS
          </span>
          <span style={{ fontFamily: MONO, fontSize: '7px', color: '#3D1F6B', marginLeft: '8px', letterSpacing: '0.15em' }}>
            v2.1
          </span>
        </div>

        {/* Tabs Scroller */}
        <div className="flex flex-1 overflow-x-auto no-scrollbar">
          {TABS.map(tab => {
            const isActive = activeTab === tab;
            const color = TAB_COLORS[tab] || '#A855F7';
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  fontFamily: MONO, fontSize: '9px', letterSpacing: '0.1em',
                  padding: '0 14px',
                  color: isActive ? color : '#3A3A3A',
                  background: isActive ? `${color}11` : 'transparent',
                  borderRight: '1px solid #1E1E1E',
                  borderBottom: isActive ? `2px solid ${color}` : '2px solid transparent',
                  textShadow: isActive ? `0 0 8px ${color}` : 'none',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                  flexShrink: 0,
                }}
              >
                {tab}
              </button>
            );
          })}
        </div>

        {/* System Time & Controls */}
        <div className="flex items-center gap-2 px-3 flex-shrink-0" style={{ borderLeft: '1px solid #1E1E1E' }}>
          <span style={{ color: '#2A2A2A', fontFamily: MONO, fontSize: '8px' }}>{timeStr}</span>
          {['_', '□', '×'].map((sym, i) => (
            <button key={sym} className="hover:bg-[#222]" style={{
              width: '16px', height: '16px',
              border: `1px solid ${i === 2 ? '#FF444444' : '#2A2A2A'}`,
              background: '#161616',
              color: i === 2 ? '#FF4444' : '#444',
              fontFamily: MONO, fontSize: '9px',
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            }}>{sym}</button>
          ))}
        </div>
      </div>

      {/* ─── MAIN BODY ─── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Fixed Sidebar */}
        <SystemPulseLog />

        {/* Dynamic Content Area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-hidden p-2">
            {renderTab()}
          </div>

          {/* ─── STATUS BAR (20px) ─── */}
          <div className="flex items-center justify-between px-3 flex-shrink-0" style={{ background: '#0A0A0A', borderTop: '1px solid #1A1A1A', height: '20px' }}>
            <div className="flex items-center gap-4">
              <span style={{ color: '#2A2A2A', fontFamily: MONO, fontSize: '7px' }}>BIOS: F21b | ASUS CROSSHAIR X670E</span>
              <span style={{ color: '#2A2A2A', fontFamily: MONO, fontSize: '7px' }}>KERNEL: 6.6.2-ARCH1</span>
            </div>
            <div className="flex items-center gap-4">
              {[
                { label: '● CPU OK', color: '#A855F7' },
                { label: '● GPU WARN', color: '#FF6B00' },
                { label: '● MEM OK', color: '#22C55E' },
                { label: '● NET OK', color: '#22C55E' },
              ].map(({ label, color }) => (
                <span key={label} style={{ color, fontFamily: MONO, fontSize: '7px', textShadow: `0 0 4px ${color}` }}>{label}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ─── GLOBAL OVERLAYS (z-50) ─── */}
      {/* Scanline Pattern */}
      <div className="fixed inset-0 pointer-events-none z-50 opacity-60" style={{
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
      }} />
      {/* CRT Vignette */}
      <div className="fixed inset-0 pointer-events-none z-50" style={{
        background: 'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.4) 100%)',
      }} />
      </div>
    </SentinelProvider>
  );
}
