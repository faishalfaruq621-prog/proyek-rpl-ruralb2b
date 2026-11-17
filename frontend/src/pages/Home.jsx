import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Truck,
  ShieldCheck,
  Handshake,
  Leaf,
  Package,
  Store,
  Users,
  Search,
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { formatRupiah } from '../utils/format'

export default function Home() {
  const [search, setSearch] = useState('')

  const handleSearch = (e) => {
    e.preventDefault()
    if (search.trim()) {
      window.location.href = '/katalog?search=' + encodeURIComponent(search.trim())
    }
  }

  const stats = [
    { icon: Users, label: 'UMKM Terdaftar', value: '1.200+' },
    { icon: Package, label: 'Produk Unggulan', value: '3.400+' },
    { icon: ShieldCheck, label: 'Terverifikasi', value: '850+' },
    { icon: ArrowRight, label: 'Transaksi Bulanan', value: '12.000+' },
  ]

  const categories = [
    { name: 'Sayuran Segar', icon: Leaf, count: '450 produk', color: 'bg-rural-100 text-rural-700' },
    { name: 'Buah-Buahan', icon: Package, count: '320 produk', color: 'bg-amber-100 text-amber-700' },
    { name: 'Beras & Pangan', icon: Store, count: '280 produk', color: 'bg-blue-100 text-blue-700' },
    { name: 'Peternakan', icon: Users, count: '180 produk', color: 'bg-rose-100 text-rose-700' },
  ]

  const howItWorks = [
    {
      step: 1,
      title: 'Pilih Produk',
      desc: 'Jelajahi katalog hasil petani dan UMKM pedesaan, lalu pilih produk yang Anda butuhkan.',
    },
    {
      step: 2,
      title: 'Masukkan ke Keranjang',
      desc: 'Tambahkan produk ke keranjang dengan jumlah yang sesuai kebutuhan bisnis Anda.',
    },
    {
      step: 3,
      title: 'Checkout & Bayar',
      desc: 'Selesaikan pesanan dengan checkout dan upload bukti pembayaran untuk konfirmasi.',
    },
  ]

  const featuredProducts = [
    {
      id: 1,
      name: 'Segar Bunga Pepaya Organik',
      seller: 'Tani Makmur - Cibiru, Bandung',
      price: 15000,
      unit: 'kg',
      image:
        'https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=800&auto=format&fit=crop',
    },
    {
      id: 2,
      name: 'Buah Naga Merah Segar',
      seller: 'Naga Sari - Sleman, Yogyakarta',
      price: 35000,
      unit: 'kg',
      image:
        'https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=800&auto=format&fit=crop',
    },
    {
      id: 3,
      name: 'Beras Organik Cianjur',
      seller: 'Beras Jaya - Cianjur, Jawa Barat',
      price: 18000,
      unit: 'kg',
      image:
        'https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=800&auto=format&fit=crop',
    },
    {
      id: 4,
      name: 'Telur Ayam Kampung',
      seller: 'Ternak Sejahtera - Purwakarta',
      price: 28000,
      unit: 'kg',
      image:
        'https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=800&auto=format&fit=crop',
    },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-earth-50">
      {/* Hero */}
      <section className="relative bg-rural-900 text-white py-20 lg:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-30" />
        <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h1 className="font-display font-extrabold text-4xl md:text-6xl leading-tight mb-6">
              Marketplace B2B<br />
              untuk UMKM Pedesaan Indonesia
            </h1>
            <p className="text-rural-200 text-lg mb-8 max-w-lg">
              Menghubungkan petani, supplier, dan kolektor lokal dengan pembeli
              bisnis di seluruh Indonesia. Transparan, terpercaya, dan berkualitas.
            </p>
            <form onSubmit={handleSearch} className="relative mb-8 max-w-xl">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-rural-200 w-5 h-5">
                <Search />
              </div>
              <input
                type="text"
                placeholder="Cari produk, kategori, atau nama penjual..."
                className="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-white/20 bg-white/10 focus:border-rural-400 focus:ring-2 focus:ring-rural-400 outline-none text-white placeholder-white/60 transition-all"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <Button size="lg" variant="outline" className="absolute right-2 top-1/2 -translate-y-1/2 bg-white text-rural-900 hover:bg-rural-50">
                Cari
              </Button>
            </form>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button size="lg" asChild>
                <Link to="/katalog">Jelajahi Produk</Link>
              </Button>
              <Button variant="outline" size="lg" className="bg-white text-rural-900 hover:bg-rural-50" asChild>
                <Link to="/register">Daftar Menjadi Penjual</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Kategori Produk */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="font-display font-bold text-2xl md:text-3xl text-slate-900 mb-2">
              Kategori Produk
            </h2>
            <p className="text-slate-600">Pilih kategori yang Anda cari</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {categories.map((cat) => (
              <Link
                key={cat.name}
                to="/katalog"
                className="group flex flex-col items-center justify-center gap-3 p-6 rounded-2xl border border-slate-100 bg-white hover:bg-rural-50 hover:border-rural-200 transition-all cursor-pointer"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-rural-600 ${cat.color} shadow-sm group-hover:scale-110 transition-transform`}>
                  <cat.icon className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 text-sm">{cat.name}</h3>
                <p className="text-xs text-slate-500">{cat.count}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-rural-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((s) => (
              <Card key={s.label} className="p-8 text-center">
                <s.icon className="w-8 h-8 text-rural-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500 mb-2">{s.label}</p>
                <p className="font-display font-bold text-3xl text-slate-900">{s.value}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Cara Kerja */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="font-display font-bold text-2xl md:text-3xl text-slate-900 mb-2">
              Cara Kerja Marketplace
            </h2>
            <p className="text-slate-600">Transaksi B2B yang sederhana dan transparan</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {howItWorks.map((step) => (
              <Card key={step.step} className="p-8 text-center">
                <div className="w-12 h-12 rounded-xl bg-rural-100 flex items-center justify-center text-rural-600 font-bold text-xl mx-auto mb-6">
                  {step.step}
                </div>
                <h3 className="font-bold text-slate-900 mb-3">{step.title}</h3>
                <p className="text-slate-600 text-sm">{step.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Produk Unggulan */}
      <section className="py-16 bg-rural-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-end mb-10 gap-4">
            <div>
              <h2 className="font-display font-bold text-2xl md:text-3xl text-slate-900 mb-2">
                Produk Unggulan
              </h2>
              <p className="text-slate-600">Koleksi hasil terbaik dari mitra kami</p>
            </div>
            <Link
              to="/katalog"
              className="text-sm font-medium text-rural-600 flex items-center gap-1 hover:text-rural-700 transition-colors"
            >
              Lihat Semua <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((p) => (
              <Card
                key={p.id}
                className="cursor-pointer group hover:border-rural-200 transition-border"
                onClick={() => {
                  window.location.href = '/produk/' + p.id
                }}
              >
                <div className="h-48 bg-slate-100 flex items-center justify-center overflow-hidden group-hover:scale-105 transition-transform duration-200">
                  <img
                    src={p.image}
                    alt={p.name}
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100"
                  />
                </div>
                <div className="p-5">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-slate-900 text-base truncate">{p.name}</h3>
                    <Badge variant="success" className="text-xs">
                      Tersedia
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 truncate mb-3">{p.seller}</p>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="font-bold text-rural-600 text-xl">
                      {formatRupiah(p.price)}
                    </span>
                    <span className="text-sm text-slate-500">/{p.unit}</span>
                  </div>
                  <Button size="sm" variant="outline" className="w-full" onClick={() => {}}>
                    Pesan Sekarang
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Bergabung */}
      <section className="py-20 bg-rural-900 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-3xl bg-rural-800 p-10 md:p-16 flex flex-col md:flex-row items-center gap-8 border border-rural-700 overflow-hidden">
            <div className="md:w-1/2">
              <h2 className="font-display font-bold text-2xl md:text-3xl text-white mb-4">
                Bergabung dengan RuralB2B
              </h2>
              <p className="text-rural-200 mb-6">
                Jualkan hasil petani dan produk UMKM Anda ke pembeli bisnis di
                seluruh Indonesia dengan mudah dan terpercaya.
              </p>
              <div className="flex gap-3">
                <Button size="lg" asChild>
                  <Link to="/register">Daftar Gratis</Link>
                </Button>
                <Button variant="outline" size="lg" className="text-white border-rural-500 hover:bg-white hover:text-rural-900" asChild>
                  <Link to="/katalog">Jelajahi Produk</Link>
                </Button>
              </div>
            </div>
            <div className="md:w-1/2 hidden md:block">
              <div className="relative rounded-2xl overflow-hidden border border-rural-700">
                <img
                  src="https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=2070&auto=format&fit=crop"
                  alt="Komunitas petani"
                  className="w-full h-64 object-cover opacity-90"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
