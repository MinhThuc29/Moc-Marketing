import type { Metadata } from 'next';
import './globals.css';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { MobileBottomNav } from '../components/layout/MobileBottomNav';
import { CartProvider } from '../context/CartContext';

export const metadata: Metadata = {
  title: 'Mộc Healthy — Trái Cây Tươi, Nước Ép & Đồ Uống Healthy',
  description:
    'Thương hiệu trái cây tuyển chọn cắt sẵn, nước ép 100% nguyên chất, sinh tố và đồ uống healthy tươi mới mỗi ngày. Giao nhanh trong 30 phút.',
  keywords: [
    'trái cây cắt sẵn',
    'nước ép nguyên chất',
    'sinh tố bơ',
    'sữa chua hoa quả',
    'mộc healthy',
    'đồ uống healthy',
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="scroll-smooth">
      <body className="antialiased min-h-screen flex flex-col bg-slate-50/60 text-slate-800">
        <CartProvider>
          <Header />
          <main className="flex-1 pb-16 md:pb-0">{children}</main>
          <Footer />
          <MobileBottomNav />
        </CartProvider>
      </body>
    </html>
  );
}
