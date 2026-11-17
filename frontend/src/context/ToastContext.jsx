import { createContext, useContext, useState, useEffect } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = (toast) => {
    const id = Date.now() + Math.random()
    setToasts((prev) => [...prev, { ...toast, id }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }

  const success = (message) => addToast({ type: 'success', message })
  const error = (message) => addToast({ type: 'error', message })
  const info = (message) => addToast({ type: 'info', message })

  const value = { toasts, success, error, info, addToast, setToasts }

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto px-4 py-3 rounded-xl shadow-lg flex items-center gap-3 min-w-[300px] animate-in slide-in-from-top-4 duration-300"
            style={{
              backgroundColor:
                t.type === 'success'
                  ? '#dcfce7'
                  : t.type === 'error'
                  ? '#fee2e2'
                  : '#dbeafe',
              color:
                t.type === 'success'
                  ? '#14532d'
                  : t.type === 'error'
                  ? '#991b1b'
                  : '#1e3a8a',
            }}
          >
            <span className="font-medium">{t.message}</span>
            <button
              onClick={() =>
                setToasts((prev) => prev.filter((x) => x.id !== t.id))
              }
              className="ml-auto text-sm opacity-70 hover:opacity-100"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export default ToastContext
