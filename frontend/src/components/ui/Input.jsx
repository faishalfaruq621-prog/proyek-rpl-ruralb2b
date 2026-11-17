export function Input({ className = '', ...props }) {
  return (
    <input
      className={`w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-rural-500 focus:border-rural-500 outline-none transition-all duration-200 bg-white text-slate-900 placeholder-slate-400 ${className}`}
      {...props}
    />
  )
}

export default Input
