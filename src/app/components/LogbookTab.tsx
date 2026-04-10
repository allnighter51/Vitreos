import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

type Severity = 'CRIT' | 'WARN' | 'INFO' | 'SYS' | 'ALL';

interface LogEntry {
  id: string;
  timestamp: string;
  severity: Exclude<Severity, 'ALL'>;
  component: string;
  event: string;
}

const COMPONENTS = ['KERNEL', 'GPU_DRV', 'NET_STACK', 'SEC_SENTINEL', 'THERMAL_SENS', 'STORAGE_CTRL'];
const EVENTS = {
  CRIT: ['THERMAL_THROTTLING_ACTIVE', 'VOLTAGE_SAG_DETECTED', 'KERNEL_PANIC_PREVENTED'],
  WARN: ['FAN_RPM_FLUCTUATION', 'HIGH_MEM_PRESSURE', 'UNAUTH_PORT_SCAN'],
  INFO: ['NETWORK_INTERFACE_UP', 'STORAGE_OPTIMIZATION_COMPLETE', 'UPDATE_CHECK_PASSED'],
  SYS: ['BOOT_SEQUENCE_OK', 'SENTINEL_SHIELD_SYNCED', 'HEARTBEAT_ACKNOWLEDGED']
};

export function LogbookTab() {
  const [filter, setFilter] = useState<Severity>('ALL');
  const [search, setSearch] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Generate Initial Archive
  useEffect(() => {
    const initialLogs: LogEntry[] = Array.from({ length: 40 }, (_, i) => {
      const sevs: Exclude<Severity, 'ALL'>[] = ['CRIT', 'WARN', 'INFO', 'SYS'];
      const sev = sevs[Math.floor(Math.random() * sevs.length)];
      return {
        id: Math.random().toString(36).substr(2, 9).toUpperCase(),
        timestamp: `2026-04-09 ${10 + Math.floor(i/4)}:${10 + (i%50)}:${20 + (i%30)}`,
        severity: sev,
        component: COMPONENTS[Math.floor(Math.random() * COMPONENTS.length)],
        event: EVENTS[sev][Math.floor(Math.random() * EVENTS[sev].length)]
      };
    });
    setLogs(initialLogs.reverse());
  }, []);

  const filteredLogs = logs.filter(l => 
    (filter === 'ALL' || l.severity === filter) &&
    (l.event.toLowerCase().includes(search.toLowerCase()) || l.component.toLowerCase().includes(search.toLowerCase()))
  );

  const getSevColor = (sev: Severity) => {
    switch (sev) {
      case 'CRIT': return '#FF4444';
      case 'WARN': return '#FF6B00';
      case 'INFO': return '#06B6D4';
      case 'SYS': return '#A855F7';
      default: return '#E2E8F0';
    }
  };

  return (
    <WinFrame title="SYSTEM_AUDIT_LOG // HISTORICAL_ARCHIVE" accentColor="#6B3FA0" badge="DB_CONNECTED">
      <div className="flex flex-col h-full bg-[#0D0D0D]">
        
        {/* 1. Control Bar */}
        <div className="flex items-center justify-between p-2 border-b border-[#2A2A2A] bg-[#111111]">
          <div className="flex gap-2">
            {(['ALL', 'CRIT', 'WARN', 'INFO', 'SYS'] as Severity[]).map(s => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                style={{
                  background: filter === s ? 'repeating-linear-gradient(45deg, #000, #000 3px, rgba(255,107,0,0.1) 3px, rgba(255,107,0,0.1) 6px)' : 'transparent',
                  border: `1px solid ${filter === s ? '#FF6B00' : '#2A2A2A'}`,
                  color: filter === s ? '#FF6B00' : '#444',
                  fontFamily: MONO, fontSize: '8px', padding: '2px 8px',
                  letterSpacing: '0.1em', transition: 'all 0.1s ease'
                }}
              >
                {s}
              </button>
            ))}
          </div>
          
          <div className="flex items-center gap-2 border border-[#2A2A2A] px-2 py-1 bg-[#050505]">
            <span style={{ color: '#A855F7', fontSize: '9px', fontFamily: MONO }}>QUERY:</span>
            <input 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="SEARCH_DB..."
              className="bg-transparent border-none outline-none text-[9px] text-[#888] w-32"
              style={{ fontFamily: MONO }}
            />
          </div>
        </div>

        {/* 2. Audit Table */}
        <div className="flex-1 overflow-y-auto no-scrollbar">
          <table className="w-full text-left" style={{ fontFamily: MONO, fontSize: '9px' }}>
            <thead className="sticky top-0 bg-[#141414] text-[#333] border-b border-[#2A2A2A]">
              <tr>
                <th className="p-2 font-normal">TIMESTAMP</th>
                <th className="p-2 font-normal">SEVERITY</th>
                <th className="p-2 font-normal">COMPONENT</th>
                <th className="p-2 font-normal">EVENT_ID</th>
                <th className="p-2 font-normal">DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.id} className="border-b border-[#161616] hover:bg-[#A855F705]">
                  <td className="p-2 text-[#444]">{log.timestamp}</td>
                  <td className="p-2">
                    <span style={{ 
                      color: getSevColor(log.severity), 
                      textShadow: log.severity === 'CRIT' ? `0 0 6px ${getSevColor(log.severity)}` : 'none'
                    }}>
                      [{log.severity}]
                    </span>
                  </td>
                  <td className="p-2 text-[#06B6D4]">{log.component}</td>
                  <td className="p-2 text-[#333]">{log.id}</td>
                  <td className="p-2 text-[#888] truncate max-w-[300px]">{log.event}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 3. Footer Stats */}
        <div className="px-3 py-1 bg-[#0A0A0A] border-t border-[#2A2A2A] flex justify-between">
          <span style={{ fontSize: '7px', color: '#222' }}>DB_RECORDS_INDEXED: {logs.length}</span>
          <span style={{ fontSize: '7px', color: '#222' }}>FILTRATION_RESULT: {filteredLogs.length}</span>
        </div>
      </div>
    </WinFrame>
  );
}
