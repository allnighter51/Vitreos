import { useState, useEffect, useRef } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';
import { useSentinel } from './SentinelProvider';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

function jitter(base: number, variance: number) { return base + (Math.random() - 0.5) * variance; }
function clamp(val: number, min: number, max: number) { return Math.max(min, Math.min(max, val)); }

export function GpuProTab() {
  const { isConnected, data: sentinelData } = useSentinel();
  const [frameTimes, setFrameTimes] = useState<number[]>([]);
  const [demoClocks, setDemoClocks] = useState({ core: 2520, shader: 2640, mem: 1313 });
  const [demoActivity, setDemoActivity] = useState({ nvenc: 12, nvdec: 0, compute: 44 });
  const [coreOffset, setCoreOffset] = useState(0);
  const [memOffset, setMemOffset] = useState(0);
  const [ocArmed, setOcArmed] = useState(false);
  const [ocResult, setOcResult] = useState<string>('');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Use real data if connected, otherwise use demo
  const clocks = isConnected && sentinelData ? {
    core: sentinelData.gpu.coreClock,
    shader: sentinelData.gpu.coreClock + 120, // Approximation
    mem: sentinelData.gpu.memClock
  } : demoClocks;

  const activity = isConnected && sentinelData ? {
    nvenc: 12, // Not available in sentinel data, use demo
    nvdec: 0,
    compute: sentinelData.gpu.load
  } : demoActivity;

  // High-frequency Frame Time simulation (approx 60fps jitter)
  useEffect(() => {
    const interval = setInterval(() => {
      const newFrame = clamp(jitter(8.3, 4), 6, 16.6); // Jittering around 120fps (8.3ms)
      setFrameTimes(prev => [...prev.slice(-99), newFrame]);
      
      // Demo jitter (only when disconnected)
      if (!isConnected) {
        setDemoClocks({
          core: Math.floor(jitter(2520, 30)),
          shader: Math.floor(jitter(2640, 30)),
          mem: Math.floor(jitter(1313, 5)),
        });
        setDemoActivity({
          nvenc: clamp(jitter(demoActivity.nvenc, 5), 0, 100),
          nvdec: clamp(jitter(demoActivity.nvdec, 2), 0, 10),
          compute: clamp(jitter(44, 20), 10, 90),
        });
      }
    }, 100);
    return () => clearInterval(interval);
  }, [isConnected, demoActivity.nvenc, demoActivity.nvdec]);

  // Frame Time Sparkline Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.fillStyle = '#080808';
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Draw frame time line
    ctx.strokeStyle = '#FF6B00';
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#FF6B00';
    ctx.beginPath();
    
    frameTimes.forEach((ft, i) => {
      const x = (rect.width / 100) * i;
      const y = rect.height - (ft / 20) * rect.height; // Scaled to 20ms max
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }, [frameTimes]);

  const handleOcCommit = () => {
    if (!ocArmed) {
      setOcArmed(true);
      setTimeout(() => setOcArmed(false), 3000);
      return;
    }

    // Send OC command to backend
    if (isConnected) {
      const ws = new WebSocket('ws://localhost:8000/sentinel');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'ADJUST_CLOCK',
          core_offset: coreOffset,
          mem_offset: memOffset
        }));
      };
      ws.onmessage = (event) => {
        const response = JSON.parse(event.data);
        if (response.type === 'OC_RESULT') {
          setOcResult(response.success ? 'OC COMMITTED' : `ERROR: ${response.error}`);
          setTimeout(() => setOcResult(''), 5000);
        }
        ws.close();
      };
    } else {
      setOcResult('BACKEND DISCONNECTED');
      setTimeout(() => setOcResult(''), 3000);
    }
    
    setOcArmed(false);
  };

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* Upper: Clocks & Frame Time */}
      <div className="grid grid-cols-12 gap-2 flex-1">
        {/* Frame Time Monitor */}
        <WinFrame title="FRAME TIME LATENCY" accentColor="#FF6B00" badge="120Hz" className="col-span-8">
          <div className="flex flex-col h-full p-2">
            <div className="flex justify-between mb-1" style={{ fontFamily: MONO, fontSize: '9px' }}>
              <span className="text-[#FF6B00]">CURRENT: {frameTimes[frameTimes.length - 1]?.toFixed(2)}ms</span>
              <span className="text-[#444]">TARGET: 8.33ms (6.0ms - 16.6ms)</span>
            </div>
            <canvas ref={canvasRef} className="flex-1 w-full h-full" />
          </div>
        </WinFrame>

        {/* Clock Matrix */}
        <WinFrame title="CLOCK MATRIX" accentColor="#FF6B00" className="col-span-4">
          <div className="flex flex-col justify-around h-full p-3 bg-[#0A0A0A]">
            {[
              { label: 'CORE_CLK', val: clocks.core, unit: 'MHz' },
              { label: 'SHDR_CLK', val: clocks.shader, unit: 'MHz' },
              { label: 'MEM_CLK', val: clocks.mem, unit: 'MHz' },
            ].map(c => (
              <div key={c.label} className="flex flex-col border-b border-[#1A1A1A] last:border-0 pb-2">
                <span style={{ fontFamily: MONO, fontSize: '8px', color: '#444' }}>{c.label}</span>
                <div className="flex items-baseline gap-2">
                  <span style={{ fontFamily: VT, fontSize: '32px', color: '#FF6B00', textShadow: '0 0 10px #FF6B00' }}>{c.val}</span>
                  <span style={{ fontFamily: MONO, fontSize: '9px', color: '#333' }}>{c.unit}</span>
                </div>
              </div>
            ))}
          </div>
        </WinFrame>
      </div>

      {/* Lower: Engines, Activity & OC Control */}
      <div className="grid grid-cols-4 gap-2 h-40">
        <WinFrame title="NVENC ACTIVITY" accentColor="#A855F7">
          <div className="p-3 flex flex-col justify-center h-full gap-2">
            <span style={{ fontFamily: MONO, fontSize: '10px', color: '#A855F7' }}>ENCODER LOAD: {activity.nvenc.toFixed(1)}%</span>
            <SegmentedBar value={activity.nvenc} segments={30} color="#A855F7" height={12} />
          </div>
        </WinFrame>
        <WinFrame title="NVDEC ACTIVITY" accentColor="#6B3FA0">
          <div className="p-3 flex flex-col justify-center h-full gap-2 opacity-50">
            <span style={{ fontFamily: MONO, fontSize: '10px', color: '#6B3FA0' }}>DECODER LOAD: {activity.nvdec.toFixed(1)}%</span>
            <SegmentedBar value={activity.nvdec} segments={30} color="#6B3FA0" height={12} />
          </div>
        </WinFrame>
        <WinFrame title="COMPUTE WORKLOAD" accentColor="#06B6D4">
          <div className="p-3 flex flex-col justify-center h-full gap-2">
            <span style={{ fontFamily: MONO, fontSize: '10px', color: '#06B6D4' }}>CUDA UTIL: {activity.compute.toFixed(1)}%</span>
            <SegmentedBar value={activity.compute} segments={30} color="#06B6D4" height={12} />
          </div>
        </WinFrame>
        
        {/* OC CONTROL PANEL */}
        <WinFrame title="HARDWARE_COMMIT // OC_ADJUST" accentColor="#FF6B00" badge="⚠ DANGER">
          <div className="p-2 flex flex-col justify-between h-full gap-1">
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <span style={{ fontFamily: MONO, fontSize: '7px', color: '#FF6B00' }}>CORE_OFFSET</span>
                <span style={{ fontFamily: MONO, fontSize: '8px', color: '#E2E8F0' }}>{coreOffset > 0 ? '+' : ''}{coreOffset}MHz</span>
              </div>
              <input
                type="range"
                min="-100"
                max="250"
                value={coreOffset}
                onChange={(e) => setCoreOffset(Number(e.target.value))}
                className="w-full h-1 bg-[#1A1A1A] appearance-none cursor-pointer"
                style={{ border: '1px solid #FF6B0044', borderRadius: 0 }}
              />
            </div>
            
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <span style={{ fontFamily: MONO, fontSize: '7px', color: '#FF6B00' }}>MEM_OFFSET</span>
                <span style={{ fontFamily: MONO, fontSize: '8px', color: '#E2E8F0' }}>{memOffset > 0 ? '+' : ''}{memOffset}MHz</span>
              </div>
              <input
                type="range"
                min="-100"
                max="500"
                value={memOffset}
                onChange={(e) => setMemOffset(Number(e.target.value))}
                className="w-full h-1 bg-[#1A1A1A] appearance-none cursor-pointer"
                style={{ border: '1px solid #FF6B0044', borderRadius: 0 }}
              />
            </div>
            
            <button
              onClick={handleOcCommit}
              style={{
                background: 'repeating-linear-gradient(45deg, #000, #000 5px, rgba(255,107,0,0.2) 5px, rgba(255,107,0,0.2) 10px)',
                border: `2px solid ${ocArmed ? '#FF4444' : '#FF6B00'}`,
                color: ocArmed ? '#FF4444' : '#FF6B00',
                fontFamily: VT,
                fontSize: '14px',
                padding: '4px',
                textShadow: `0 0 10px ${ocArmed ? '#FF4444' : '#FF6B00'}`,
                boxShadow: `0 0 12px ${ocArmed ? '#FF444444' : '#FF6B0044'}`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                letterSpacing: '0.05em'
              }}
            >
              {ocArmed ? '⚠ CONFIRM ⚠' : 'COMMIT_TO_SILICON'}
            </button>
            
            {ocResult && (
              <span style={{ fontFamily: MONO, fontSize: '6px', color: '#FF6B00', textAlign: 'center', letterSpacing: '0.1em' }}>
                {ocResult}
              </span>
            )}
          </div>
        </WinFrame>
      </div>
    </div>
  );
}
