'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCart } from '../../context/CartContext';

export const MobileBottomNav: React.FC = () => {
  const pathname = usePathname();
  const { itemCount } = useCart();

  const navItems = [
    { label: 'Trang chủ', href: '/', icon: '🏠' },
    { label: 'Thực đơn', href: '/search', icon: '🥑' },
    { label: 'Khuyến mãi', href: '/promotions', icon: '🏷️' },
    { label: 'Giỏ hàng', href: '/cart', icon: '🛒', badge: itemCount > 0 ? String(itemCount) : undefined },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-slate-200/80 px-2 py-1 shadow-lg">
      <div className="grid grid-cols-4 items-center">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center py-1.5 transition-colors relative ${
                isActive ? 'text-emerald-700 font-bold' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <span className="text-lg relative">
                {item.icon}
                {item.badge && (
                  <span className="absolute -top-1 -right-2 bg-emerald-600 text-white rounded-full min-w-3.5 h-3.5 px-0.5 text-[9px] font-extrabold flex items-center justify-center">
                    {item.badge}
                  </span>
                )}
              </span>
              <span className="text-[10px] mt-0.5 tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
