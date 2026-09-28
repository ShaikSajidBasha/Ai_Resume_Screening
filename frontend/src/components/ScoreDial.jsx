/**
 * Circular score gauge — the visual centerpiece of the Results page.
 * Pure SVG, no external chart library needed for this one.
 */
export default function ScoreDial({ score = 0, label, size = 148, accent = '#0E7C7B' }) {
  const stroke = 10
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, score))
  const offset = circumference * (1 - clamped / 100)

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="#E7E2D6" strokeWidth={stroke}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={accent} strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-3xl font-medium text-ink tabular-nums">{Math.round(clamped)}</span>
          <span className="text-xs text-slate-650">/ 100</span>
        </div>
      </div>
      {label && <span className="mt-3 text-sm text-slate-650 text-center">{label}</span>}
    </div>
  )
}
