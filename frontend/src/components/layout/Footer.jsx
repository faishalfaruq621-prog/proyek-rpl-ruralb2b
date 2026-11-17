export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white mt-auto">
      <div className="container px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-8 mb-10">
          <div className="col-span-2 lg:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-lg bg-rural-600 flex items-center justify-center text-white font-bold text-sm">
                R
              </div>
              <span className="font-display font-bold text-slate-900">RuralB2B</span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed mb-4">
              Marketplace B2B untuk UMKM Pedesaan Indonesia. Terhubung dengan
              petani, supplier, dan kolektor lokal di seluruh Nusantara.
            </p>
            <div className="flex gap-3">
              <a href="#" className="w-8 h-8 rounded-xl bg-rural-50 flex items-center justify-center text-rural-600 hover:bg-rural-100 transition-colors">
                <span className="w-4 h-4">f</span>
              </a>
              <a href="#" className="w-8 h-8 rounded-xl bg-rural-50 flex items-center justify-center text-rural-600 hover:bg-rural-100 transition-colors">
                <span className="w-4 h-4">ig</span>
              </a>
              <a href="#" className="w-8 h-8 rounded-xl bg-rural-50 flex items-center justify-center text-rural-600 hover:bg-rural-100 transition-colors">
                <span className="w-4 h-4">t</span>
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-bold text-slate-900 mb-4">Produk</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="/katalog" className="hover:text-rural-600 transition-colors">Semua Produk</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Produk Unggulan</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Kategori</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Promo</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-slate-900 mb-4">Pembeli</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="/keranjang" className="hover:text-rural-600 transition-colors">Keranjang Saya</a></li>
              <li><a href="/pesanan" className="hover:text-rural-600 transition-colors">Pesanan Saya</a></li>
              <li><a href="/checkout" className="hover:text-rural-600 transition-colors">Checkout</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Pembayaran</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-slate-900 mb-4">Perusahaan</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-rural-600 transition-colors">Tentang Kami</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Karir</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Kontak</a></li>
              <li><a href="#" className="hover:text-rural-600 transition-colors">Pusat Bantuan</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm">
            <p className="text-slate-500">
              &copy; {new Date().getFullYear()} RuralB2B. Hak cipta dilindungi.
            </p>
            <div className="flex gap-4 text-slate-500">
              <a href="#" className="hover:text-rural-600 transition-colors">Kebijakan Privasi</a>
              <a href="#" className="hover:text-rural-600 transition-colors">Syarat &amp; Ketentuan</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
