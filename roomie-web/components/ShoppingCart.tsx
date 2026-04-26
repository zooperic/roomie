'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

interface CartItem {
  query: string;
  matched: string | null;
  sku: string;
  price: number;
  quantity: number;
  unit_price?: number;
  total_price: number;
  pack_size?: string;
  brand?: string;
  category?: string;
  error?: string;
}

interface CartResult {
  matched_items: CartItem[];
  total_items: number;
  successfully_matched?: number;
  total_cost: number;
  source?: string;
  categories?: Record<string, CartItem[]>;
  subtotal?: number;
  delivery_fee?: number;
  total?: number;
  platform?: string;
}

export default function ShoppingCart() {
  const [items, setItems] = useState<Array<{ name: string; quantity?: number; unit?: string }>>([]);
  const [cartResult, setCartResult] = useState<CartResult | null>(null);
  const [newItem, setNewItem] = useState('');

  // Listen for build-cart events from RecipeParser
  useEffect(() => {
    const handleBuildCart = (e: CustomEvent) => {
      if (e.detail?.items) {
        setItems(e.detail.items);
        buildCartMutation.mutate(e.detail.items);
      }
    };

    window.addEventListener('build-cart', handleBuildCart as EventListener);
    return () => {
      window.removeEventListener('build-cart', handleBuildCart as EventListener);
    };
  }, []);

  const buildCartMutation = useMutation({
    mutationFn: (items: Array<{ name: string; quantity?: number; unit?: string }>) =>
      alfredClient.buildCart(items),
    onSuccess: (data) => {
      try {
        const response = typeof data.response === 'string' 
          ? JSON.parse(data.response) 
          : data.response;
        setCartResult(response);
      } catch {
        setCartResult(null);
      }
    },
  });

  const placeOrderMutation = useMutation({
    mutationFn: (cart: CartResult) => {
      const message = `place order with cart: ${JSON.stringify(cart)}`;
      return alfredClient.sendMessage(message, 'web-user', 'lebowski');
    },
    onSuccess: (data) => {
      alert('Order placed! Check the Events tab for confirmation.');
      setCartResult(null);
      setItems([]);
    },
  });

  const handleAddItem = () => {
    if (!newItem.trim()) return;
    
    const item = { name: newItem.trim() };
    const updatedItems = [...items, item];
    setItems(updatedItems);
    setNewItem('');
    buildCartMutation.mutate(updatedItems);
  };

  const handleRemoveItem = (index: number) => {
    const updatedItems = items.filter((_, i) => i !== index);
    setItems(updatedItems);
    if (updatedItems.length > 0) {
      buildCartMutation.mutate(updatedItems);
    } else {
      setCartResult(null);
    }
  };

  const handlePlaceOrder = () => {
    if (!cartResult) return;
    
    const confirmMessage = `Place order for ₹${cartResult.total || cartResult.total_cost}?\n\n` +
      `Platform: ${cartResult.platform || cartResult.source || 'Swiggy'}\n` +
      `Items: ${cartResult.total_items}\n` +
      `Payment: COD\n\n` +
      `This will place a REAL order that cannot be cancelled.`;
    
    if (confirm(confirmMessage)) {
      placeOrderMutation.mutate(cartResult);
    }
  };

  const groupedItems = cartResult?.categories || {};
  const hasCategories = Object.keys(groupedItems).length > 0;

  return (
    <div className="fade-in">
      {/* Add Items Input */}
      <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ 
          fontSize: '10px', 
          color: '#666', 
          letterSpacing: '0.1em', 
          marginBottom: '12px' 
        }}>
          BUILD YOUR CART
        </div>
        
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input
            type="text"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddItem()}
            placeholder="Add item (e.g., milk, 500g paneer, 2L oil)..."
            style={{
              flex: 1,
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '10px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
          <button
            onClick={handleAddItem}
            disabled={!newItem.trim()}
            style={{
              background: newItem.trim() ? '#22c55e' : '#1a1a1a',
              color: newItem.trim() ? '#000' : '#444',
              border: 'none',
              borderRadius: '2px',
              padding: '10px 20px',
              fontSize: '11px',
              fontWeight: '500',
              letterSpacing: '0.08em',
              cursor: newItem.trim() ? 'pointer' : 'not-allowed',
            }}
          >
            ADD
          </button>
        </div>

        {/* Current Items List */}
        {items.length > 0 && (
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '8px',
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px solid #1a1a1a'
          }}>
            {items.map((item, i) => (
              <span
                key={i}
                className="badge"
                style={{ 
                  background: '#1a1a1a',
                  color: '#e8e8e8',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {item.name}
                {item.quantity && ` (${item.quantity}${item.unit || ''})`}
                <button
                  onClick={() => handleRemoveItem(i)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#f87171',
                    cursor: 'pointer',
                    padding: 0,
                    fontSize: '12px',
                  }}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Loading State */}
      {buildCartMutation.isPending && (
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#666' }}>
            Matching items to catalog...
          </div>
        </div>
      )}

      {/* Cart Results */}
      {cartResult && !buildCartMutation.isPending && (
        <div className="fade-in">
          {/* Summary Header */}
          <div className="card" style={{ 
            padding: '20px', 
            marginBottom: '20px',
            borderColor: '#22c55e'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between' 
            }}>
              <div>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                  {cartResult.platform || cartResult.source || 'SHOPPING CART'}
                </div>
                <div style={{ fontSize: '24px', fontWeight: '300', color: '#fff' }}>
                  ₹{cartResult.total || cartResult.total_cost}
                </div>
                <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                  {cartResult.successfully_matched || cartResult.total_items} of {cartResult.total_items} items matched
                </div>
              </div>
              <button
                onClick={handlePlaceOrder}
                disabled={placeOrderMutation.isPending}
                style={{
                  background: '#22c55e',
                  color: '#000',
                  border: 'none',
                  borderRadius: '2px',
                  padding: '12px 24px',
                  fontSize: '11px',
                  fontWeight: '500',
                  letterSpacing: '0.08em',
                  cursor: 'pointer',
                }}
              >
                {placeOrderMutation.isPending ? 'PLACING...' : 'PLACE ORDER'}
              </button>
            </div>
          </div>

          {/* Items by Category or Flat List */}
          {hasCategories ? (
            Object.entries(groupedItems).map(([category, categoryItems]) => (
              <div key={category} style={{ marginBottom: '20px' }}>
                <div style={{ 
                  fontSize: '10px', 
                  color: '#666', 
                  letterSpacing: '0.1em',
                  marginBottom: '12px'
                }}>
                  {category.toUpperCase()}
                </div>
                <div style={{ 
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                  gap: '12px'
                }}>
                  {categoryItems.map((item, i) => (
                    <CartItemCard key={i} item={item} />
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div style={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
              gap: '12px'
            }}>
              {cartResult.matched_items.map((item, i) => (
                <CartItemCard key={i} item={item} />
              ))}
            </div>
          )}

          {/* Price Breakdown */}
          {cartResult.subtotal !== undefined && (
            <div className="card" style={{ padding: '20px', marginTop: '20px' }}>
              <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '12px' }}>
                PRICE BREAKDOWN
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                  <span style={{ color: '#888' }}>Subtotal:</span>
                  <span style={{ color: '#fff' }}>₹{cartResult.subtotal}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                  <span style={{ color: '#888' }}>Delivery Fee:</span>
                  <span style={{ color: '#fff' }}>
                    {cartResult.delivery_fee === 0 ? 'FREE' : `₹${cartResult.delivery_fee}`}
                  </span>
                </div>
                <div style={{ 
                  borderTop: '1px solid #1a1a1a', 
                  paddingTop: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  fontWeight: '500'
                }}>
                  <span style={{ color: '#fff' }}>Total:</span>
                  <span style={{ color: '#22c55e' }}>₹{cartResult.total}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {items.length === 0 && !cartResult && (
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>🛒</div>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
            Your cart is empty
          </div>
          <div style={{ fontSize: '11px', color: '#555' }}>
            Add items manually or use the Recipe Parser to build a cart
          </div>
        </div>
      )}
    </div>
  );
}

function CartItemCard({ item }: { item: CartItem }) {
  return (
    <div className="card" style={{ padding: '16px' }}>
      {item.error ? (
        <div>
          <div style={{ fontSize: '11px', color: '#f87171', marginBottom: '4px' }}>
            ⚠️ Not Found
          </div>
          <div style={{ fontSize: '10px', color: '#666' }}>
            {item.query}
          </div>
        </div>
      ) : (
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'start',
            marginBottom: '8px'
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '11px', fontWeight: '500', color: '#fff' }}>
                {item.matched}
              </div>
              {item.brand && (
                <div style={{ fontSize: '9px', color: '#666', marginTop: '2px' }}>
                  {item.brand}
                </div>
              )}
            </div>
            <div style={{ fontSize: '13px', fontWeight: '500', color: '#22c55e' }}>
              ₹{item.total_price}
            </div>
          </div>

          {item.pack_size && (
            <div style={{ fontSize: '10px', color: '#888', marginBottom: '8px' }}>
              {item.pack_size}
            </div>
          )}

          <div style={{ 
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '8px',
            borderTop: '1px solid #1a1a1a'
          }}>
            <div style={{ fontSize: '10px', color: '#666' }}>
              Qty: {item.quantity}
            </div>
            <div style={{ fontSize: '10px', color: '#666' }}>
              ₹{item.unit_price || item.price} each
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
