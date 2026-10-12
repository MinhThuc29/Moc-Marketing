'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CartResponse, CartItem } from '@moc-healthy/contracts';
import { cartApi } from '../lib/api';
import { analytics } from '../lib/analytics';

interface CartContextType {
  cart: CartResponse | null;
  cartToken: string;
  itemCount: number;
  isLoading: boolean;
  addItem: (productId: string, quantity?: number, note?: string) => Promise<boolean>;
  updateQuantity: (itemId: string, quantity: number, note?: string) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<boolean>;
  applyCoupon: (code: string) => Promise<{ success: boolean; message: string }>;
  removeCoupon: () => Promise<boolean>;
  clearCart: () => Promise<boolean>;
  refreshCart: () => Promise<void>;
  toastMessage: string | null;
  clearToast: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

function getOrCreateCartToken(): string {
  if (typeof window === 'undefined') return '';
  let token = localStorage.getItem('moc_cart_token');
  if (!token) {
    token = `cart_${Math.random().toString(36).substring(2, 12)}_${Date.now()}`;
    localStorage.setItem('moc_cart_token', token);
  }
  return token;
}

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cartToken, setCartToken] = useState<string>('');
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const clearToast = useCallback(() => setToastMessage(null), []);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((prev) => (prev === msg ? null : prev));
    }, 3000);
  }, []);

  const refreshCart = useCallback(async () => {
    if (!cartToken) return;
    try {
      setIsLoading(true);
      const data = await cartApi.getCart(cartToken);
      setCart(data);
    } catch (err) {
      console.error('Failed to load cart:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cartToken]);

  // Initialize cart token on client mount
  useEffect(() => {
    const token = getOrCreateCartToken();
    setCartToken(token);
  }, []);

  // Fetch cart once token is available
  useEffect(() => {
    if (cartToken) {
      refreshCart();
    }
  }, [cartToken, refreshCart]);

  const addItem = async (productId: string, quantity: number = 1, note?: string): Promise<boolean> => {
    if (!cartToken) return false;
    try {
      setIsLoading(true);
      const updatedCart = await cartApi.addItem(cartToken, {
        product_id: productId,
        quantity,
        note,
      });
      setCart(updatedCart);

      const addedItem = updatedCart.items.find((i) => i.product_id === productId);
      if (addedItem) {
        analytics.trackAddToCart({
          productId: addedItem.product_id,
          name: addedItem.product_name,
          price: addedItem.unit_price,
          quantity,
        });
        showToast(`Đã thêm "${addedItem.product_name}" vào giỏ hàng!`);
      } else {
        showToast('Đã thêm sản phẩm vào giỏ hàng!');
      }
      return true;
    } catch (err: any) {
      showToast(err.message || 'Không thể thêm vào giỏ hàng');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number, note?: string): Promise<boolean> => {
    if (!cartToken) return false;
    try {
      setIsLoading(true);
      const updatedCart = await cartApi.updateItem(cartToken, itemId, {
        quantity,
        note,
      });
      setCart(updatedCart);
      return true;
    } catch (err: any) {
      showToast(err.message || 'Không thể cập nhật số lượng');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const removeItem = async (itemId: string): Promise<boolean> => {
    if (!cartToken) return false;
    try {
      setIsLoading(true);
      const targetItem = cart?.items.find((i) => i.id === itemId);
      const updatedCart = await cartApi.removeItem(cartToken, itemId);
      setCart(updatedCart);
      if (targetItem) {
        analytics.trackRemoveFromCart({
          productId: targetItem.product_id,
          name: targetItem.product_name,
        });
        showToast(`Đã xóa "${targetItem.product_name}" khỏi giỏ hàng.`);
      }
      return true;
    } catch (err: any) {
      showToast(err.message || 'Không thể xóa sản phẩm');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const applyCoupon = async (code: string): Promise<{ success: boolean; message: string }> => {
    if (!cartToken) return { success: false, message: 'Chưa có giỏ hàng' };
    try {
      setIsLoading(true);
      const updatedCart = await cartApi.applyCoupon(cartToken, code);
      setCart(updatedCart);
      analytics.trackApplyCoupon({
        code,
        discount: updatedCart.discount_amount,
        success: true,
      });
      const msg = updatedCart.promo_message || `Áp dụng mã ${code.toUpperCase()} thành công!`;
      showToast(msg);
      return { success: true, message: msg };
    } catch (err: any) {
      const errMsg = err.message || 'Mã ưu đãi không hợp lệ';
      analytics.trackApplyCoupon({
        code,
        discount: 0,
        success: false,
      });
      showToast(errMsg);
      return { success: false, message: errMsg };
    } finally {
      setIsLoading(false);
    }
  };

  const removeCoupon = async (): Promise<boolean> => {
    if (!cartToken) return false;
    try {
      setIsLoading(true);
      const updatedCart = await cartApi.removeCoupon(cartToken);
      setCart(updatedCart);
      showToast('Đã gỡ mã ưu đãi.');
      return true;
    } catch (err: any) {
      showToast(err.message || 'Không thể gỡ mã');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const clearCart = async (): Promise<boolean> => {
    if (!cartToken) return false;
    try {
      setIsLoading(true);
      const updatedCart = await cartApi.clearCart(cartToken);
      setCart(updatedCart);
      showToast('Đã xóa toàn bộ giỏ hàng.');
      return true;
    } catch (err: any) {
      showToast(err.message || 'Không thể làm trống giỏ hàng');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const itemCount = cart?.total_items || 0;

  return (
    <CartContext.Provider
      value={{
        cart,
        cartToken,
        itemCount,
        isLoading,
        addItem,
        updateQuantity,
        removeItem,
        applyCoupon,
        removeCoupon,
        clearCart,
        refreshCart,
        toastMessage,
        clearToast,
      }}
    >
      {children}
      {/* Toast Feedback Notification */}
      {toastMessage && (
        <div className="fixed bottom-20 right-4 sm:bottom-6 sm:right-6 z-50 bg-slate-900/95 text-white px-4 py-3 rounded-2xl shadow-xl flex items-center space-x-3 text-xs sm:text-sm animate-fade-in border border-emerald-500/30">
          <span className="text-emerald-400 text-base">🌿</span>
          <span className="font-medium">{toastMessage}</span>
          <button
            onClick={clearToast}
            className="text-slate-400 hover:text-white ml-2 text-xs font-bold"
          >
            ✕
          </button>
        </div>
      )}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
