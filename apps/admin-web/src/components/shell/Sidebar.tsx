'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { Badge } from '@moc-healthy/ui';

interface NavItem {
  name: string;
  href: string;
  icon: string;
  permission?: string;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: '01 Dashboard', href: '/', icon: '📊' },
  { name: '02 Products', href: '/products', icon: '🥑', permission: 'product.read' },
  { name: '02.1 Kho & HSD', href: '/inventory', icon: '📦', permission: 'inventory.read' },
  { name: '02.2 Khuyến Mãi', href: '/promotions', icon: '🏷️', permission: 'campaign.create' },
  { name: '03 Orders', href: '/orders', icon: '🧾', permission: 'order.read' },
  { name: '04 Customers', href: '/customers', icon: '👥', permission: 'customer.read' },
  { name: '05 Marketing', href: '/marketing', icon: '🎯', permission: 'campaign.create' },
  { name: '06 AI Studio', href: '/ai-studio', icon: '✨', permission: 'content.create', badge: 'AI' },
  { name: '07 Content', href: '/content', icon: '📝', permission: 'content.create' },
  { name: '08 Analytics', href: '/analytics', icon: '📈', permission: 'analytics.read' },
  { name: '09 Automation', href: '/automation', icon: '⚡', permission: 'settings.manage' },
  { name: '10 Settings', href: '/settings', icon: '⚙️', permission: 'settings.manage' },
];

export const Sidebar: React.FC<{ onItemClick?: () => void }> = ({ onItemClick }) => {
  const pathname = usePathname();
  const { hasPermission } = useAuth();

  const allowedItems = NAV_ITEMS.filter((item) => {
    if (!item.permission) return true;
    return hasPermission(item.permission);
  });

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center space-x-3 border-b border-slate-800 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-extrabold text-base shadow-sm">
          M
        </div>
        <div>
          <span className="font-bold text-white text-sm tracking-tight block">Mộc Healthy</span>
          <span className="text-[10px] text-emerald-400 font-medium uppercase tracking-wider block">
            AI Marketing Hub
          </span>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Chức năng Quản trị
        </div>
        {allowedItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onItemClick}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                isActive
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span className="text-sm">{item.icon}</span>
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.2 text-[9px] font-bold bg-emerald-500/30 text-emerald-300 rounded border border-emerald-500/40">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Footer info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between shrink-0">
        <span>v0.1.0 • Omnichannel</span>
        <span className="w-2 h-2 rounded-full bg-emerald-500" title="System Online" />
      </div>
    </aside>
  );
};
