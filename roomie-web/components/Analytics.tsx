'use client';

import { useQuery } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

export default function Analytics() {
  const { data: fridgeItems = [] } = useQuery({
    queryKey: ['inventory-fridge'],
    queryFn: () => alfredClient.getFridgeInventory(),
  });

  const { data: pantryItems = [] } = useQuery({
    queryKey: ['inventory-pantry'],
    queryFn: () => alfredClient.getPantryInventory(),
  });

  const { data: status } = useQuery({
    queryKey: ['alfred-status'],
    queryFn: () => alfredClient.getStatus(),
  });

  const allItems = [...fridgeItems, ...pantryItems];

  // Analytics calculations
  const totalItems = allItems.length;
  const lowStockItems = allItems.filter(i => 
    i.low_stock_threshold && i.quantity <= i.low_stock_threshold
  );
  const wellStockedItems = allItems.filter(i => 
    !i.low_stock_threshold || i.quantity > i.low_stock_threshold
  );

  // Category breakdown
  const categoryBreakdown = allItems.reduce((acc, item) => {
    const cat = item.category || 'uncategorized';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topCategories = Object.entries(categoryBreakdown)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  // Stock health score (0-100)
  const stockHealthScore = totalItems > 0
    ? Math.round(((totalItems - lowStockItems.length) / totalItems) * 100)
    : 100;

  // Insights generation
  const insights = [];

  if (lowStockItems.length > 0) {
    insights.push({
      type: 'warning',
      icon: '⚠️',
      title: 'Low Stock Alert',
      message: `${lowStockItems.length} item${lowStockItems.length !== 1 ? 's' : ''} running low`,
      items: lowStockItems.slice(0, 3).map(i => i.name),
      color: '#fbbf24',
    });
  }

  if (stockHealthScore >= 80) {
    insights.push({
      type: 'success',
      icon: '✅',
      title: 'Well Stocked',
      message: 'Your kitchen is in great shape!',
      color: '#22c55e',
    });
  }

  if (totalItems < 5) {
    insights.push({
      type: 'info',
      icon: '📦',
      title: 'Stock Up',
      message: 'Your inventory is looking sparse. Time to shop?',
      color: '#60a5fa',
    });
  }

  const mostCommonCategory = topCategories[0]?.[0];
  if (mostCommonCategory) {
    insights.push({
      type: 'info',
      icon: '📊',
      title: 'Category Leader',
      message: `Most of your items are ${mostCommonCategory}`,
      color: '#8b5cf6',
    });
  }

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ fontSize: '36px', marginBottom: '12px' }}>📊</div>
        <div style={{ fontSize: '20px', fontWeight: '300', color: '#fff', marginBottom: '8px' }}>
          Kitchen Analytics
        </div>
        <div style={{ fontSize: '11px', color: '#666' }}>
          Insights powered by Finn 🎯
        </div>
      </div>

      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div className="card" style={{ padding: '20px', borderColor: '#22c55e' }}>
          <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
            STOCK HEALTH
          </div>
          <div style={{ fontSize: '32px', fontWeight: '300', color: '#22c55e', marginBottom: '4px' }}>
            {stockHealthScore}%
          </div>
          <div style={{ fontSize: '10px', color: '#999' }}>
            {stockHealthScore >= 80 ? 'Excellent' : stockHealthScore >= 60 ? 'Good' : 'Needs attention'}
          </div>
        </div>

        <div className="card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
            TOTAL ITEMS
          </div>
          <div style={{ fontSize: '32px', fontWeight: '300', color: '#fff', marginBottom: '4px' }}>
            {totalItems}
          </div>
          <div style={{ fontSize: '10px', color: '#999' }}>
            {fridgeItems.length} fridge · {pantryItems.length} pantry
          </div>
        </div>

        <div className="card" style={{ padding: '20px', borderColor: lowStockItems.length > 0 ? '#fbbf24' : '#1a1a1a' }}>
          <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
            LOW STOCK
          </div>
          <div style={{ fontSize: '32px', fontWeight: '300', color: lowStockItems.length > 0 ? '#fbbf24' : '#666', marginBottom: '4px' }}>
            {lowStockItems.length}
          </div>
          <div style={{ fontSize: '10px', color: '#999' }}>
            {lowStockItems.length > 0 ? 'Needs restocking' : 'All good!'}
          </div>
        </div>

        <div className="card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
            CATEGORIES
          </div>
          <div style={{ fontSize: '32px', fontWeight: '300', color: '#fff', marginBottom: '4px' }}>
            {Object.keys(categoryBreakdown).length}
          </div>
          <div style={{ fontSize: '10px', color: '#999' }}>
            {mostCommonCategory || 'No categories'}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ 
          fontSize: '10px', 
          color: '#666', 
          letterSpacing: '0.1em',
          marginBottom: '16px'
        }}>
          INSIGHTS
        </div>

        {insights.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {insights.map((insight, i) => (
              <div
                key={i}
                style={{
                  background: `${insight.color}11`,
                  border: `1px solid ${insight.color}33`,
                  borderRadius: '6px',
                  padding: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '24px' }}>{insight.icon}</span>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: '500', color: '#fff', marginBottom: '2px' }}>
                      {insight.title}
                    </div>
                    <div style={{ fontSize: '10px', color: '#888' }}>
                      {insight.message}
                    </div>
                  </div>
                </div>
                {insight.items && insight.items.length > 0 && (
                  <div style={{ 
                    fontSize: '9px', 
                    color: '#666',
                    marginLeft: '36px'
                  }}>
                    {insight.items.join(', ')}
                    {insight.items.length < lowStockItems.length && ' and more...'}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎯</div>
            <div style={{ fontSize: '11px' }}>
              Add more items to get insights
            </div>
          </div>
        )}
      </div>

      {/* Category Breakdown */}
      <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ 
          fontSize: '10px', 
          color: '#666', 
          letterSpacing: '0.1em',
          marginBottom: '16px'
        }}>
          CATEGORY BREAKDOWN
        </div>

        {topCategories.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {topCategories.map(([category, count]) => {
              const percentage = totalItems > 0 ? Math.round((count / totalItems) * 100) : 0;
              const colors = {
                dairy: '#e2e8f0',
                produce: '#a3e635',
                meat: '#f87171',
                beverages: '#60a5fa',
                condiments: '#fbbf24',
                snacks: '#fb923c',
                grains: '#c084fc',
                spices: '#f472b6',
              };
              const color = colors[category as keyof typeof colors] || '#888';

              return (
                <div key={category}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    marginBottom: '6px'
                  }}>
                    <div style={{ fontSize: '11px', color: '#fff', textTransform: 'capitalize' }}>
                      {category}
                    </div>
                    <div style={{ fontSize: '10px', color: '#666' }}>
                      {count} items · {percentage}%
                    </div>
                  </div>
                  <div style={{
                    height: '6px',
                    background: '#1a1a1a',
                    borderRadius: '3px',
                    overflow: 'hidden',
                  }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${percentage}%`,
                        background: color,
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <div style={{ fontSize: '11px' }}>
              No categories assigned yet
            </div>
          </div>
        )}
      </div>

      {/* Low Stock Details */}
      {lowStockItems.length > 0 && (
        <div className="card" style={{ padding: '24px', borderColor: '#fbbf24' }}>
          <div style={{ 
            fontSize: '10px', 
            color: '#fbbf24', 
            letterSpacing: '0.1em',
            marginBottom: '16px'
          }}>
            ⚠️ ITEMS NEEDING RESTOCK ({lowStockItems.length})
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '12px',
          }}>
            {lowStockItems.map((item, i) => (
              <div
                key={i}
                style={{
                  background: '#1a1a1a',
                  border: '1px solid #2a2a2a',
                  borderRadius: '4px',
                  padding: '12px',
                }}
              >
                <div style={{ fontSize: '11px', color: '#fff', marginBottom: '4px' }}>
                  {item.name}
                </div>
                <div style={{ fontSize: '10px', color: '#fbbf24', marginBottom: '4px' }}>
                  {item.quantity} {item.unit} remaining
                </div>
                {item.low_stock_threshold && (
                  <div style={{ fontSize: '9px', color: '#666' }}>
                    Threshold: {item.low_stock_threshold} {item.unit}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Status */}
      {status?.agents?.finn && (
        <div className="card" style={{ padding: '20px', marginTop: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '32px' }}>🎯</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>
                Finn says:
              </div>
              <div style={{ fontSize: '10px', color: '#ccc' }}>
                {status.agents.finn.summary || 'Analytics system operational'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
