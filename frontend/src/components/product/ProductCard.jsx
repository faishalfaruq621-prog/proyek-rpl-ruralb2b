import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { formatRupiah, PRODUCT_IMAGE_PLACEHOLDER } from '../../utils/format'
import { Link } from 'react-router-dom'

export function ProductCard({ product }) {
  return (
    <Card className="cursor-pointer group hover:border-rural-200" onClick={() => {
      window.location.href = '/produk/' + product.id
    }}>
      <div className="h-48 bg-slate-100 flex items-center justify-center overflow-hidden group-hover:scale-105 transition-transform duration-200 mb-4">
        <img
          src={product.images?.[0]?.url || PRODUCT_IMAGE_PLACEHOLDER}
          alt={product.product_name}
          className="w-full h-full object-cover opacity-90 group-hover:opacity-100"
          onError={(e) => { e.target.src = PRODUCT_IMAGE_PLACEHOLDER; }}
        />
      </div>
      <div className="p-4">
        <div className="flex justify-between items-start mb-1">
          <h3 className="font-bold text-slate-900 text-lg">{product.product_name}</h3>
          <Badge variant="success" className="text-xs">Tersedia</Badge>
        </div>
        <p className="text-sm text-slate-500 truncate mb-3">{product.description || '-'}</p>
        <div className="flex items-baseline gap-2">
          <span className="font-bold text-rural-600 text-xl">{formatRupiah(product.price)}</span>
          <span className="text-sm text-slate-500">/{product.unit || 'kg'}</span>
        </div>
        <div className="mt-4">
          <Button size="sm" className="w-full" variant="outline">
            Lihat Detail
          </Button>
        </div>
      </div>
    </Card>
  )
}

function Button({ children, className = '', variant = 'outline', size = 'sm', ...props }) {
  const base = "font-medium rounded-xl transition-colors duration-200 flex items-center justify-center gap-2"
  const variants = {
    primary: "bg-rural-600 hover:bg-rural-700 text-white",
    outline: "border border-slate-300 hover:border-rural-600 hover:bg-rural-50 text-slate-700 hover:text-rural-600",
  }
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-6 py-3 text-base",
  }
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}

export default ProductCard
