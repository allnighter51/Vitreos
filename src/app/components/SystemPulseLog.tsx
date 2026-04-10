import { useState, useEffect, useRef } from 'react';

const MONO = "'Share Tech Mono', monospace";

interface LogEntry {
  timestamp: string;
  level: 'OK' | 'SYS' | 'GPU' | 'WARN' | 'CRIT';
  message: string;
}

const LOG_COLORS = {
  OK: '#22C55E',
  SYS: '#06B6D4',
  GPU: '#A855F7',
  WARN: '#FF6B00',
  CRIT: '#FF4444',
};

const SAMPLE_LOGS: Omit<LogEntry, 'timestamp'>[] = [
  { level: 'OK', message: 'NVML initialized' },
  { level: 'SYS', message: 'Thermal sensors online' },
  { level: 'GPU', message: 'CUDA cores detected: 10240' },
  { level: 'OK', message: 'Network interface bound' },
  { level: 'SYS', message: 'Registry watcher active' },
  { level: 'WARN', message: 'CPU temp spike: 78°C' },
  { level: 'OK', message: 'Disk I/O normalized' },
  { level: 'GPU', message: 'VRAM usage: 4.2GB/24GB' },
  { level: 'SYS', message: 'USB device inserted' },
  { level: 'OK', message: 'Ping stable: 12ms' },
];

function getTimestamp() {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
}

export function SystemPulseLog() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      const randomLog = SAMPLE_LOGS[Math.floor(Math.random() * SAMPLE_LOGS.length)];
      setLogs(prev => [...prev.slice(-19), { ...randomLog, timestamp: getTimestamp() }]);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="w-[232px] h-full bg-[#0A0A0A] border-r border-[#1A1A1A] flex flex-col" style={{ borderRadius: 0 }}>
      {/* Header */}
      <div className="h-8 border-b border-[#1A1A1A] flex items-center px-3">
        <span style={{ fontFamily: MONO, fontSize: '11px', color: '#A855F7', textShadow: '0 0 8px #A855F7' }}>
          SYSTEM PULSE
        </span>
      </div>

      {/* Log Feed */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 space-y-1" style={{ scrollbarWidth: 'thin' }}>
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2" style={{ fontFamily: MONO, fontSize: '9px' }}>
            <span className="text-[#444]">{log.timestamp}</span>
            <span style={{ color: LOG_COLORS[log.level], textShadow: `0 0 6px ${LOG_COLORS[log.level]}` }}>
              [{log.level}]
            </span>
            <span className="text-[#666] flex-1">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
