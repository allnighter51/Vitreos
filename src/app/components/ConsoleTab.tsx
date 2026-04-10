import { useState, useEffect, useRef } from 'react';
import { WinFrame } from './WinFrame';

const MONO = "'Share Tech Mono', monospace";

const BOOT_LOG = [
  '[ 0.000000] Initializing VITREOS kernel...',
  '[ 0.124532] CPU: AMD Ryzen 9 7950X 16-Core Processor',
  '[ 0.256891] Memory: 65536MB DDR5-6000',
  '[ 0.389234] GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)',
  '[ 0.512678] Loading hardware monitoring drivers...',
  '[ 0.645123] [OK] CPU thermal sensors initialized',
  '[ 0.778456] [OK] GPU telemetry interface ready',
  '[ 0.901789] [OK] Network stack initialized',
  '[ 1.034512] [OK] Storage controllers detected',
  '[ 1.167845] Mounting filesystems...',
  '[ 1.301178] [OK] /dev/nvme0n1p1 mounted at /',
  '[ 1.434511] [OK] /dev/nvme1n1p1 mounted at /data',
  '[ 1.567844] Starting system services...',
  '[ 1.701177] [OK] Hardware monitor daemon started',
  '[ 1.834510] [OK] Security sentinel active',
  '[ 1.967843] [OK] Network analyzer online',
  '[ 2.101176] System initialization complete.',
  '[ 2.234509] VITREOS v2.1 ready.',
  '',
  'root@vitreos:~# _',
];

export function ConsoleTab() {
  const [lines, setLines] = useState<string[]>([]);
  const [cursor, setCursor] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let i = 0;
    const t = setInterval(() => {
      if (i < BOOT_LOG.length) {
        setLines(prev => [...prev, BOOT_LOG[i]]);
        i++;
      } else {
        clearInterval(t);
      }
    }, 60);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setCursor(c => !c), 530);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <WinFrame title="SYSTEM_CONSOLE // TTY1" accentColor="#22C55E">
      <div 
        ref={containerRef}
        className="h-full bg-black p-4 overflow-y-auto no-scrollbar"
        style={{ fontFamily: MONO, fontSize: '10px', lineHeight: '1.4' }}
      >
        {lines.map((line, idx) => (
          <div key={idx} style={{ color: idx === lines.length - 1 ? '#22C55E' : '#444' }}>
            {line.replace('_', cursor ? '█' : ' ')}
          </div>
        ))}
      </div>
    </WinFrame>
  );
}
