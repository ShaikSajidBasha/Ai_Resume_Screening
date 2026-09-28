import { useEffect } from 'react'
import { CheckCircle2, AlertCircle, X } from 'lucide-react'

export default function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [toast, onClose])

  if (!toast) return null
  const isError = toast.type === 'error'

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-[fadeIn_0.2s_ease]">
      <div className={`flex items-center gap-3 px-4 py-3 rounded-md shadow-lg border ${
        isError ? 'bg-[#3A1F19] border-danger/40 text-[#F7E9E3]' : 'bg-ink-800 border-teal/40 text-paper'
      }`}>
        {isError ? <AlertCircle size={18} className="text-danger shrink-0" /> : <CheckCircle2 size={18} className="text-teal shrink-0" />}
        <span className="text-sm">{toast.message}</span>
        <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100">
          <X size={16} />
        </button>
      </div>
    </div>
  )
}
