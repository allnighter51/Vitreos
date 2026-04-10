import { useState, useEffect } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';

const MONO = "'Share Tech Mono', monospace";

interface Drive {
  id: string;
  model: string;
  type: 'NVMe' | 'HDD';
  temp: number;
  used: number;
  total: number;
  read: number;
  write: number;
  health: number;
}

export function StorageTab() {
  const [drives, setDrives] = useState<Drive[]>([
    { id: '0', model: 'WD_BLACK SN850X', type: 'NVMe', temp: 42, used: 450, total: 2000, read: 1420, write: 840, health: 99 },
    { id: '1', model: 'SAMSUNG 990 PRO', type: 'NVMe', temp: 38, used: 780, total: 1000, read: 2100, write: 1150, health: 100 },
    { id: '2', model: 'SEAGATE IRONWOLF', type: 'HDD', temp: 34, used: 6200, total: 8000, read: 180, write: 165, health: 94 }
  ]);

  useEffect(() => {
    const t = setInterval(() => {
      setDrives(prev => prev.map(d => ({
        ...d,
        temp: Math.max(30, Math.min(65, d.temp + (Math.random() - 0.5) * 2)),
        read: Math.max(0, d.read + (Math.random() - 0.5) * 100),
        write: Math.max(0, d.write + (Math.random() - 0.5) * 80)
      })));
    }, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex flex-col gap-2 h-full">
      <div className="grid grid-cols-2 gap-2 flex-1">
        {drives.map(drive => (
          <WinFrame key={drive.id} title={`${drive.type} // ${drive.model}`} accentColor="#A855F7" badge={`${drive.health}% HEALTH`}>
            <div className="p-3 flex flex-col h-full gap-4">
              <div className="flex justify-between items-center">
                <div className="flex flex-col">
                  <span style={{ fontSize: '7px', color: '#444', fontFamily: MONO }}>TEMPERATURE</span>
                  <span style={{ fontSize: '18px', color: drive.temp > 45 ? '#FF6B00' : '#A855F7', fontFamily: MONO }}>{drive.temp.toFixed(0)}°C</span>
                </div>
                <div className="text-right">
                  <span style={{ fontSize: '7px', color: '#444', fontFamily: MONO }}>VOLUME_USAGE</span>
                  <div className="flex gap-2 items-center">
                     <span style={{ fontSize: '10px', color: '#E2E8F0', fontFamily: MONO }}>{((drive.used/drive.total)*100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Partition Map Visualization */}
              <div className="h-12 border border-[#1A1A1A] bg-[#080808] flex overflow-hidden">
                <div style={{ width: `${(drive.used/drive.total)*100}%`, background: '#A855F733' }} className="h-full border-r border-[#A855F7] flex items-center px-2">
                  <span style={{ fontSize: '7px', color: '#A855F7', fontFamily: MONO }}>USED</span>
                </div>
                <div className="flex-1 flex items-center px-2">
                  <span style={{ fontSize: '7px', color: '#333', fontFamily: MONO }}>FREE_SPACE: {drive.total - drive.used}GB</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-auto">
                <div>
                  <div className="flex justify-between text-[7px] mb-1" style={{ color: '#22C55E', fontFamily: MONO }}>
                    <span>READ_SPD</span> <span>{drive.read.toFixed(0)} MB/s</span>
                  </div>
                  <SegmentedBar value={(drive.read/3500)*100} segments={15} color="#22C55E" height={6} />
                </div>
                <div>
                  <div className="flex justify-between text-[7px] mb-1" style={{ color: '#06B6D4', fontFamily: MONO }}>
                    <span>WRITE_SPD</span> <span>{drive.write.toFixed(0)} MB/s</span>
                  </div>
                  <SegmentedBar value={(drive.write/3500)*100} segments={15} color="#06B6D4" height={6} />
                </div>
              </div>
            </div>
          </WinFrame>
        ))}
      </div>
    </div>
  );
}
