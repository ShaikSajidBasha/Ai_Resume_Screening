export default function SkillBadge({ children, variant = 'match' }) {
  const styles = {
    match: 'bg-teal-light text-teal border border-teal/30',
    missing: 'bg-[#F7E9E3] text-danger border border-danger/25',
    neutral: 'bg-[#EDEAE1] text-slate-650 border border-[#DCD6C8]',
  }
  return (
    <span className={`inline-block px-3 py-1 rounded-sm text-sm ${styles[variant]}`}>
      {children}
    </span>
  )
}
