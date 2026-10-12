'use client';

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { Drawer } from '@moc-healthy/ui';
import { ProtectedRoute } from '../ProtectedRoute';
import { Role } from '@moc-healthy/contracts';

export interface AdminShellProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: Role;
}

export const AdminShell: React.FC<AdminShellProps> = ({
  children,
  requiredPermission,
  requiredRole,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <ProtectedRoute requiredPermission={requiredPermission} requiredRole={requiredRole}>
      <div className="min-h-screen bg-slate-50 flex">
        {/* Desktop Fixed Sidebar */}
        <div className="hidden lg:block shrink-0 sticky top-0 h-screen z-40">
          <Sidebar />
        </div>

        {/* Mobile Slide-over Sidebar Drawer */}
        <Drawer
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          position="left"
          maxWidth="sm"
        >
          <div className="-m-6 h-full">
            <Sidebar onItemClick={() => setMobileMenuOpen(false)} />
          </div>
        </Drawer>

        {/* Main Content Viewport */}
        <div className="flex-1 flex flex-col min-w-0">
          <Topbar onToggleMobileMenu={() => setMobileMenuOpen(true)} />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
};
