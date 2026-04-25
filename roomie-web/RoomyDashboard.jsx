import { useState, useEffect } from "react";

const MOCK = {
  alfred: "online",
  agents: {
    elsa: {
      healthy: true,
      summary: "14 items tracked. 3 low stock.",
      total_items: 14,
      low_stock_count: 3,
      low_stock_items: ["milk", "eggs", "curd"],
    },
  },
  pending_confirmations: 1,
};

const MOCK_INVENTORY = [
  { name: "Milk", quantity: 0.5, unit: "liters", category: "dairy", low_stock_threshold: 1 },
  { name: "Eggs", quantity: 2, unit: "units", category: "dairy", low_stock_threshold: 4 },
  { name: "Curd", quantity: 100, unit: "grams", category: "dairy", low_stock_threshold: 200 },
  { name: "Butter", quantity: 150, unit: "grams", category: "dairy", low_stock_threshold: null },
  { name: "Orange Juice", quantity: 1.2, unit: "liters", category: "beverages", low_stock_threshold: null },
  { name: "Tomatoes", quantity: 4, unit: "units", category: "produce", low_stock_threshold: 2 },
  { name: "Spinach", quantity: 200, unit: "grams", category: "produce", low_stock_threshold: null },
  { name: "Chicken", quantity: 500, unit: "grams", category: "meat", low_stock_threshold: null },
  { name: "Leftover Dal", quantity: 1, unit: "units", category: "leftovers", low_stock_threshold: null },
  { name: "Soy Sauce", quantity: 0.8, unit: "units", category: "condiments", low_stock_threshold: null },
];

const MOCK_EVENTS = [
  { time: "09:14", agent: "elsa", type: "inventory_update", detail: "Added 1L milk" },
  { time: "09:32", agent: "alfred", type: "order_confirmed", detail: "InstaMart order ₹312 confirmed" },
  { time: "11:05", agent: "elsa", type: "low_stock_alert", detail: "Eggs running low (2 left)" },
  { time: "13:22", agent: "elsa", type: "recipe_parsed", detail: "Pasta → 2 items missing" },
  { time: "15:47", agent: "alfred", type: "order_suggested", detail: "Cart of 3 items ready" },
];

const MOCK_ANALYTICS = {
  total_orders: 12,
  total_spent: 4280,
  avg_order: 357,
  savings_vs_retail: 640,
  most_ordered: "Milk",
  orders_this_month: 4,
};

function isLow(item) {
  return item.low_stock_threshold !== null && item.quantity <= item.low_stock_threshold;
}

function stockPercent(item) {
  if (!item.low_stock_threshold) return 100;
  return Math.min(100, Math.round((item.quantity / (item.low_stock_threshold * 2)) * 100));
}

const CATEGORY_COLORS = {
  dairy: "#e2e8f0",
  produce: "#a3e635",
  meat: "#f87171",
  beverages: "#60a5fa",
  condiments: "#fbbf24",
  leftovers: "#a78bfa",
  snacks: "#fb923c",
};

export default function App() {
  const [tab, setTab] = useState("overview");
  const [time, setTime] = useState(new Date());
  const [pendingVisible, setPendingVisible] = useState(true);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const lowItems = MOCK_INVENTORY.filter(isLow);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080808",
      color: "#e8e8e8",
      fontFamily: "'DM Mono', 'Courier New', monospace",
      padding: "0",
      boxSizing: "border-box",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
        .tab-btn { background: none; border: none; cursor: pointer; transition: all 0.15s; }
        .tab-btn:hover { color: #fff !important; }
        .card { background: #111; border: 1px solid #1e1e1e; border-radius: 2px; }
        .card:hover { border-color: #2a2a2a; }
        .badge { display: inline-block; padding: 2px 8px; font-size: 10px; letter-spacing: 0.1em; border-radius: 1px; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        .fade-in { animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .bar-fill { transition: width 0.6s cubic-bezier(0.4,0,0.2,1); }
      `}</style>

      {/* ─── Header ─── */}
      <header style={{
        borderBottom: "1px solid #1a1a1a",
        padding: "0 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "56px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <span style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: "22px",
            letterSpacing: "0.15em",
            color: "#fff",
          }}>ROOMY</span>
          <span style={{ color: "#2a2a2a", fontSize: "12px" }}>|</span>
          <nav style={{ display: "flex", gap: "4px" }}>
            {["overview", "inventory", "analytics", "events"].map(t => (
              <button
                key={t}
                className="tab-btn"
                onClick={() => setTab(t)}
                style={{
                  color: tab === t ? "#fff" : "#444",
                  fontSize: "11px",
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  padding: "6px 12px",
                  borderBottom: tab === t ? "1px solid #fff" : "1px solid transparent",
                }}
              >{t}</button>
            ))}
          </nav>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <span style={{ fontSize: "10px", color: "#333", letterSpacing: "0.05em" }}>
            {time.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span className="pulse" style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
            <span style={{ fontSize: "10px", color: "#444", letterSpacing: "0.08em" }}>ALFRED ONLINE</span>
          </div>
        </div>
      </header>

      <main style={{ padding: "24px 32px", maxWidth: "1200px", margin: "0 auto" }}>

        {/* ─── Pending Confirmation Banner ─── */}
        {pendingVisible && MOCK.pending_confirmations > 0 && (
          <div className="fade-in" style={{
            background: "#111",
            border: "1px solid #2a2a2a",
            borderLeft: "3px solid #fff",
            padding: "12px 20px",
            marginBottom: "20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <span style={{ fontSize: "10px", color: "#555", letterSpacing: "0.1em" }}>PENDING APPROVAL</span>
              <p style={{ fontSize: "13px", color: "#e8e8e8", marginTop: "2px" }}>
                Order 3 items from InstaMart — ₹312 estimated
              </p>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button onClick={() => setPendingVisible(false)} style={{
                background: "#fff", color: "#000", border: "none",
                padding: "6px 16px", fontSize: "11px", letterSpacing: "0.08em",
                cursor: "pointer", fontFamily: "inherit",
              }}>CONFIRM</button>
              <button onClick={() => setPendingVisible(false)} style={{
                background: "none", color: "#555", border: "1px solid #222",
                padding: "6px 16px", fontSize: "11px", letterSpacing: "0.08em",
                cursor: "pointer", fontFamily: "inherit",
              }}>CANCEL</button>
            </div>
          </div>
        )}

        {/* ─── OVERVIEW TAB ─── */}
        {tab === "overview" && (
          <div className="fade-in">
            {/* Stat cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
              {[
                { label: "ITEMS TRACKED", value: MOCK.agents.elsa.total_items, sub: "by elsa" },
                { label: "LOW STOCK", value: MOCK.agents.elsa.low_stock_count, sub: "needs restock", alert: true },
                { label: "ORDERS THIS MONTH", value: MOCK_ANALYTICS.orders_this_month, sub: "via instamart" },
                { label: "SAVED VS RETAIL", value: `₹${MOCK_ANALYTICS.savings_vs_retail}`, sub: "this month" },
              ].map((s, i) => (
                <div key={i} className="card" style={{ padding: "18px 20px" }}>
                  <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "8px" }}>{s.label}</div>
                  <div style={{ fontSize: "28px", color: s.alert ? "#f87171" : "#fff", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "0.05em" }}>{s.value}</div>
                  <div style={{ fontSize: "10px", color: "#333", marginTop: "4px" }}>{s.sub}</div>
                </div>
              ))}
            </div>

            {/* Low stock + Events */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: "12px" }}>
              <div className="card" style={{ padding: "20px" }}>
                <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "16px" }}>LOW STOCK ALERTS</div>
                {lowItems.length === 0 ? (
                  <div style={{ fontSize: "12px", color: "#333" }}>All stocked up.</div>
                ) : lowItems.map((item, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                    <div>
                      <div style={{ fontSize: "12px", color: "#e8e8e8" }}>{item.name}</div>
                      <div style={{ fontSize: "10px", color: "#444" }}>{item.quantity} {item.unit} left</div>
                    </div>
                    <span className="badge" style={{ background: "#1a0a0a", color: "#f87171", border: "1px solid #3a1010" }}>LOW</span>
                  </div>
                ))}
              </div>

              <div className="card" style={{ padding: "20px" }}>
                <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "16px" }}>RECENT EVENTS</div>
                {MOCK_EVENTS.slice(0, 5).map((e, i) => (
                  <div key={i} style={{ display: "flex", gap: "12px", marginBottom: "12px", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "10px", color: "#333", width: "40px", flexShrink: 0 }}>{e.time}</span>
                    <div style={{
                      width: 6, height: 6, borderRadius: "50%", marginTop: "4px", flexShrink: 0,
                      background: e.agent === "alfred" ? "#e8e8e8" : "#555",
                    }} />
                    <div>
                      <div style={{ fontSize: "11px", color: "#e8e8e8" }}>{e.detail}</div>
                      <div style={{ fontSize: "10px", color: "#333" }}>{e.agent} · {e.type.replace(/_/g, " ")}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ─── INVENTORY TAB ─── */}
        {tab === "inventory" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <span style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em" }}>ELSA — FRIDGE INVENTORY</span>
              </div>
              <span style={{ fontSize: "10px", color: "#333" }}>{MOCK_INVENTORY.length} items</span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" }}>
              {MOCK_INVENTORY.map((item, i) => {
                const pct = stockPercent(item);
                const low = isLow(item);
                const catColor = CATEGORY_COLORS[item.category] || "#555";
                return (
                  <div key={i} className="card" style={{ padding: "14px 18px", borderLeft: `2px solid ${low ? "#f87171" : "#1e1e1e"}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{
                          width: 6, height: 6, borderRadius: "50%",
                          background: catColor, display: "inline-block", flexShrink: 0,
                        }} />
                        <span style={{ fontSize: "12px", color: "#e8e8e8" }}>{item.name}</span>
                      </div>
                      <span style={{ fontSize: "11px", color: low ? "#f87171" : "#888" }}>
                        {item.quantity} {item.unit}
                      </span>
                    </div>
                    {item.low_stock_threshold !== null && (
                      <div style={{ background: "#0a0a0a", height: "2px", borderRadius: "1px", overflow: "hidden" }}>
                        <div className="bar-fill" style={{
                          width: `${pct}%`, height: "100%",
                          background: low ? "#f87171" : "#2a2a2a",
                        }} />
                      </div>
                    )}
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px" }}>
                      <span style={{ fontSize: "9px", color: "#333", textTransform: "uppercase", letterSpacing: "0.08em" }}>{item.category}</span>
                      {low && <span style={{ fontSize: "9px", color: "#f87171", letterSpacing: "0.08em" }}>RESTOCK</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ─── ANALYTICS TAB ─── */}
        {tab === "analytics" && (
          <div className="fade-in">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "16px" }}>
              {[
                { label: "TOTAL SPENT", value: `₹${MOCK_ANALYTICS.total_spent.toLocaleString()}`, sub: "all time via roomy" },
                { label: "AVG ORDER VALUE", value: `₹${MOCK_ANALYTICS.avg_order}`, sub: "per instaMart order" },
                { label: "TOTAL ORDERS", value: MOCK_ANALYTICS.total_orders, sub: "placed by alfred" },
              ].map((s, i) => (
                <div key={i} className="card" style={{ padding: "20px" }}>
                  <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "8px" }}>{s.label}</div>
                  <div style={{ fontSize: "32px", fontFamily: "'Bebas Neue', sans-serif", color: "#fff", letterSpacing: "0.03em" }}>{s.value}</div>
                  <div style={{ fontSize: "10px", color: "#333", marginTop: "4px" }}>{s.sub}</div>
                </div>
              ))}
            </div>

            <div className="card" style={{ padding: "20px", marginBottom: "12px" }}>
              <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "16px" }}>SPEND — LAST 6 MONTHS</div>
              <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", height: "80px" }}>
                {[680, 920, 540, 1100, 760, 280].map((v, i) => {
                  const months = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr"];
                  const maxV = 1100;
                  return (
                    <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                      <span style={{ fontSize: "9px", color: "#555" }}>₹{v}</span>
                      <div style={{
                        width: "100%",
                        height: `${(v / maxV) * 60}px`,
                        background: i === 5 ? "#e8e8e8" : "#1e1e1e",
                        border: "1px solid #2a2a2a",
                      }} />
                      <span style={{ fontSize: "9px", color: "#333" }}>{months[i]}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card" style={{ padding: "20px" }}>
              <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "12px" }}>MOST ORDERED ITEMS</div>
              {[
                { name: "Milk", count: 8, pct: 80 },
                { name: "Eggs", count: 6, pct: 60 },
                { name: "Curd", count: 5, pct: 50 },
                { name: "Tomatoes", count: 3, pct: 30 },
              ].map((item, i) => (
                <div key={i} style={{ marginBottom: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ fontSize: "11px", color: "#e8e8e8" }}>{item.name}</span>
                    <span style={{ fontSize: "10px", color: "#444" }}>{item.count}x</span>
                  </div>
                  <div style={{ background: "#0a0a0a", height: "2px" }}>
                    <div style={{ width: `${item.pct}%`, height: "100%", background: "#2a2a2a" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── EVENTS TAB ─── */}
        {tab === "events" && (
          <div className="fade-in">
            <div style={{ fontSize: "9px", color: "#444", letterSpacing: "0.12em", marginBottom: "16px" }}>AGENT EVENT LOG — TODAY</div>
            <div className="card" style={{ padding: "0" }}>
              {MOCK_EVENTS.map((e, i) => (
                <div key={i} style={{
                  display: "flex", gap: "20px", padding: "14px 20px",
                  borderBottom: i < MOCK_EVENTS.length - 1 ? "1px solid #141414" : "none",
                  alignItems: "center",
                }}>
                  <span style={{ fontSize: "10px", color: "#333", width: "40px", flexShrink: 0 }}>{e.time}</span>
                  <span className="badge" style={{
                    background: e.agent === "alfred" ? "#1a1a1a" : "#0f0f0f",
                    color: e.agent === "alfred" ? "#888" : "#555",
                    border: `1px solid ${e.agent === "alfred" ? "#2a2a2a" : "#1a1a1a"}`,
                    width: "48px", textAlign: "center", flexShrink: 0,
                  }}>{e.agent}</span>
                  <span style={{ fontSize: "11px", color: "#e8e8e8", flex: 1 }}>{e.detail}</span>
                  <span style={{ fontSize: "9px", color: "#333", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                    {e.type.replace(/_/g, " ")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* ─── Footer ─── */}
      <footer style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        borderTop: "1px solid #111",
        background: "#080808",
        padding: "8px 32px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span style={{ fontSize: "9px", color: "#2a2a2a", letterSpacing: "0.1em" }}>
          PROJECT ROOMY v0.1.0 — LOCAL
        </span>
        <div style={{ display: "flex", gap: "16px" }}>
          <span style={{ fontSize: "9px", color: "#2a2a2a" }}>LLM: claude-haiku</span>
          <span style={{ fontSize: "9px", color: "#2a2a2a" }}>DB: sqlite</span>
          <span style={{ fontSize: "9px", color: "#2a2a2a" }}>AGENTS: 1 active</span>
        </div>
      </footer>
    </div>
  );
}
