interface SegmentedBarProps {
  value: number;
  segments?: number;
  color?: string;
  height?: number;
  vertical?: boolean;
}

export function SegmentedBar({ value, segments = 20, color = '#22C55E', height = 8, vertical = false }: SegmentedBarProps) {
  const activeSegments = Math.floor((value / 100) * segments);
  const isHot = value >= 80;
  const finalColor = isHot ? '#FF6B00' : color;

  if (vertical) {
    return (
      <div className="flex flex-col-reverse gap-[2px]" style={{ height: '100%' }}>
        {Array.from({ length: segments }).map((_, i) => {
          const isActive = i < activeSegments;
          return (
            <div
              key={i}
              className="flex-1"
              style={{
                backgroundColor: isActive ? finalColor : '#1A1A1A',
                boxShadow: isActive ? `0 0 6px ${finalColor}44` : 'none',
                borderRadius: 0,
              }}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div className="flex gap-[2px]" style={{ height: `${height}px` }}>
      {Array.from({ length: segments }).map((_, i) => {
        const isActive = i < activeSegments;
        return (
          <div
            key={i}
            className="flex-1"
            style={{
              backgroundColor: isActive ? finalColor : '#1A1A1A',
              boxShadow: isActive ? `0 0 6px ${finalColor}44` : 'none',
              borderRadius: 0,
            }}
          />
        );
      })}
    </div>
  );
}
