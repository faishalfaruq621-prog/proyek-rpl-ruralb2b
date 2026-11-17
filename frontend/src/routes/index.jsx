import { Routes, Route } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import Home from '../pages/Home'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Catalog from '../pages/Catalog'
import ProductDetail from '../pages/ProductDetail'
import Cart from '../pages/Cart'
import Checkout from '../pages/Checkout'
import Orders from '../pages/Orders'
import OrderDetail from '../pages/OrderDetail'
import BusinessProfile from '../pages/BusinessProfile'
import Dashboard from '../pages/Dashboard'
import NotFound from '../pages/NotFound'
import Verifikasi from '../pages/Verifikasi'
import ProdukTambah from '../pages/ProdukTambah'
import ProdukKelola from '../pages/ProdukKelola'
import ProdukEdit from '../pages/ProdukEdit'
import VerifikasiAdmin from '../pages/VerifikasiAdmin'
import DetailVerifikasiAdmin from '../pages/DetailVerifikasiAdmin'
import SellerOrders from '../pages/SellerOrders'
import SellerOrderDetail from '../pages/SellerOrderDetail'
import ChatList from '../pages/ChatList'
import ChatThread from '../pages/ChatThread'
import AccountSettings from '../pages/AccountSettings'
import Notifikasi from '../pages/Notifikasi'
import AdminDashboard from '../pages/AdminDashboard'
import AdminUsers from '../pages/AdminUsers'
import AdminCategories from '../pages/AdminCategories'
import AdminOrders from '../pages/AdminOrders'
import AIChatStandard from '../pages/AIChatStandard'
import AIChatPlus from '../pages/AIChatPlus'
import AIProductRecommendation from '../pages/AIProductRecommendation'
import AIBusinessInsights from '../pages/AIBusinessInsights'

/**
 * Pembagian kemampuan:
 * - capability="canBuy": halaman alur pembelian (keranjang, checkout,
 *   pesanan milik buyer, rekomendasi produk).
 * - capability="canSell": halaman alur penjualan (kelola produk, pesanan
 *   masuk, insight bisnis).
 * Halaman admin dilindungi roles=['admin'] dan di backend oleh
 * @admin_required (role != admin -> 403).
 */
export function AppRoutes() {
  return (
    <Routes>
      {/* Public pages without layout */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Pages with layout (navbar + footer) */}
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/katalog" element={<Catalog />} />

        {/* Seller: produk */}
        <Route
          path="/produk/tambah"
          element={
            <ProtectedRoute capability="canSell">
              <ProdukTambah />
            </ProtectedRoute>
          }
        />
        <Route
          path="/produk/kelola"
          element={
            <ProtectedRoute capability="canSell">
              <ProdukKelola />
            </ProtectedRoute>
          }
        />
        <Route
          path="/produk/edit/:id"
          element={
            <ProtectedRoute capability="canSell">
              <ProdukEdit />
            </ProtectedRoute>
          }
        />
        <Route
          path="/verifikasi"
          element={
            <ProtectedRoute capability="canSell">
              <Verifikasi />
            </ProtectedRoute>
          }
        />

        {/* Seller: pesanan masuk dan riwayat penjualan */}
        <Route
          path="/seller/pesanan"
          element={
            <ProtectedRoute capability="canSell">
              <SellerOrders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/seller/pesanan/:id"
          element={
            <ProtectedRoute capability="canSell">
              <SellerOrderDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai/insights"
          element={
            <ProtectedRoute capability="canSell">
              <AIBusinessInsights />
            </ProtectedRoute>
          }
        />

        {/* Buyer: alur pembelian */}
        <Route
          path="/keranjang"
          element={
            <ProtectedRoute capability="canBuy">
              <Cart />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout"
          element={
            <ProtectedRoute capability="canBuy">
              <Checkout />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pesanan"
          element={
            <ProtectedRoute capability="canBuy">
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pesanan/:id"
          element={
            <ProtectedRoute capability="canBuy">
              <OrderDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai/recommendations"
          element={
            <ProtectedRoute capability="canBuy">
              <AIProductRecommendation />
            </ProtectedRoute>
          }
        />

        {/* Bersama */}
        <Route path="/produk/:id" element={<ProductDetail />} />
        <Route
          path="/profil-bisnis"
          element={
            <ProtectedRoute>
              <BusinessProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai/chat"
          element={
            <ProtectedRoute>
              <AIChatStandard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai/chat/plus"
          element={
            <ProtectedRoute>
              <AIChatPlus />
            </ProtectedRoute>
          }
        />

        {/* Chat: semua akun login (buyer & seller) */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/:id"
          element={
            <ProtectedRoute>
              <ChatThread />
            </ProtectedRoute>
          }
        />

        {/* Pengaturan akun & notifikasi: semua akun login */}
        <Route
          path="/pengaturan-akun"
          element={
            <ProtectedRoute>
              <AccountSettings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/notifikasi"
          element={
            <ProtectedRoute>
              <Notifikasi />
            </ProtectedRoute>
          }
        />

        {/* Admin: digate roles=['admin'] di frontend dan @admin_required
            di backend. */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/pengguna"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminUsers />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/kategori"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminCategories />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/transaksi"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminOrders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/verifikasi/admin"
          element={
            <ProtectedRoute roles={['admin']}>
              <VerifikasiAdmin />
            </ProtectedRoute>
          }
        />
        <Route
          path="/verifikasi/admin/:id"
          element={
            <ProtectedRoute roles={['admin']}>
              <DetailVerifikasiAdmin />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default AppRoutes
