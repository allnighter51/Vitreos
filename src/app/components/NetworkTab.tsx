import { useState, useEffect, useRef } from 'react';
import { WinFrame } from './WinFrame';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

const INTERFACES = ['ETH0', 'WLAN0', 'TUN0'] as const;
type Interface = typeof INTERFACES[number];
const PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'HTTP', 'SSH', 'DNS'];

// Simulation Utilities
const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(max, val));
const jitter = (val: number, range: number, min?: number, max?: number) => {
  const result = val + (Math.random() - 0.5) * range;
  return min !== undefined && max !== undefined ? clamp(result, min, max) : result;
};
const randomIP = () => `${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}`;

interface Packet { id: number; src: string; dst: string; protocol: string; size: number; time: string; }

export function NetworkTab() {
  const [activeInterface, setActiveInterface] = useState<Interface>('ETH0');
  const [inData, setInData] = useState<number[]>(new Array(60).fill(0));
  const [outData, setOutData] = useState<number[]>(new Array(60).fill(0));
  const [packets, setPackets] = useState<Packet[]>([]);
  const [stats, setStats] = useState({ in: 0, out: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const packetIdRef = useRef(0);

  // Bandwidth & Packet Simulation
  useEffect(() => {
    const t = setInterval(() => {
      const inSpeed = clamp(jitter(45, 30), 0, 100);
      const outSpeed = clamp(jitter(25, 20), 0, 100);
      
      setInData(prev => [...prev.slice(-59), inSpeed]);
      setOutData(prev => [...prev.slice(-59), outSpeed]);
      setStats({ in: inSpeed, out: outSpeed });

      // Generate Packet
      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}.${String(now.getMilliseconds()).padStart(3,'0')}`;
      const newPacket: Packet = {
        id: packetIdRef.current++,
        src: randomIP(),
        dst: randomIP(),
        protocol: PROTOCOLS[Math.floor(Math.random() * PROTOCOLS.length)],
        size: Math.floor(jitter(512, 1024)),
        time: timeStr,
      };
      setPackets(prev => [...prev.slice(-40), newPacket]);
    }, 150);
    return () => clearInterval(t);
  }, []);

  // Canvas Wave Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.fillStyle = '#0D0D0D'; ctx.fillRect(0, 0, rect.width, rect.height);
    
    // Grid Lines
    ctx.strokeStyle = '#1A1A1A'; ctx.lineWidth = 1;
    for(let i=1; i<4; i++) {
        const y = (rect.height/4) * i;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(rect.width, y); ctx.stroke();
    }

    const drawWave = (data: number[], color: string) => {
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.shadowBlur = 8; ctx.shadowColor = color;
      ctx.beginPath();
      data.forEach((val, i) => {
        const x = (rect.width / 60) * i;
        const y = rect.height - (val / 100) * rect.height;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke(); ctx.shadowBlur = 0;
    };

    drawWave(inData, '#22C55E');
    drawWave(outData, '#06B6D4');
  }, [inData, outData]);

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* 1. Traffic Visualization */}
      <WinFrame title="SIGNAL_INTELLIGENCE // BANDWIDTH" accentColor="#22C55E" badge="ENCRYPTED">
        <div className="flex flex-col h-full p-2">
          <div className="flex gap-6 mb-2">
            <div className="flex items-center gap-2">
              <div style={{ width: 8, height: 8, background: '#22C55E', boxShadow: '0 0 6px #22C55E' }} />
              <span style={{ fontSize: '9px', color: '#22C55E' }}>RX: {stats.in.toFixed(1)} Mbps</span>
            </div>
            <div className="flex items-center gap-2">
              <div style={{ width: 8, height: 8, background: '#06B6D4', boxShadow: '0 0 6px #06B6D4' }} />
              <span style={{ fontSize: '9px', color: '#06B6D4' }}>TX: {stats.out.toFixed(1)} Mbps</span>
            </div>
            <span style={{ fontSize: '9px', color: '#444', marginLeft: 'auto' }}>INTERFACE: {activeInterface}</span>
          </div>
          <canvas ref={canvasRef} className="flex-1 w-full h-full border border-[#1A1A1A]" />
        </div>
      </WinFrame>

      <div className="flex gap-2 h-[260px]">
        {/* 2. Packet Intercept Feed */}
        <WinFrame title="PACKET_INTERCEPT_LOG" accentColor="#06B6D4" className="flex-1">
          <div className="overflow-y-auto h-full p-1" style={{ scrollbarWidth: 'none' }}>
            <table className="w-full text-left" style={{ fontFamily: MONO, fontSize: '8px' }}>
              <thead className="sticky top-0 bg-[#141414] text-[#555] border-b border-[#2A2A2A]">
                <tr>
                  <th className="p-1 font-normal">TIMESTAMP</th>
                  <th className="p-1 font-normal">SOURCE_IP</th>
                  <th className="p-1 font-normal">DEST_IP</th>
                  <th className="p-1 font-normal">PROTO</th>
                  <th className="p-1 font-normal text-right">SIZE</th>
                </tr>
              </thead>
              <tbody>
                {packets.map(p => (
                  <tr key={p.id} className="border-b border-[#1A1A1A] hover:bg-[#22C55E08]">
                    <td className="p-1 text-[#444]">{p.time}</td>
                    <td className="p-1 text-[#22C55E]">{p.src}</td>
                    <td className="p-1 text-[#06B6D4]">{p.dst}</td>
                    <td className="p-1 text-[#A855F7]">{p.protocol}</td>
                    <td className="p-1 text-right text-[#666]">{p.size}B</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </WinFrame>

        {/* 3. Interface Control */}
        <WinFrame title="HARDWARE_COMM" accentColor="#A855F7" className="w-48">
          <div className="p-2 flex flex-col gap-2">
            {INTERFACES.map(iface => (
              <button 
                key={iface}
                onClick={() => setActiveInterface(iface)}
                className="p-2 border border-[#2A2A2A] text-left transition-all"
                style={{ 
                  fontFamily: MONO, 
                  fontSize: '10px',
                  color: activeInterface === iface ? '#A855F7' : '#333',
                  background: activeInterface === iface ? '#A855F711' : 'transparent',
                  borderColor: activeInterface === iface ? '#A855F7' : '#2A2A2A',
                  textShadow: activeInterface === iface ? '0 0 8px #A855F7' : 'none'
                }}
              >
                {iface} :: {activeInterface === iface ? 'ONLINE' : 'STANDBY'}
              </button>
            ))}
          </div>
        </WinFrame>
      </div>
    </div>
  );
}
