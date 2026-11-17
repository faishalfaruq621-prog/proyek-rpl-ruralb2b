import { Link } from 'react-router-dom'
import { Home, ArrowRight } from 'lucide-react'
import { Card } from '../components/ui/Card'
import { CardHeader } from '../components/ui/Card'
import { CardBody } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-earth-50 px-4">
      <Card className="w-full max-w-md shadow-rural-lg text-center">
        <CardHeader className="p-10">
          <div className="w-16 h-16 rounded-full bg-rural-100 flex items-center justify-center text-rural-600 mx-auto mb-4">
            <Home className="w-8 h-8" />
          </div>
          <h1 className="font-display font-bold text-2xl text-slate-900">Halaman Tidak Ditemukan</h1>
          <p className="text-slate-600 mt-2">Halaman yang Anda cari tidak ada.</p>
        </CardHeader>
        <CardBody className="p-6">
          <Button asChild size="sm" className="w-full bg-rural-600 hover:bg-rural-700 text-white">
            <Link to="/" className="flex items-center justify-center gap-2">
              <ArrowRight className="w-4 h-4" /> Kembali ke Beranda
            </Link>
          </Button>
        </CardBody>
      </Card>
    </div>
  )
}
