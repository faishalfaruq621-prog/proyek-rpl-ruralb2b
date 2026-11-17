import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'

export function Button({ children, className = '', variant = 'primary', size = 'md', disabled, onClick, asChild, ...props }) {
  const base = "font-medium rounded-xl transition-colors duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:pointer-events-none"
  const variants = {
    primary: "bg-rural-600 hover:bg-rural-700 text-white",
    outline: "border border-slate-300 hover:border-rural-600 hover:bg-rural-50 text-slate-700 hover:text-rural-600",
    secondary: "bg-slate-100 hover:bg-slate-200 text-slate-800",
  }
  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg",
  }

  const Comp = asChild ? Slot : 'button'

  return (
    <Comp
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </Comp>
  )
}

export default Button
