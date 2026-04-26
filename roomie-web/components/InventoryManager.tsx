'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alfredClient, type InventoryItem } from '@/lib/alfred-client';

const CATEGORY_COLORS: Record<string, string> = {
  dairy: '#e2e8f0',
  produce: '#a3e635',
  meat: '#f87171',
  beverages: '#60a5fa',
  condiments: '#fbbf24',
  leftovers: '#a78bfa',
  snacks: '#fb923c',
  grains: '#c084fc',
  spices: '#f472b6',
};

function isLow(item: InventoryItem) {
  return item.low_stock_threshold && item.quantity <= item.low_stock_threshold;
}

function stockPercent(item: InventoryItem) {
  if (!item.low_stock_threshold) return 100;
  return Math.min(100, Math.round((item.quantity / (item.low_stock_threshold * 2)) * 100));
}

interface InventoryManagerProps {
  type: 'fridge' | 'pantry';
}

export default function InventoryManager({ type }: InventoryManagerProps) {
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const queryClient = useQueryClient();

  const queryKey = [`inventory-${type}`];
  
  // Fetch inventory
  const { data: items = [], isLoading } = useQuery({
    queryKey,
    queryFn: () => type === 'fridge' ? alfredClient.getFridgeInventory() : alfredClient.getPantryInventory(),
    refetchInterval: 10000,
  });

  // Add item mutation
  const addMutation = useMutation({
    mutationFn: (item: Partial<InventoryItem>) => alfredClient.addInventoryItem(item, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      setIsAddingItem(false);
    },
  });

  // Update item mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, item }: { id: number; item: Partial<InventoryItem> }) =>
      alfredClient.updateInventoryItem(id, item, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      setEditingItem(null);
    },
  });

  // Delete item mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => alfredClient.deleteInventoryItem(id, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const lowItems = filteredItems.filter(isLow);

  if (isLoading) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '14px', color: '#666' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      {/* Header Actions */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search items..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            background: '#111',
            border: '1px solid #1e1e1e',
            borderRadius: '2px',
            padding: '8px 12px',
            color: '#e8e8e8',
            fontSize: '11px',
            flex: 1,
          }}
        />
        <button
          onClick={() => setIsAddingItem(true)}
          style={{
            background: '#22c55e',
            color: '#000',
            border: 'none',
            borderRadius: '2px',
            padding: '8px 16px',
            fontSize: '11px',
            fontWeight: '500',
            cursor: 'pointer',
            letterSpacing: '0.05em',
          }}
        >
          + ADD ITEM
        </button>
      </div>

      {/* Low Stock Warning */}
      {lowItems.length > 0 && (
        <div className="card" style={{ padding: '16px', marginBottom: '20px', borderColor: '#fbbf24' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span>⚠️</span>
            <span style={{ fontSize: '11px', color: '#fbbf24', letterSpacing: '0.08em' }}>
              {lowItems.length} LOW STOCK ITEMS
            </span>
          </div>
          <div style={{ fontSize: '10px', color: '#ccc' }}>
            {lowItems.map(i => i.name).join(', ')}
          </div>
        </div>
      )}

      {/* Add Item Form */}
      {isAddingItem && (
        <ItemForm
          onSubmit={(item) => addMutation.mutate(item)}
          onCancel={() => setIsAddingItem(false)}
          isSubmitting={addMutation.isPending}
        />
      )}

      {/* Edit Item Form */}
      {editingItem && (
        <ItemForm
          initialItem={editingItem}
          onSubmit={(item) => updateMutation.mutate({ id: editingItem.id!, item })}
          onCancel={() => setEditingItem(null)}
          isSubmitting={updateMutation.isPending}
        />
      )}

      {/* Inventory Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '12px'
      }}>
        {filteredItems.map((item) => (
          <div key={item.id} className="card" style={{ padding: '16px', position: 'relative' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '8px'
            }}>
              <span style={{ fontSize: '11px', fontWeight: '500' }}>{item.name}</span>
              {isLow(item) && <span>⚠️</span>}
            </div>

            <div style={{ fontSize: '20px', color: '#fff', marginBottom: '8px' }}>
              {item.quantity} <span style={{ fontSize: '11px', color: '#666' }}>{item.unit}</span>
            </div>

            {item.category && (
              <span
                className="badge"
                style={{
                  background: CATEGORY_COLORS[item.category] || '#333',
                  color: '#000',
                  marginBottom: '8px',
                }}
              >
                {item.category}
              </span>
            )}

            {item.low_stock_threshold && (
              <div style={{ marginTop: '12px', marginBottom: '12px' }}>
                <div style={{
                  height: '3px',
                  background: '#1a1a1a',
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div
                    className="bar-fill"
                    style={{
                      height: '100%',
                      width: `${stockPercent(item)}%`,
                      background: isLow(item) ? '#fbbf24' : '#22c55e'
                    }}
                  />
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                onClick={() => setEditingItem(item)}
                style={{
                  background: '#1a1a1a',
                  color: '#888',
                  border: 'none',
                  borderRadius: '2px',
                  padding: '4px 8px',
                  fontSize: '9px',
                  cursor: 'pointer',
                  flex: 1,
                }}
              >
                EDIT
              </button>
              <button
                onClick={() => {
                  if (confirm(`Delete ${item.name}?`)) {
                    deleteMutation.mutate(item.id!);
                  }
                }}
                style={{
                  background: '#1a1a1a',
                  color: '#f87171',
                  border: 'none',
                  borderRadius: '2px',
                  padding: '4px 8px',
                  fontSize: '9px',
                  cursor: 'pointer',
                  flex: 1,
                }}
              >
                DELETE
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#666' }}>
            {searchQuery ? 'No items match your search' : `No items in ${type}`}
          </div>
        </div>
      )}
    </div>
  );
}

interface ItemFormProps {
  initialItem?: InventoryItem;
  onSubmit: (item: Partial<InventoryItem>) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

function ItemForm({ initialItem, onSubmit, onCancel, isSubmitting }: ItemFormProps) {
  const [name, setName] = useState(initialItem?.name || '');
  const [quantity, setQuantity] = useState(initialItem?.quantity?.toString() || '');
  const [unit, setUnit] = useState(initialItem?.unit || 'units');
  const [category, setCategory] = useState(initialItem?.category || '');
  const [threshold, setThreshold] = useState(initialItem?.low_stock_threshold?.toString() || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      quantity: parseFloat(quantity),
      unit,
      category: category || undefined,
      low_stock_threshold: threshold ? parseFloat(threshold) : undefined,
    });
  };

  return (
    <div className="card" style={{ padding: '20px', marginBottom: '20px' }}>
      <form onSubmit={handleSubmit}>
        <div style={{ fontSize: '11px', color: '#666', letterSpacing: '0.1em', marginBottom: '16px' }}>
          {initialItem ? 'EDIT ITEM' : 'ADD NEW ITEM'}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '12px', marginBottom: '12px' }}>
          <input
            type="text"
            placeholder="Item name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '8px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
          <input
            type="number"
            step="0.01"
            placeholder="Qty"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
            style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '8px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
          <select
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '8px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          >
            <option value="units">units</option>
            <option value="grams">grams</option>
            <option value="kg">kg</option>
            <option value="ml">ml</option>
            <option value="liters">liters</option>
          </select>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Category (optional)"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '8px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
          <input
            type="number"
            step="0.01"
            placeholder="Low stock threshold (optional)"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '8px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              background: '#22c55e',
              color: '#000',
              border: 'none',
              borderRadius: '2px',
              padding: '8px 16px',
              fontSize: '11px',
              fontWeight: '500',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              opacity: isSubmitting ? 0.5 : 1,
            }}
          >
            {isSubmitting ? 'SAVING...' : 'SAVE'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            style={{
              background: '#1a1a1a',
              color: '#888',
              border: 'none',
              borderRadius: '2px',
              padding: '8px 16px',
              fontSize: '11px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
            }}
          >
            CANCEL
          </button>
        </div>
      </form>
    </div>
  );
}
