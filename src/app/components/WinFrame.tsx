import { ReactNode } from 'react';

const MONO = "'Share Tech Mono', monospace";

interface WinFrameProps {
  title: string;
  accentColor: string;
  badge?: string;
  badgeColor?: string;
  children: ReactNode;
  className?: string;
  pid?: string;
}

export function WinFrame({ title, accentColor, badge, badgeColor, children, className = '', pid }: WinFrameProps) {
  return (
    <div className={`relative bg-[#0D0D0D] border border-[#1A1A1A] overflow-hidden ${className}`} style={{ borderRadius: 0 }}>
      {/* Title Bar */}
      <div className="h-6 border-b flex items-center justify-between px-2" style={{ borderColor: accentColor, backgroundColor: '#0A0A0A' }}>
        <div className="flex items-center gap-2">
          {/* Status Dots */}
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-[#22C55E]" style={{ borderRadius: 0, boxShadow: '0 0 4px #22C55E' }} />
            <div className="w-2 h-2 bg-[#444]" style={{ borderRadius: 0 }} />
            <div className="w-2 h-2 bg-[#444]" style={{ borderRadius: 0 }} />
          </div>
          {/* Title */}
          <span style={{ fontFamily: MONO, fontSize: '10px', color: accentColor, textShadow: `0 0 8px ${accentColor}` }}>
            {title}
          </span>
          {/* Badge */}
          {badge && (
            <span className="px-1 border" style={{ 
              fontFamily: MONO, 
              fontSize: '8px', 
              color: badgeColor || accentColor,
              borderColor: badgeColor || accentColor,
              borderRadius: 0
            }}>
              {badge}
            </span>
          )}
        </div>
        {/* PID */}
        {pid && (
          <span style={{ fontFamily: MONO, fontSize: '8px', color: '#333' }}>
            PID:{pid}
          </span>
        )}
      </div>

      {/* Content Area */}
      <div className="relative" style={{ minHeight: 0 }}>
        {children}
      </div>

      {/* Scanline Overlay */}
      <div 
        className="absolute inset-0 pointer-events-none" 
        style={{ 
          top: '24px',
          background: 'repeating-linear-gradient(0deg, transparent 0px, transparent 1px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 2px)',
          zIndex: 10
        }} 
      />
    </div>
  );
}
