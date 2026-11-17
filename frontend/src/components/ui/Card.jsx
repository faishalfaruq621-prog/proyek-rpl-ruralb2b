import * as React from 'react'

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-2xl shadow-rural border border-slate-100 overflow-hidden transition-all duration-200 hover:shadow-rural-lg ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`p-6 border-b border-slate-100 ${className}`}>{children}</div>
  )
}

// forwardRef: dipakai halaman chat untuk auto-scroll ke pesan terbaru.
export const CardBody = React.forwardRef(function CardBody({ children, className = '' }, ref) {
  return (
    <div ref={ref} className={`p-6 ${className}`}>{children}</div>
  )
})

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`p-6 border-t border-slate-100 bg-slate-50 ${className}`}>{children}</div>
  )
}

export default Card
