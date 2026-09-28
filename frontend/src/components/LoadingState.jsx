export default function LoadingState({ message = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-ink/15 border-t-teal rounded-full animate-spin" />
        <p className="text-slate-650 text-sm">{message}</p>
      </div>
    </div>
  )
}
