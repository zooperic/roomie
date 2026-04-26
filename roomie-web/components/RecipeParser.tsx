'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

type ParseMode = 'url' | 'text' | 'dish';

interface RecipeResult {
  recipe_name: string;
  ingredients: Array<{
    name: string;
    quantity?: number;
    unit?: string;
    available: boolean;
  }>;
  available_items: string[];
  missing_items: Array<{
    name: string;
    quantity?: number;
    unit?: string;
  }>;
  can_make: boolean;
}

export default function RecipeParser() {
  const [mode, setMode] = useState<ParseMode>('dish');
  const [input, setInput] = useState('');
  const [result, setResult] = useState<RecipeResult | null>(null);

  const parseMutation = useMutation({
    mutationFn: (params: { input: string; mode: ParseMode }) =>
      alfredClient.parseRecipe(params.input, params.mode),
    onSuccess: (data) => {
      // Parse the response to extract recipe info
      // The actual structure depends on Remy's response format
      try {
        const response = typeof data.response === 'string' 
          ? JSON.parse(data.response) 
          : data.response;
        setResult(response);
      } catch {
        // If parsing fails, show raw response
        setResult({
          recipe_name: 'Recipe',
          ingredients: [],
          available_items: [],
          missing_items: [],
          can_make: false,
        });
      }
    },
  });

  const handleParse = () => {
    if (!input.trim()) return;
    parseMutation.mutate({ input: input.trim(), mode });
    setResult(null);
  };

  const handleShopNow = () => {
    // Navigate to cart builder with missing items
    if (result?.missing_items) {
      window.dispatchEvent(
        new CustomEvent('build-cart', { 
          detail: { items: result.missing_items } 
        })
      );
    }
  };

  return (
    <div className="fade-in">
      {/* Mode Selector */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ 
          fontSize: '10px', 
          color: '#666', 
          letterSpacing: '0.1em', 
          marginBottom: '12px' 
        }}>
          INPUT METHOD
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { mode: 'dish' as ParseMode, label: 'DISH NAME' },
            { mode: 'url' as ParseMode, label: 'RECIPE URL' },
            { mode: 'text' as ParseMode, label: 'PASTE RECIPE' },
          ].map(({ mode: m, label }) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{
                background: mode === m ? '#fff' : '#1a1a1a',
                color: mode === m ? '#000' : '#666',
                border: 'none',
                borderRadius: '2px',
                padding: '8px 16px',
                fontSize: '10px',
                letterSpacing: '0.08em',
                cursor: 'pointer',
                fontWeight: mode === m ? '500' : '400',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
        {mode === 'text' ? (
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste recipe text here..."
            style={{
              width: '100%',
              minHeight: '200px',
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '12px',
              color: '#e8e8e8',
              fontSize: '11px',
              fontFamily: 'inherit',
              resize: 'vertical',
            }}
          />
        ) : (
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleParse()}
            placeholder={
              mode === 'url'
                ? 'https://example.com/recipe...'
                : 'E.g., Butter Chicken, Pasta Carbonara, Paneer Tikka...'
            }
            style={{
              width: '100%',
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '2px',
              padding: '12px',
              color: '#e8e8e8',
              fontSize: '11px',
            }}
          />
        )}

        <button
          onClick={handleParse}
          disabled={!input.trim() || parseMutation.isPending}
          style={{
            background: input.trim() ? '#22c55e' : '#1a1a1a',
            color: input.trim() ? '#000' : '#444',
            border: 'none',
            borderRadius: '2px',
            padding: '10px 20px',
            fontSize: '11px',
            fontWeight: '500',
            letterSpacing: '0.08em',
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            marginTop: '12px',
          }}
        >
          {parseMutation.isPending ? 'PARSING...' : 'PARSE RECIPE'}
        </button>
      </div>

      {/* Error Display */}
      {parseMutation.isError && (
        <div className="card" style={{ 
          padding: '20px', 
          marginBottom: '24px', 
          borderColor: '#f87171' 
        }}>
          <div style={{ fontSize: '11px', color: '#f87171' }}>
            Error parsing recipe. Please try again or use a different format.
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="fade-in">
          {/* Summary Card */}
          <div className="card" style={{ 
            padding: '20px', 
            marginBottom: '24px',
            borderColor: result.can_make ? '#22c55e' : '#fbbf24'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              marginBottom: '12px'
            }}>
              <div>
                <div style={{ 
                  fontSize: '16px', 
                  fontWeight: '500', 
                  color: '#fff',
                  marginBottom: '4px'
                }}>
                  {result.recipe_name}
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {result.ingredients.length} ingredients total
                </div>
              </div>
              <div style={{ fontSize: '32px' }}>
                {result.can_make ? '✅' : '⚠️'}
              </div>
            </div>

            <div style={{ 
              fontSize: '11px', 
              color: result.can_make ? '#22c55e' : '#fbbf24',
              letterSpacing: '0.05em'
            }}>
              {result.can_make 
                ? '✓ You have everything needed!' 
                : `Missing ${result.missing_items.length} item${result.missing_items.length !== 1 ? 's' : ''}`
              }
            </div>
          </div>

          {/* Available Items */}
          {result.available_items.length > 0 && (
            <div className="card" style={{ padding: '20px', marginBottom: '16px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: '#22c55e', 
                letterSpacing: '0.1em',
                marginBottom: '12px'
              }}>
                ✓ HAVE ({result.available_items.length})
              </div>
              <div style={{ 
                display: 'flex', 
                flexWrap: 'wrap', 
                gap: '8px' 
              }}>
                {result.available_items.map((item, i) => (
                  <span
                    key={i}
                    className="badge"
                    style={{ 
                      background: '#1a2e1a', 
                      color: '#22c55e',
                      border: '1px solid #22c55e'
                    }}
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing Items */}
          {result.missing_items.length > 0 && (
            <div className="card" style={{ 
              padding: '20px', 
              marginBottom: '16px',
              borderColor: '#fbbf24'
            }}>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '12px'
              }}>
                <div style={{ 
                  fontSize: '10px', 
                  color: '#fbbf24', 
                  letterSpacing: '0.1em'
                }}>
                  ✗ NEED ({result.missing_items.length})
                </div>
                <button
                  onClick={handleShopNow}
                  style={{
                    background: '#fbbf24',
                    color: '#000',
                    border: 'none',
                    borderRadius: '2px',
                    padding: '6px 12px',
                    fontSize: '10px',
                    fontWeight: '500',
                    letterSpacing: '0.08em',
                    cursor: 'pointer',
                  }}
                >
                  SHOP NOW →
                </button>
              </div>
              <div style={{ 
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: '8px'
              }}>
                {result.missing_items.map((item, i) => (
                  <div
                    key={i}
                    style={{
                      background: '#1a1a1a',
                      border: '1px solid #2a2a2a',
                      borderRadius: '2px',
                      padding: '12px',
                    }}
                  >
                    <div style={{ fontSize: '11px', color: '#fff', marginBottom: '4px' }}>
                      {item.name}
                    </div>
                    {item.quantity && (
                      <div style={{ fontSize: '10px', color: '#666' }}>
                        {item.quantity} {item.unit || 'units'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      {!result && !parseMutation.isPending && (
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '11px', color: '#666', lineHeight: '1.6' }}>
            <div style={{ marginBottom: '12px', color: '#888' }}>
              <strong>How it works:</strong>
            </div>
            <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
              <li style={{ marginBottom: '6px' }}>
                <strong>Dish Name:</strong> Enter "Butter Chicken" - AI generates ingredient list
              </li>
              <li style={{ marginBottom: '6px' }}>
                <strong>Recipe URL:</strong> Paste link from any cooking website
              </li>
              <li style={{ marginBottom: '6px' }}>
                <strong>Paste Recipe:</strong> Copy full recipe text from anywhere
              </li>
            </ul>
            <div style={{ marginTop: '12px', color: '#888' }}>
              We'll check your fridge and pantry to see what's available!
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
