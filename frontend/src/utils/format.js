const ID_LOCALE = {
  short: {
    MMM: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des'],
  },
}

// Gambar placeholder untuk produk tanpa foto (dipakai komponen kartu/detail).
// SVG data-URI lokal: tanpa dependensi CDN eksternal, selalu tampil.
// Jangan memanggil endpoint /images/:id ketika produk tidak memiliki gambar —
// endpoint hanya menyajikan gambar nyata yang terdaftar di product_images.
export const PRODUCT_IMAGE_PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%23eaf4ee'/%3E%3Cpath d='M200 62 L266 100 V176 L200 214 L134 176 V100 Z' fill='%23bbf7d0'/%3E%3Cpath d='M134 100 L200 138 L266 100 M200 138 V214' stroke='%2316a34a' stroke-width='6' fill='none'/%3E%3C/svg%3E"

export function formatRupiah(amount) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(amount || 0)
}

export function formatDate(dateString) {
  if (!dateString) return '-'
  const d = new Date(dateString)
  if (isNaN(d.getTime())) return '-'
  const month = ID_LOCALE.short.MMM[d.getMonth()]
  return `${d.getDate()} ${month} ${d.getFullYear()}`
}

export function truncate(text, length = 100) {
  if (!text) return ''
  return text.length > length ? `${text.slice(0, length)}...` : text
}
