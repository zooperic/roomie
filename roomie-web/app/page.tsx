'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';
import InventoryManager from '@/components/InventoryManager';
import RecipeParser from '@/components/RecipeParser';
import ShoppingCart from '@/components/ShoppingCart';
import Roomies from '@/components/Roomies';
import AgentChat from '@/components/AgentChat';
import PhotoScanner from '@/components/PhotoScanner';
import Analytics from '@/components/Analytics';

const MOCK_EVENTS = [
  { time: '09:14', agent: 'elsa', type: 'inventory_update', detail: 'Added 1L milk' },
  { time: '09:32', agent: 'alfred', type: 'order_confirmed', detail: 'InstaMart order ₹312 confirmed' },
  { time: '11:05', agent: 'elsa', type: 'low_stock_alert', detail: 'Eggs running low (2 left)' },
  { time: '13:22', agent: 'remy', type: 'recipe_parsed', detail: 'Pasta → 2 items missing' },
  { time: '15:47', agent: 'lebowski', type: 'order_suggested', detail: 'Cart of 3 items ready' },
];

function isLow(item: { quantity: number; low_stock_threshold?: number }) {
  return item.low_stock_threshold !== null && 
         item.low_stock_threshold !== undefined && 
         item.quantity <= item.low_stock_threshold;
}

export default function Dashboard() {
  const [tab, setTab] = useState('overview');
  const [selectedAgent, setSelectedAgent] = useState('alfred');
  const [time, setTime] = useState(new Date());

  // Fetch Alfred status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['alfred-status'],
    queryFn: () => alfredClient.getStatus(),
    refetchInterval: 5000,
  });

  // Fetch fridge inventory for overview stats
  const { data: fridgeItems = [] } = useQuery({
    queryKey: ['inventory-fridge'],
    queryFn: () => alfredClient.getFridgeInventory(),
    refetchInterval: 10000,
  });

  // Fetch pantry inventory for overview stats
  const { data: pantryItems = [] } = useQuery({
    queryKey: ['inventory-pantry'],
    queryFn: () => alfredClient.getPantryInventory(),
    refetchInterval: 10000,
  });

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const allItems = [...fridgeItems, ...pantryItems];
  const lowItems = allItems.filter(isLow);
  const isOnline = status?.status === 'healthy' || !statusLoading;

  return (
    <div style={{
      minHeight: '100vh',
      background: '#080808',
      color: '#e8e8e8',
      fontFamily: 'var(--font-dm-mono)',
      padding: '0',
    }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid #1a1a1a',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '56px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div>
            <span style={{
              fontFamily: 'var(--font-bebas-neue)',
              fontSize: '22px',
              letterSpacing: '0.15em',
              color: '#fff',
            }}>ROOMIE</span>
            <div style={{ 
              fontSize: '7px', 
              color: '#444', 
              letterSpacing: '0.05em',
              marginTop: '2px'
            }}>
              Random Operators On My Individual Errands
            </div>
          </div>
          <span style={{ color: '#2a2a2a', fontSize: '12px' }}>|</span>
          <nav style={{ display: 'flex', gap: '4px' }}>
            {['overview', 'inventory', 'recipe', 'shopping', 'scan', 'chat', 'analytics', 'roomies', 'events'].map(t => (
              <button
                key={t}
                className="tab-btn"
                onClick={() => setTab(t)}
                style={{
                  color: tab === t ? '#fff' : '#444',
                  fontSize: '11px',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  padding: '6px 12px',
                  borderBottom: tab === t ? '1px solid #fff' : '1px solid transparent',
                }}
              >{t}</button>
            ))}
          </nav>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ fontSize: '10px', color: '#333', letterSpacing: '0.05em' }}>
            {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span 
              className={isOnline ? 'pulse' : ''} 
              style={{ 
                width: 6, 
                height: 6, 
                borderRadius: '50%', 
                background: isOnline ? '#22c55e' : '#ef4444',
                display: 'inline-block' 
              }} 
            />
            <span style={{ fontSize: '10px', color: '#444', letterSpacing: '0.08em' }}>
              {isOnline ? 'ALFRED ONLINE' : 'ALFRED OFFLINE'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto' }}>
        {tab === 'overview' && (
          <div className="fade-in">
            {/* Quick Stats */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
              gap: '16px',
              marginBottom: '24px' 
            }}>
              <div 
                className="card" 
                onClick={() => setTab('inventory')}
                style={{ 
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = '#22c55e'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#1a1a1a'}
              >
                <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  FRIDGE ITEMS
                </div>
                <div style={{ fontSize: '32px', fontWeight: '300', color: '#fff' }}>
                  {fridgeItems.length}
                </div>
                <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                  {fridgeItems.filter(isLow).length} low stock
                </div>
              </div>

              <div 
                className="card" 
                onClick={() => setTab('inventory')}
                style={{ 
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = '#f59e0b'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#1a1a1a'}
              >
                <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  PANTRY ITEMS
                </div>
                <div style={{ fontSize: '32px', fontWeight: '300', color: '#fff' }}>
                  {pantryItems.length}
                </div>
                <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                  {pantryItems.filter(isLow).length} low stock
                </div>
              </div>

              <div 
                className="card" 
                onClick={() => setTab('roomies')}
                style={{ 
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = '#60a5fa'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#1a1a1a'}
              >
                <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  AGENTS STATUS
                </div>
                <div style={{ fontSize: '32px', fontWeight: '300', color: '#22c55e' }}>
                  {status?.agents ? Object.keys(status.agents).length : 4}
                </div>
                <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                  all systems operational
                </div>
              </div>

              <div className="card" style={{ padding: '20px' }}>
                <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  RECENT ACTIVITY
                </div>
                <div style={{ fontSize: '32px', fontWeight: '300', color: '#fff' }}>
                  {MOCK_EVENTS.length}
                </div>
                <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                  events today
                </div>
              </div>
            </div>

            {/* Low Stock Alert */}
            {lowItems.length > 0 && (
              <div className="card" style={{ padding: '20px', marginBottom: '24px', borderColor: '#fbbf24' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <span style={{ fontSize: '18px' }}>⚠️</span>
                  <span style={{ fontSize: '12px', color: '#fbbf24', letterSpacing: '0.1em' }}>
                    LOW STOCK WARNING
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#ccc', lineHeight: '1.6' }}>
                  {lowItems.map(i => i.name).join(', ')} running low. Consider restocking soon.
                </div>
              </div>
            )}

            {/* Recent Events */}
            <div className="card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '16px' }}>
                RECENT EVENTS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {MOCK_EVENTS.slice(0, 5).map((event, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'start' }}>
                    <span style={{ fontSize: '10px', color: '#444', width: '50px' }}>
                      {event.time}
                    </span>
                    <span className="badge" style={{ background: '#1a1a1a', color: '#888' }}>
                      {event.agent}
                    </span>
                    <span style={{ fontSize: '11px', color: '#ccc', flex: 1 }}>
                      {event.detail}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === 'inventory' && (
          <div className="fade-in">
            <div style={{ marginBottom: '24px' }}>
              <div style={{ fontSize: '12px', color: '#666', letterSpacing: '0.1em', marginBottom: '16px' }}>
                FRIDGE
              </div>
              <InventoryManager type="fridge" />
            </div>

            <div style={{ marginTop: '40px' }}>
              <div style={{ fontSize: '12px', color: '#666', letterSpacing: '0.1em', marginBottom: '16px' }}>
                PANTRY
              </div>
              <InventoryManager type="pantry" />
            </div>
          </div>
        )}

        {tab === 'recipe' && (
          <div className="fade-in">
            <RecipeParser />
          </div>
        )}

        {tab === 'shopping' && (
          <div className="fade-in">
            <ShoppingCart />
          </div>
        )}

        {tab === 'scan' && (
          <div className="fade-in">
            <PhotoScanner />
          </div>
        )}

        {tab === 'chat' && (
          <div className="fade-in">
            {/* Agent Selector */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: '#666', 
                letterSpacing: '0.1em',
                marginBottom: '12px'
              }}>
                SELECT AGENT
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {['alfred', 'elsa', 'remy', 'lebowski', 'finn', 'iris'].map(agent => {
                  const agentInfo = {
                    alfred: { emoji: '🎩', color: '#60a5fa' },
                    elsa: { emoji: '❄️', color: '#22c55e' },
                    remy: { emoji: '👨‍🍳', color: '#f59e0b' },
                    lebowski: { emoji: '🥃', color: '#a78bfa' },
                    finn: { emoji: '🎯', color: '#ec4899' },
                    iris: { emoji: '👁️', color: '#8b5cf6' },
                  }[agent as 'alfred' | 'elsa' | 'remy' | 'lebowski' | 'finn' | 'iris'];
                  
                  return (
                    <button
                      key={agent}
                      onClick={() => setSelectedAgent(agent)}
                      style={{
                        background: selectedAgent === agent ? agentInfo?.color : '#1a1a1a',
                        color: selectedAgent === agent ? '#000' : '#888',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '10px 16px',
                        fontSize: '11px',
                        fontWeight: '500',
                        letterSpacing: '0.05em',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <span style={{ fontSize: '16px' }}>{agentInfo?.emoji}</span>
                      {agent.toUpperCase()}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Chat Interface */}
            <AgentChat agentId={selectedAgent} key={selectedAgent} />
          </div>
        )}

        {tab === 'roomies' && (
          <div className="fade-in">
            <Roomies />
          </div>
        )}

        {tab === 'analytics' && (
          <div className="fade-in">
            <Analytics />
          </div>
        )}

        {tab === 'events' && (
          <div className="fade-in">
            <div className="card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '20px' }}>
                EVENT LOG
              </div>
              {MOCK_EVENTS.map((event, i) => (
                <div 
                  key={i} 
                  style={{ 
                    display: 'flex', 
                    gap: '16px', 
                    padding: '12px 0',
                    borderBottom: i < MOCK_EVENTS.length - 1 ? '1px solid #1a1a1a' : 'none'
                  }}
                >
                  <span style={{ fontSize: '10px', color: '#444', width: '60px' }}>
                    {event.time}
                  </span>
                  <span className="badge" style={{ background: '#1a1a1a', color: '#888' }}>
                    {event.agent}
                  </span>
                  <span className="badge" style={{ background: '#1a1a1a', color: '#888' }}>
                    {event.type}
                  </span>
                  <span style={{ fontSize: '11px', color: '#ccc', flex: 1 }}>
                    {event.detail}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
