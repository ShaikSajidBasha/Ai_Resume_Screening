const config = {
  HIGH: { label: 'High priority', className: 'bg-danger/10 text-danger border-danger/30' },
  MEDIUM: { label: 'Medium priority', className: 'bg-signal/10 text-signal-dark border-signal/30' },
  LOW: { label: 'Low priority', className: 'bg-teal-light text-teal border-teal/30' },
}

export default function PriorityTag({ priority = 'MEDIUM' }) {
  const c = config[priority] || config.MEDIUM
  return (
    <span className={`inline-block px-2.5 py-1 rounded-sm text-xs border ${c.className}`}>
      {c.label}
    </span>
  )
}
