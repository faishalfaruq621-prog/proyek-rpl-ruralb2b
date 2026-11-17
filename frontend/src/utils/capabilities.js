/**
 * Model kemampuan pengguna (capability) — satu titik sambung untuk
 * pemisahan menu Buyer dan Seller.
 *
 * Dasar identifikasi (dari data aktual, bukan nama/email/tebakan):
 * - `user.role` dari tabel users (business_user / admin).
 * - `user.business_profile` dari tabel business_profiles: keberadaan profil
 *   bisnis adalah prasyarat menyewakan produk (endpoint seller dan
 *   produk/verifikasi semuanya berbasis business_profiles).
 *
 * DEFAULT AKUN GANDA: setiap business_user dapat membeli dari bisnis lain
 * sekaligus menjual produknya sendiri (didukung aturan backend
 * `ensure_not_self_purchase`). Jika nanti aplikasi menambahkan kolom
 * kapabilitas di database (mis. `can_buy` / `can_sell`), cukup set nilai
 * tersebut pada payload `/auth/me` dan helper ini otomatis menghormati
 * nilai `false`.
 */

export function getCapabilities(user) {
  if (!user) {
    return { canBuy: false, canSell: false, isAdmin: false }
  }

  const caps = user.capabilities || user.business_profile?.capabilities || {}
  const isAdmin = user.role === 'admin'
  const hasProfile = !!user.business_profile

  return {
    // Pembelian hanya untuk pemilik profil bisnis (business_user) — selaras
    // dengan backend: endpoint cart/checkout/pesanan memakai
    // @business_user_required yang MENOLAK admin (403), jadi admin tidak
    // boleh melihat menu Pembelian.
    canBuy: hasProfile && caps.can_buy !== false,
    // Penjualan membutuhkan profil bisnis (tabel business_profiles).
    canSell: hasProfile && caps.can_sell !== false,
    isAdmin,
    isBuyer: hasProfile && caps.can_buy !== false,
    isSeller: hasProfile && caps.can_sell !== false,
  }
}

export default getCapabilities
