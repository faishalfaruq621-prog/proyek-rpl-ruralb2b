import { Loader2 } from 'lucide-react'

export function Loading({ className = '' }) {
  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <Loader2 className="w-5 h-5 animate-spin text-rural-600" />
      <span className="text-sm text-slate-500">Memuat...</span>
    </div>
  )
}

export default Loading
