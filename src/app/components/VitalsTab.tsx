import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';
import { useSentinel } from './SentinelProvider';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

// Simulation Utilities
const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(max, val));
const jitter = (val: number, range: number, min: number, max: number) => clamp(val + (Math.random() - 0.5) * range, min, max);

export function VitalsTab() {
  const { isConnected, data: sentinelData } = useSentinel();
  const [demoData, setDemoData] = useState({
    cpu: { totalLoad: 38.4, temp: 74, clock: 5127 },
    gpu: { load: 72, vram: 8.4, temp: 68 },
    thermal: { mbd: 56, case: 45, ambient: 29 },
    storage: { drive1: 45, drive2: 28 },
    memory: { used: 23.9, speed: 6000 },
    net: { dl: 952.6, ul: 101.3 }
  });

  // Use real data if connected, otherwise use demo jitter
  const data = isConnected && sentinelData ? {
    cpu: sentinelData.cpu,
    gpu: sentinelData.gpu,
    thermal: sentinelData.thermal,
    storage: { 
      drive1: sentinelData.storage.drives[0]?.health || 0, 
      drive2: sentinelData.storage.drives[1]?.health || 0 
    },
    memory: sentinelData.memory,
    net: { 
      dl: sentinelData.network.download, 
      ul: sentinelData.network.upload 
    }
  } : demoData;

  // Demo jitter simulation (only runs when disconnected)
  useEffect(() => {
    if (isConnected) return; // Skip demo mode if connected
    
    const t = setInterval(() => {
      setDemoData(prev => ({
        cpu: {
          totalLoad: jitter(prev.cpu.totalLoad, 12, 5, 95),
          temp: jitter(prev.cpu.temp, 2, 65, 92),
          clock: jitter(prev.cpu.clock, 50, 4800, 5200)
        },
        gpu: {
          load: jitter(prev.gpu.load, 5, 55, 85),
          vram: jitter(prev.gpu.vram, 0.2, 7.5, 10),
          temp: jitter(prev.gpu.temp, 1.5, 60, 80)
        },
        thermal: {
          mbd: jitter(prev.thermal.mbd, 1, 40, 65),
          case: jitter(prev.thermal.case, 1, 35, 55),
          ambient: jitter(prev.thermal.ambient, 0.5, 25, 32)
        },
        storage: {
          drive1: jitter(prev.storage.drive1, 5, 10, 90),
          drive2: jitter(prev.storage.drive2, 3, 5, 80)
        },
        memory: {
          used: jitter(prev.memory.used, 0.2, 22, 27),
          speed: 6000
        },
        net: {
          dl: jitter(prev.net.dl, 40, 800, 1000),
          ul: jitter(prev.net.ul, 10, 80, 120)
        }
      }));
    }, 1500);
    return () => clearInterval(t);
  }, [isConnected]);

  return (
    <div className="grid grid-cols-3 grid-rows-2 gap-2 h-full">
      
      {/* 1. STORAGE ARRAY (Mini) */}
      <WinFrame title="STORAGE ARRAY" accentColor="#A855F7" badge="NVME_STABLE">
        <div className="p-3 flex flex-col justify-around h-full">
          <div>
            <div className="flex justify-between text-[8px] mb-1" style={{ color: '#555' }}>
              <span>SYSTEM_C:</span> <span>{data.storage.drive1.toFixed(0)}%</span>
            </div>
            <SegmentedBar value={data.storage.drive1} segments={15} color="#A855F7" height={6} />
          </div>
          <div>
            <div className="flex justify-between text-[8px] mb-1" style={{ color: '#555' }}>
              <span>DATA_D:</span> <span>{data.storage.drive2.toFixed(0)}%</span>
            </div>
            <SegmentedBar value={data.storage.drive2} segments={15} color="#6B3FA0" height={6} />
          </div>
        </div>
      </WinFrame>

      {/* 2. CPU MONITOR (Mini) */}
      <WinFrame title="CPU MONITOR" accentColor="#A855F7" badge="RYZEN_9">
        <div className="p-3 flex flex-col items-center justify-center h-full">
          <span style={{ fontFamily: VT, fontSize: '42px', color: '#A855F7', textShadow: '0 0 10px #A855F7' }}>
            {data.cpu.totalLoad.toFixed(1)}%
          </span>
          <div className="flex gap-4 mt-1">
            <span style={{ fontSize: '9px', color: '#444' }}>{data.cpu.clock.toFixed(0)} MHz</span>
            <span style={{ fontSize: '9px', color: data.cpu.temp > 80 ? '#FF6B00' : '#444' }}>{data.cpu.temp.toFixed(0)}°C</span>
          </div>
        </div>
      </WinFrame>

      {/* 3. THERMAL MATRIX (Mini) */}
      <WinFrame title="THERMAL MATRIX" accentColor="#06B6D4">
        <div className="p-3 grid grid-cols-2 gap-2 h-full">
          {[
            { label: 'MBD', val: data.thermal.mbd, color: '#06B6D4' },
            { label: 'CASE', val: data.thermal.case, color: '#06B6D4' },
            { label: 'AMB', val: data.thermal.ambient, color: '#22C55E' },
            { label: 'VMR', val: 52, color: '#06B6D4' }
          ].map(sensor => (
            <div key={sensor.label} className="border border-[#1A1A1A] p-1 flex flex-col items-center">
              <span style={{ fontSize: '7px', color: '#333' }}>{sensor.label}</span>
              <span style={{ fontSize: '12px', color: sensor.color }}>{sensor.val.toFixed(0)}°</span>
            </div>
          ))}
        </div>
      </WinFrame>

      {/* 4. MEMORY ARRAY (Mini) */}
      <WinFrame title="MEMORY ARRAY" accentColor="#6B3FA0" badge="XMP_ACTIVE">
        <div className="p-3 flex flex-col justify-center h-full">
          <div className="flex items-baseline gap-2 mb-2">
            <span style={{ fontFamily: VT, fontSize: '28px', color: '#A855F7' }}>{data.memory.used.toFixed(1)}</span>
            <span style={{ fontSize: '10px', color: '#333' }}>GB / 64GB</span>
          </div>
          <SegmentedBar value={(data.memory.used / 64) * 100} segments={20} color="#6B3FA0" height={10} />
        </div>
      </WinFrame>

      {/* 5. GPU MONITOR (Mini) */}
      <WinFrame title="GPU MONITOR" accentColor="#FF6B00" badge="RTX_4090">
        <div className="p-3 flex items-center gap-4 h-full">
          <div className="relative w-16 h-16 border-2 border-[#1A1A1A] flex items-center justify-center">
             <span style={{ fontFamily: VT, fontSize: '20px', color: '#FF6B00' }}>{data.gpu.load.toFixed(0)}%</span>
             <div className="absolute inset-0 border border-[#FF6B0033] shadow-[inset_0_0_10px_#FF6B0022]" />
          </div>
          <div className="flex flex-col gap-1">
            <span style={{ fontSize: '9px', color: '#444' }}>VRAM: {data.gpu.vram.toFixed(1)}GB</span>
            <span style={{ fontSize: '9px', color: '#444' }}>TEMP: {data.gpu.temp.toFixed(0)}°C</span>
          </div>
        </div>
      </WinFrame>

      {/* 6. NET INTERFACE (Mini) */}
      <WinFrame title="NET INTERFACE" accentColor="#22C55E">
        <div className="p-3 flex flex-col justify-around h-full">
          <div className="flex flex-col">
            <span style={{ fontSize: '8px', color: '#22C55E' }}>DOWNLOAD</span>
            <span style={{ fontFamily: VT, fontSize: '18px', color: '#E2E8F0' }}>{data.net.dl.toFixed(1)} Mbps</span>
          </div>
          <div className="flex flex-col">
            <span style={{ fontSize: '8px', color: '#06B6D4' }}>UPLOAD</span>
            <span style={{ fontFamily: VT, fontSize: '18px', color: '#E2E8F0' }}>{data.net.ul.toFixed(1)} Mbps</span>
          </div>
        </div>
      </WinFrame>

    </div>
  );
}
