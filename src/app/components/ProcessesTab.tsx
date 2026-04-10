import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';

const MONO = "'Share Tech Mono', monospace";

// Simulation Constants
const PROCESS_NAMES = [
  'vitreos.exe', 'kernel_task', 'system_pulse', 'discord.exe', 
  'chrome.exe', 'nvidia-smi', 'ssh-agent', 'dockerd',
  'node_runner', 'listener.py', 'shield_sentinel', 'mem_cache'
];

interface Process {
  pid: number;
  name: string;
  cpu: number;
  mem: number;
  status: 'RUNNING' | 'SLEEP' | 'WAIT';
}

type SortKey = 'pid' | 'name' | 'cpu' | 'mem';

export function ProcessesTab() {
  const [processes, setProcesses] = useState<Process[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('cpu');
  const [sortAsc, setSortAsc] = useState(false);

  // Initial Seed
  useEffect(() => {
    const initial = Array.from({ length: 14 }, (_, i) => ({
      pid: 1000 + Math.floor(Math.random() * 9000),
      name: PROCESS_NAMES[i % PROCESS_NAMES.length],
      cpu: Math.random() * 40,
      mem: Math.random() * 1024,
      status: 'RUNNING' as const
    }));
    setProcesses(initial);
  }, []);

  // Real-time Jitter Simulation
  useEffect(() => {
    const t = setInterval(() => {
      setProcesses(prev => prev.map(p => ({
        ...p,
        cpu: Math.max(0, Math.min(99, p.cpu + (Math.random() - 0.5) * 15)),
        mem: Math.max(16, p.mem + (Math.random() - 0.5) * 50)
      })));
    }, 1200);
    return () => clearInterval(t);
  }, []);

  const sorted = [...processes].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortAsc ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
  });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  return (
    <WinFrame title="TASK_ORCHESTRATOR // PROCESS_FEED" accentColor="#06B6D4" badge="LIVE_RECALL">
      <div className="flex flex-col h-full" style={{ background: '#0D0D0D' }}>
        {/* Table Header */}
        <div className="grid grid-cols-12 border-b border-[#2A2A2A] bg-[#141414] py-1 px-3">
          {[
            { label: 'PID', key: 'pid', span: 'col-span-2' },
            { label: 'IDENTIFIER', key: 'name', span: 'col-span-4' },
            { label: 'LOAD_UNIT', key: 'cpu', span: 'col-span-3' },
            { label: 'MEM_ALLOC', key: 'mem', span: 'col-span-3' }
          ].map(col => (
            <button
              key={col.key}
              onClick={() => toggleSort(col.key as SortKey)}
              className={`${col.span} text-left text-[8px] tracking-widest hover:text-[#06B6D4] transition-colors`}
              style={{ color: sortKey === col.key ? '#06B6D4' : '#444', fontFamily: MONO }}
            >
              {col.label} {sortKey === col.key ? (sortAsc ? '▲' : '▼') : ''}
            </button>
          ))}
        </div>

        {/* Process List */}
        <div className="flex-1 overflow-y-auto no-scrollbar">
          {sorted.map(p => {
            // High load threshold turns orange
            const isHighLoad = p.cpu > 75;
            const accent = isHighLoad ? '#FF6B00' : '#06B6D4';
            
            return (
              <div 
                key={p.pid} 
                className="grid grid-cols-12 px-3 py-2 border-b border-[#1A1A1A] items-center hover:bg-[#06B6D405]"
                style={{ background: isHighLoad ? 'rgba(255, 107, 0, 0.05)' : 'transparent' }}
              >
                <span className="col-span-2 text-[9px] text-[#333]" style={{ fontFamily: MONO }}>{p.pid}</span>
                <span 
                  className="col-span-4 text-[10px] truncate pr-2" 
                  style={{ 
                    color: accent, 
                    fontFamily: MONO,
                    textShadow: isHighLoad ? `0 0 8px ${accent}` : 'none' 
                  }}
                >
                  {p.name.toUpperCase()}
                </span>
                <div className="col-span-3 flex items-center gap-2 pr-4">
                  <SegmentedBar value={p.cpu} segments={8} color={accent} height={6} />
                  <span className="text-[9px]" style={{ color: isHighLoad ? accent : '#555', fontFamily: MONO }}>
                    {p.cpu.toFixed(1)}%
                  </span>
                </div>
                <span className="col-span-3 text-[9px] text-[#444] text-right" style={{ fontFamily: MONO }}>
                  {p.mem.toFixed(0)} MB
                </span>
              </div>
            );
          })}
        </div>

        {/* Footer Metrics */}
        <div className="p-2 border-t border-[#2A2A2A] bg-[#0A0A0A] flex justify-between">
          <span style={{ fontSize: '8px', color: '#333', fontFamily: MONO }}>ACTIVE_THREADS: {processes.length}</span>
          <span style={{ fontSize: '8px', color: '#FF6B00', fontFamily: MONO }}>HOG_PROCESSES: {processes.filter(p => p.cpu > 75).length}</span>
        </div>
      </div>
    </WinFrame>
  );
}
