'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

type ParseMode = 'url' | 'text' | 'dish';

type Stage =
  | 'idle'
  | 'parsing'
  | 'parsed'
  | 'confirm_lebowski'
  | 'sending_to_lebowski'
  | 'cart_ready'
  | 'error';

interface IngredientItem {
  name: string;
  original_name?: string;
  quantity?: number;
  unit?: string;
  notes?: string;
  optional?: boolean;
}

interface RecipeResult {
  dish: string;
  servings?: number;
  total_ingredients: number;
  available: string[];
  missing: IngredientItem[];
  source_type?: string;
}

interface CartItem {
  query: string;
  matched: string | null;
  sku?: string;
  price?: number;
  quantity?: number;
  total_price?: number;
  pack_size?: string;
  error?: string;
}

interface CartResult {
  matched_items: CartItem[];
  total_cost: number;
  successfully_matched?: number;
  total_items?: number;
  subtotal?: number;
  delivery_fee?: number;
  total?: number;
}

export default function RecipeParser() {
  const [mode, setMode] = useState<ParseMode>('dish');
  const [input, setInput] = useState('');
  const [servings, setServings] = useState<string>('');
  const [stage, setStage] = useState<Stage>('idle');
  const [recipeResult, setRecipeResult] = useState<RecipeResult | null>(null);
  const [cartResult, setCartResult] = useState<CartResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Step 1: Parse recipe
  // Step 1: Parse via direct /recipes/parse — no LLM router overhead
  const parseMutation = useMutation({
    mutationFn: async () => {
      const servingsNum = servings ? parseInt(servings, 10) : undefined;
      return alfredClient.parseRecipe(input.trim(), mode, servingsNum || undefined);
    },
    onSuccess: (data) => {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      // data.result is the dict returned by Remy (has 'dish', 'missing', 'available')
      const result = data.result;

      if (!result || (data.error && typeof result === 'string')) {
        setErrorMsg(typeof result === 'string' ? result : (data.error || 'Something went wrong.'));
        setStage('error');
        return;
      }

      if (typeof result === 'object' && result !== null && 'dish' in result) {
        setRecipeResult(result as RecipeResult);
        setStage('parsed');
      } else if (typeof result === 'string') {
        setErrorMsg(result);
        setStage('error');
      } else {
        setErrorMsg('Got an unexpected response — try again.');
        setStage('error');
      }
    },
    onError: (err: unknown) => {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      const isTimeout = (err as { code?: string })?.code === 'ECONNABORTED';
      setErrorMsg(
        isTimeout
          ? 'Took too long — try again, or paste the ingredients directly.'
          : 'Could not reach the server. Is Alfred running?'
      );
      setStage('error');
    },
  });

  // Step 2: Build cart via Lebowski
  const cartMutation = useMutation({
    mutationFn: async (items: IngredientItem[]) =>
      alfredClient.buildCart(
        items.map((i) => ({ name: i.name, quantity: i.quantity, unit: i.unit }))
      ),
    onSuccess: (data) => {
      // /build_cart returns { response: result, result: result }
      const raw = (data as { response?: unknown; result?: unknown });
      const result = raw.response ?? raw.result ?? data;
      if (result && typeof result === 'object' && 'matched_items' in (result as object)) {
        setCartResult(result as CartResult);
        setStage('cart_ready');
      } else {
        setErrorMsg(typeof result === 'string' ? result : 'Cart build failed — try again.');
        setStage('error');
      }
    },
    onError: () => {
      setErrorMsg('Lebowski is having trouble. Try again in a moment.');
      setStage('error');
    },
  });

  const handleParse = () => {
    if (!input.trim()) return;
    setStage('parsing');
    setRecipeResult(null);
    setCartResult(null);
    setErrorMsg('');
    setElapsed(0);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    parseMutation.mutate();
  };

  const handleSendToLebowski = () => {
    if (!recipeResult?.missing?.length) return;
    setStage('sending_to_lebowski');
    cartMutation.mutate(recipeResult.missing);
  };

  const handleReset = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setStage('idle');
    setInput('');
    setServings('');
    setRecipeResult(null);
    setCartResult(null);
    setErrorMsg('');
    setElapsed(0);
  };

  const handlePlaceOrder = () => {
    if (!cartResult) return;
    window.dispatchEvent(
      new CustomEvent('build-cart', {
        detail: {
          items: cartResult.matched_items
            .filter((i) => i.matched)
            .map((i) => ({ name: i.matched, quantity: i.quantity })),
        },
      })
    );
  };

  // ── Styles ────────────────────────────────────────────────────────────────
  const card: React.CSSProperties = {
    background: '#111',
    border: '1px solid #1e1e1e',
    borderRadius: '4px',
    padding: '20px',
    marginBottom: '20px',
  };
  const label: React.CSSProperties = {
    fontSize: '10px',
    color: '#666',
    letterSpacing: '0.1em',
    marginBottom: '10px',
    display: 'block',
  };
  const input_style: React.CSSProperties = {
    width: '100%',
    background: '#0a0a0a',
    border: '1px solid #1e1e1e',
    borderRadius: '2px',
    padding: '10px 12px',
    color: '#e8e8e8',
    fontSize: '12px',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  };
  const btn = (active = true, color = '#fff'): React.CSSProperties => ({
    background: active ? color : '#1a1a1a',
    color: active ? '#000' : '#444',
    border: 'none',
    borderRadius: '2px',
    padding: '9px 18px',
    fontSize: '11px',
    fontWeight: '500',
    letterSpacing: '0.07em',
    cursor: active ? 'pointer' : 'not-allowed',
  });

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="fade-in" style={{ maxWidth: '720px' }}>

      {/* ── Input card (always shown) ── */}
      <div style={card}>
        {/* Mode tabs */}
        <span style={label}>INPUT METHOD</span>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '16px' }}>
          {(['dish', 'url', 'text'] as ParseMode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setInput(''); }}
              style={{
                ...btn(mode === m),
                background: mode === m ? '#fff' : '#1a1a1a',
                color: mode === m ? '#000' : '#666',
                padding: '7px 14px',
              }}
            >
              {m === 'dish' ? 'DISH NAME' : m === 'url' ? 'RECIPE URL' : 'PASTE RECIPE'}
            </button>
          ))}
        </div>

        {/* Input */}
        {mode === 'text' ? (
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste the full recipe here..."
            style={{ ...input_style, minHeight: '160px', resize: 'vertical', marginBottom: '12px' }}
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
                : 'Butter Chicken, Paneer Tikka, Pasta Carbonara...'
            }
            style={{ ...input_style, marginBottom: '12px' }}
          />
        )}

        {/* Servings row */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '14px' }}>
          <span style={{ ...label, margin: 0, whiteSpace: 'nowrap' }}>SERVINGS</span>
          <input
            type="number"
            min={1}
            max={50}
            value={servings}
            onChange={(e) => setServings(e.target.value)}
            placeholder="Default"
            style={{ ...input_style, width: '100px' }}
          />
          <span style={{ fontSize: '11px', color: '#444' }}>
            leave blank to use recipe default
          </span>
        </div>

        {/* Parse button */}
        <button
          onClick={handleParse}
          disabled={!input.trim() || stage === 'parsing'}
          style={btn(!!input.trim() && stage !== 'parsing', '#22c55e')}
        >
          {stage === 'parsing' ? 'PARSING...' : 'PARSE RECIPE'}
        </button>
      </div>

      {/* ── Loading state ── */}
      {stage === 'parsing' && (
        <div style={{ ...card, borderColor: '#22c55e22' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '18px', height: '18px', borderRadius: '50%', flexShrink: 0,
              border: '2px solid #1a2e1a', borderTopColor: '#22c55e',
              animation: 'spin 0.9s linear infinite',
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '12px', color: '#e8e8e8', marginBottom: '4px' }}>
                {elapsed < 5
                  ? (mode === 'url' ? 'Fetching recipe page...' : mode === 'text' ? 'Reading ingredients...' : 'Generating ingredient list...')
                  : elapsed < 20
                  ? 'Running LLM extraction...'
                  : elapsed < 50
                  ? 'Still working — local models take a moment...'
                  : 'Almost there (or set LLM_PROVIDER=claude for 5s results)...'}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ flex: 1, height: '2px', background: '#1a1a1a', borderRadius: '1px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', background: '#22c55e', borderRadius: '1px',
                    width: `${Math.min((elapsed / 90) * 100, 95)}%`,
                    transition: 'width 1s linear',
                  }} />
                </div>
                <span style={{ fontSize: '10px', color: '#555', flexShrink: 0 }}>{elapsed}s</span>
              </div>
            </div>
          </div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* ── Error ── */}
      {stage === 'error' && (
        <div style={{ ...card, borderColor: '#ef4444' }}>
          <span style={{ ...label, color: '#ef4444' }}>SOMETHING WENT WRONG</span>
          <p style={{ fontSize: '13px', color: '#e8e8e8', margin: '0 0 14px' }}>{errorMsg}</p>
          <button onClick={handleReset} style={btn(true)}>TRY AGAIN</button>
        </div>
      )}

      {/* ── Recipe result ── */}
      {(stage === 'parsed' || stage === 'confirm_lebowski' || stage === 'sending_to_lebowski') && recipeResult && (
        <div className="fade-in">
          {/* Header card */}
          <div style={{
            ...card,
            borderColor: recipeResult.missing.length === 0 ? '#22c55e' : '#fbbf24',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '17px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
                  {recipeResult.dish}
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {recipeResult.total_ingredients} ingredients
                  {recipeResult.servings ? ` · ${recipeResult.servings} servings` : ''}
                </div>
              </div>
              <span style={{ fontSize: '28px' }}>
                {recipeResult.missing.length === 0 ? '✅' : '🛒'}
              </span>
            </div>
          </div>

          {/* Have */}
          {recipeResult.available.length > 0 && (
            <div style={{ ...card }}>
              <span style={{ ...label, color: '#22c55e' }}>
                ✓ HAVE ({recipeResult.available.length})
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {recipeResult.available.map((name, i) => (
                  <span key={i} style={{
                    background: '#0d1f0d',
                    border: '1px solid #22c55e33',
                    borderRadius: '2px',
                    padding: '4px 10px',
                    fontSize: '11px',
                    color: '#22c55e',
                  }}>
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing + Lebowski CTA */}
          {recipeResult.missing.length > 0 && (
            <div style={{ ...card, borderColor: '#fbbf24' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span style={{ ...label, color: '#fbbf24', margin: 0 }}>
                  ✗ NEED TO BUY ({recipeResult.missing.length})
                </span>
                <button
                  onClick={handleSendToLebowski}
                  disabled={stage === 'sending_to_lebowski'}
                  style={btn(stage !== 'sending_to_lebowski', '#fbbf24')}
                >
                  {stage === 'sending_to_lebowski'
                    ? 'BUILDING CART...'
                    : 'ORDER ON SWIGGY →'}
                </button>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                gap: '8px',
              }}>
                {recipeResult.missing.map((item, i) => (
                  <div key={i} style={{
                    background: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                    borderRadius: '2px',
                    padding: '10px 12px',
                  }}>
                    <div style={{ fontSize: '12px', color: '#fff', marginBottom: '3px' }}>
                      {item.name}
                      {item.optional && (
                        <span style={{ color: '#666', fontSize: '10px', marginLeft: '6px' }}>optional</span>
                      )}
                    </div>
                    {item.quantity && (
                      <div style={{ fontSize: '10px', color: '#555' }}>
                        {item.quantity} {item.unit || ''}
                        {item.notes && ` · ${item.notes}`}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {recipeResult.missing.length === 0 && (
            <div style={{ ...card, borderColor: '#22c55e', textAlign: 'center' }}>
              <p style={{ fontSize: '14px', color: '#22c55e', margin: 0 }}>
                🎉 You have everything to make {recipeResult.dish}!
              </p>
            </div>
          )}

          <button onClick={handleReset} style={{ ...btn(true), background: '#1a1a1a', color: '#666', marginTop: '4px' }}>
            ← PARSE ANOTHER
          </button>
        </div>
      )}

      {/* ── Cart result ── */}
      {stage === 'cart_ready' && cartResult && (
        <div className="fade-in">
          <div style={{ ...card, borderColor: '#6366f1' }}>
            <span style={{ ...label, color: '#6366f1' }}>SWIGGY CART READY</span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>
                  ₹{cartResult.total || cartResult.total_cost}
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  {cartResult.successfully_matched ?? cartResult.matched_items?.filter(i => i.matched).length ?? 0} items matched
                  {cartResult.delivery_fee != null && ` · ₹${cartResult.delivery_fee} delivery`}
                </div>
              </div>
              <button onClick={handlePlaceOrder} style={btn(true, '#6366f1')}>
                PLACE ORDER
              </button>
            </div>

            {cartResult.matched_items?.map((item, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 0',
                borderTop: '1px solid #1a1a1a',
                fontSize: '12px',
              }}>
                <span style={{ color: item.matched ? '#e8e8e8' : '#666' }}>
                  {item.matched || <i>{item.query} (not found)</i>}
                  {item.pack_size && (
                    <span style={{ color: '#444', marginLeft: '8px', fontSize: '10px' }}>
                      {item.pack_size}
                    </span>
                  )}
                </span>
                <span style={{ color: item.matched ? '#22c55e' : '#444' }}>
                  {item.matched ? `₹${item.total_price}` : '—'}
                </span>
              </div>
            ))}
          </div>

          <button onClick={handleReset} style={{ ...btn(true), background: '#1a1a1a', color: '#666' }}>
            ← PARSE ANOTHER
          </button>
        </div>
      )}

      {/* ── Empty state ── */}
      {stage === 'idle' && (
        <div style={{ ...card, borderStyle: 'dashed' }}>
          <span style={{ ...label }}>HOW IT WORKS</span>
          <p style={{ fontSize: '12px', color: '#555', lineHeight: 1.7, margin: 0 }}>
            <strong style={{ color: '#888' }}>Dish name</strong> — type "Paneer Butter Masala" and Remy generates the ingredient list from its knowledge.<br />
            <strong style={{ color: '#888' }}>Recipe URL</strong> — paste any recipe blog link; Remy scrapes and extracts ingredients.<br />
            <strong style={{ color: '#888' }}>Paste recipe</strong> — copy-paste the full recipe text.<br /><br />
            Remy checks your fridge and pantry first. Missing items can be sent straight to Swiggy Instamart via Lebowski.
          </p>
        </div>
      )}
    </div>
  );
}
