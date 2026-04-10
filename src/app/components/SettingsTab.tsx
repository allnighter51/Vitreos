import { useState } from 'react';
import { WinFrame } from './WinFrame';
import { SegmentedBar } from './SegmentedBar';

const MONO = "'Share Tech Mono', monospace";
const VT = "'VT323', monospace";

type Theme = 'CYBER_PURPLE' | 'NEON_CYAN' | 'TOXIC_GREEN';

const THEME_COLORS = {
  CYBER_PURPLE: '#A855F7',
  NEON_CYAN: '#06B6D4',
  TOXIC_GREEN: '#39FF14'
};

export function SettingsTab() {
  const [pollingRate, setPollingRate] = useState(1500);
  const [activeTheme, setActiveTheme] = useState<Theme>('CYBER_PURPLE');
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleReset = () => {
    if (!showResetConfirm) {
      setShowResetConfirm(true);
      setTimeout(() => setShowResetConfirm(false), 3000);
    } else {
      setPollingRate(1500);
      setActiveTheme('CYBER_PURPLE');
      setShowResetConfirm(false);
      alert('SYSTEM SETTINGS RESET TO FACTORY DEFAULTS');
    }
  };

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* 1. Performance Tuning */}
      <WinFrame title="PERFORMANCE_TUNING // POLLING_ENGINE" accentColor="#A855F7" badge="REALTIME">
        <div className="p-4 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span style={{ fontFamily: MONO, fontSize: '10px', color: '#888', letterSpacing: '0.1em' }}>
              POLLING_RATE
            </span>
            <span style={{ fontFamily: VT, fontSize: '28px', color: '#A855F7', textShadow: '0 0 10px #A855F7' }}>
              {pollingRate}ms
            </span>
          </div>

          {/* Custom Slider */}
          <div className="relative">
            <input
              type="range"
              min="100"
              max="5000"
              step="100"
              value={pollingRate}
              onChange={(e) => setPollingRate(Number(e.target.value))}
              className="w-full h-2 bg-[#1A1A1A] appearance-none cursor-pointer"
              style={{
                borderRadius: 0,
                outline: 'none'
              }}
            />
            <div 
              className="absolute top-0 left-0 h-2 pointer-events-none"
              style={{
                width: `${((pollingRate - 100) / 4900) * 100}%`,
                background: '#A855F7',
                boxShadow: '0 0 8px #A855F744'
              }}
            />
            <div className="flex justify-between mt-1">
              <span style={{ fontFamily: MONO, fontSize: '7px', color: '#333' }}>100ms (HIGH_FREQ)</span>
              <span style={{ fontFamily: MONO, fontSize: '7px', color: '#333' }}>5000ms (LOW_FREQ)</span>
            </div>
          </div>

          <SegmentedBar value={(pollingRate / 5000) * 100} segments={30} color="#A855F7" height={8} />
        </div>
      </WinFrame>

      <div className="grid grid-cols-2 gap-2 flex-1">
        {/* 2. Theme Selector */}
        <WinFrame title="AESTHETIC_CONTROL // THEME_ENGINE" accentColor="#06B6D4">
          <div className="p-3 flex flex-col gap-3 h-full">
            <span style={{ fontFamily: MONO, fontSize: '8px', color: '#444', letterSpacing: '0.1em' }}>
              PRIMARY_ACCENT_COLOR
            </span>
            
            <div className="flex flex-col gap-2 flex-1">
              {(Object.keys(THEME_COLORS) as Theme[]).map(theme => {
                const isActive = activeTheme === theme;
                const color = THEME_COLORS[theme];
                
                return (
                  <button
                    key={theme}
                    onClick={() => setActiveTheme(theme)}
                    className="flex items-center gap-3 p-2 border transition-all"
                    style={{
                      borderColor: isActive ? color : '#2A2A2A',
                      background: isActive ? `${color}11` : 'transparent',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{
                      width: 24,
                      height: 24,
                      background: color,
                      boxShadow: isActive ? `0 0 12px ${color}` : 'none'
                    }} />
                    <span style={{
                      fontFamily: MONO,
                      fontSize: '9px',
                      color: isActive ? color : '#444',
                      letterSpacing: '0.1em',
                      textShadow: isActive ? `0 0 8px ${color}` : 'none'
                    }}>
                      {theme}
                    </span>
                    {isActive && (
                      <span style={{ marginLeft: 'auto', color, fontSize: '10px' }}>✓</span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-auto pt-3 border-t border-[#1A1A1A]">
              <div className="flex items-center gap-2 p-2 bg-[#0A0A0A]">
                <div style={{
                  width: 32,
                  height: 32,
                  background: THEME_COLORS[activeTheme],
                  boxShadow: `0 0 16px ${THEME_COLORS[activeTheme]}44`
                }} />
                <div className="flex flex-col">
                  <span style={{ fontFamily: MONO, fontSize: '7px', color: '#333' }}>PREVIEW</span>
                  <span style={{ fontFamily: MONO, fontSize: '9px', color: THEME_COLORS[activeTheme] }}>
                    {THEME_COLORS[activeTheme]}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </WinFrame>

        {/* 3. System Controls */}
        <WinFrame title="SYSTEM_CONTROLS // DANGER_ZONE" accentColor="#FF4444">
          <div className="p-3 flex flex-col justify-center items-center h-full gap-4">
            <div className="text-center">
              <span style={{ fontFamily: MONO, fontSize: '8px', color: '#FF4444', letterSpacing: '0.15em' }}>
                ⚠ CAUTION ⚠
              </span>
              <p style={{ fontFamily: MONO, fontSize: '7px', color: '#666', marginTop: '8px', lineHeight: '1.4' }}>
                Resetting system settings will restore all configurations to factory defaults.
                This action cannot be undone.
              </p>
            </div>

            <button
              onClick={handleReset}
              style={{
                background: 'repeating-linear-gradient(45deg, #000, #000 4px, rgba(255,107,0,0.2) 4px, rgba(255,107,0,0.2) 8px)',
                border: '2px solid #FF6B00',
                color: showResetConfirm ? '#FF4444' : '#FF6B00',
                fontFamily: MONO,
                fontSize: '11px',
                padding: '12px 24px',
                letterSpacing: '0.15em',
                textShadow: showResetConfirm ? '0 0 10px #FF4444' : '0 0 10px #FF6B00',
                boxShadow: showResetConfirm ? '0 0 16px #FF444444' : '0 0 12px #FF6B0044',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%',
                maxWidth: '240px'
              }}
            >
              {showResetConfirm ? '⚠ CONFIRM RESET ⚠' : 'RESET SYSTEM'}
            </button>

            {showResetConfirm && (
              <span style={{ fontFamily: MONO, fontSize: '7px', color: '#FF4444', letterSpacing: '0.1em' }}>
                CLICK AGAIN TO CONFIRM
              </span>
            )}
          </div>
        </WinFrame>
      </div>
    </div>
  );
}
