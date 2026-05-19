import { useState, useEffect, useRef, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const REC_STYLE = {
  "STRONG BUY": { bg: "rgba(22,163,74,0.12)",  color: "#16a34a", border: "rgba(22,163,74,0.3)",  dot: "#16a34a" },
  "BUY":        { bg: "rgba(37,99,235,0.1)",   color: "#2563eb", border: "rgba(37,99,235,0.3)",  dot: "#2563eb" },
  "HOLD":       { bg: "rgba(217,119,6,0.1)",   color: "#d97706", border: "rgba(217,119,6,0.3)",  dot: "#d97706" },
  "SELL":       { bg: "rgba(220,38,38,0.1)",   color: "#dc2626", border: "rgba(220,38,38,0.3)",  dot: "#dc2626" },
};

const FILTERS = ["All", "Strong Buy", "Buy", "In Watchlist"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function ScoreBar({ score }) {
  const pct   = Math.min(Math.max(((score + 2) / 10) * 100, 2), 100);
  const color = score >= 6 ? "#16a34a" : score >= 3 ? "#2563eb" : score >= 0 ? "#d97706" : "#dc2626";
  return (
    <div style={{ width: 60, height: 4, background: "#f0f0ec", borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.4s ease" }}/>
    </div>
  );
}

function RecBadge({ rec }) {
  const s = REC_STYLE[rec] || REC_STYLE["HOLD"];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 10px", borderRadius: 20,
      background: s.bg, color: s.color,
      border: `1px solid ${s.border}`,
      fontSize: 10, fontWeight: 700,
      fontFamily: "var(--mono)", letterSpacing: "0.05em",
      whiteSpace: "nowrap",
    }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: s.dot }}/>
      {rec}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Detail Drawer
// ---------------------------------------------------------------------------
function DetailDrawer({ result, onClose }) {
  if (!result) return null;
  const s = REC_STYLE[result.recommendation] || REC_STYLE["HOLD"];

  const MetaRow = ({ label, value, positive, negative }) => {
    const isPos = positive?.(value);
    const isNeg = negative?.(value);
    const valColor = isPos ? "#16a34a" : isNeg ? "#dc2626" : "var(--text-primary)";
    return (
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "10px 0", borderBottom: "1px solid var(--border)",
      }}>
        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 600, fontFamily: "var(--mono)", color: valColor }}>
          {value ?? "—"}
        </span>
      </div>
    );
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0,
          background: "rgba(0,0,0,0.3)",
          zIndex: 40,
        }}
      />
      {/* Drawer */}
      <div style={{
        position: "fixed", top: 0, right: 0,
        width: 400, height: "100vh",
        background: "var(--surface)",
        borderLeft: "1px solid var(--border)",
        zIndex: 50, overflowY: "auto",
        display: "flex", flexDirection: "column",
      }} className="animate-fade-in">
        {/* Header */}
        <div style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--border)",
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <span style={{ fontFamily: "var(--mono)", fontSize: 18, fontWeight: 700 }}>
                {result.symbol}
              </span>
              {result.in_watchlist && (
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 20,
                  background: "rgba(37,99,235,0.1)", color: "#2563eb",
                  border: "1px solid rgba(37,99,235,0.2)", letterSpacing: "0.06em",
                }}>
                  WATCHLIST
                </span>
              )}
            </div>
            <RecBadge rec={result.recommendation}/>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: 18, color: "var(--text-muted)", padding: 4,
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Price + Score hero */}
        <div style={{
          margin: 20,
          padding: 20,
          background: s.bg,
          border: `1px solid ${s.border}`,
          borderRadius: 12,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
            <div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>Latest Close</div>
              <div style={{ fontFamily: "var(--mono)", fontSize: 28, fontWeight: 700, color: "var(--text-primary)" }}>
                ₹{result.latest_close?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6 }}>Signal Score</div>
              <div style={{ fontFamily: "var(--mono)", fontSize: 22, fontWeight: 700, color: s.color }}>
                {result.score}
                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>/10</span>
              </div>
            </div>
          </div>
          <div style={{ marginTop: 12, height: 6, background: "rgba(0,0,0,0.08)", borderRadius: 6, overflow: "hidden" }}>
            <div style={{
              width: `${Math.min(Math.max(((result.score + 2) / 10) * 100, 2), 100)}%`,
              height: "100%", background: s.color, borderRadius: 6,
            }}/>
          </div>
        </div>

        {/* Detail rows */}
        <div style={{ padding: "0 24px 24px" }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 4 }}>
            Momentum
          </div>
          <MetaRow label="RSI (14)" value={result.rsi?.toFixed(1)}
            positive={(v) => parseFloat(v) < 30}
            negative={(v) => parseFloat(v) > 70}
          />
          <MetaRow label="5-day Momentum"
            value={result.momentum_5d != null ? `${result.momentum_5d > 0 ? "+" : ""}${result.momentum_5d?.toFixed(2)}%` : null}
            positive={(v) => v?.startsWith("+")}
            negative={(v) => v?.startsWith("-")}
          />
          <MetaRow label="MA Trend"
            value={result.ma_trend === "bull" ? "Bullish ↑" : "Bearish ↓"}
            positive={(v) => v?.startsWith("Bull")}
            negative={(v) => v?.startsWith("Bear")}
          />
          <MetaRow label="MACD Trend"
            value={result.macd_trend === "bull" ? "Bullish ↑" : "Bearish ↓"}
            positive={(v) => v?.startsWith("Bull")}
            negative={(v) => v?.startsWith("Bear")}
          />

          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", margin: "16px 0 4px" }}>
            Volume & Breakout
          </div>
          <MetaRow label="Volume Spike"
            value={result.volume_spike ? "Yes — above 1.5× avg" : "No"}
            positive={(v) => v?.startsWith("Yes")}
          />
          <MetaRow label="20-day Breakout"
            value={result.breakout ? "Yes — new high" : "No"}
            positive={(v) => v?.startsWith("Yes")}
          />

          {result.scanned_at && (
            <div style={{ marginTop: 20, fontSize: 11, color: "var(--text-muted)", textAlign: "center" }}>
              Scanned at {new Date(result.scanned_at).toLocaleString("en-IN")}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Notification Bell
// ---------------------------------------------------------------------------
function NotifBell({ count, results, onSelect }) {
  const [open, setOpen] = useState(false);
  const bullish = results.filter((r) => ["STRONG BUY", "BUY"].includes(r.recommendation));

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          position: "relative", background: "var(--surface)",
          border: "1px solid var(--border)", borderRadius: 10,
          padding: "8px 12px", cursor: "pointer",
          display: "flex", alignItems: "center", gap: 6,
          fontSize: 13, color: "var(--text-secondary)",
          transition: "all 0.15s",
        }}
        onMouseEnter={(e) => e.currentTarget.style.borderColor = "#2563eb"}
        onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border)"}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2a4.5 4.5 0 00-4.5 4.5v2l-1 2h11l-1-2V6.5A4.5 4.5 0 008 2z" stroke="currentColor" strokeWidth="1.4"/>
          <path d="M6.5 12.5a1.5 1.5 0 003 0" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
        </svg>
        Signals
        {count > 0 && (
          <span style={{
            background: "#16a34a", color: "#fff",
            borderRadius: 20, fontSize: 10, fontWeight: 700,
            padding: "1px 6px", fontFamily: "var(--mono)",
          }}>
            {count}
          </span>
        )}
      </button>

      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 29 }}/>
          <div style={{
            position: "absolute", top: "calc(100% + 8px)", right: 0,
            width: 320, maxHeight: 400, overflowY: "auto",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12, zIndex: 30,
            boxShadow: "0 8px 24px rgba(0,0,0,0.1)",
          }} className="animate-fade-in">
            <div style={{
              padding: "12px 16px",
              borderBottom: "1px solid var(--border)",
              fontSize: 11, fontWeight: 700,
              letterSpacing: "0.08em", textTransform: "uppercase",
              color: "var(--text-muted)",
            }}>
              {bullish.length} Bullish signal{bullish.length !== 1 ? "s" : ""}
            </div>
            {bullish.length === 0 ? (
              <div style={{ padding: "24px 16px", textAlign: "center", fontSize: 12, color: "var(--text-muted)" }}>
                No bullish signals yet — run a scan first.
              </div>
            ) : (
              bullish.map((r) => (
                <button
                  key={r.symbol}
                  onClick={() => { onSelect(r); setOpen(false); }}
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    width: "100%", padding: "10px 16px",
                    background: "none", border: "none",
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer", textAlign: "left",
                    transition: "background 0.1s",
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface-2)"}
                  onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                >
                  <div>
                    <div style={{ fontFamily: "var(--mono)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 3 }}>
                      {r.symbol}
                      {r.in_watchlist && (
                        <span style={{ marginLeft: 6, fontSize: 9, color: "#2563eb", fontWeight: 700 }}>★ WL</span>
                      )}
                    </div>
                    <RecBadge rec={r.recommendation}/>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontFamily: "var(--mono)", fontSize: 13, fontWeight: 600 }}>
                      ₹{r.latest_close?.toLocaleString("en-IN")}
                    </div>
                    <div style={{ fontSize: 11, color: r.momentum_5d >= 0 ? "#16a34a" : "#dc2626", fontFamily: "var(--mono)" }}>
                      {r.momentum_5d >= 0 ? "+" : ""}{r.momentum_5d?.toFixed(2)}%
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ScanPage
// ---------------------------------------------------------------------------
export default function ScanPage() {
  const [results, setResults]       = useState([]);
  const [scanning, setScanning]     = useState(false);
  const [progress, setProgress]     = useState({ done: 0, total: 0 });
  const [summary, setSummary]       = useState(null);   // final "done" event payload
  const [filter, setFilter]         = useState("All");
  const [scope, setScope]           = useState("nifty50");
  const [selected, setSelected]     = useState(null);   // for detail drawer
  const [lastScan, setLastScan]     = useState(null);
  const esRef = useRef(null);

  // Load last scan results on mount
  useEffect(() => {
    const token = localStorage.getItem("sa_token");
    if (!token) return;
    fetch("/api/scan/results", { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.results?.length) {
          setResults(data.results);
          setLastScan(data.scanned_at);
        }
      })
      .catch(() => {});
  }, []);

  const startScan = useCallback(() => {
    if (scanning) return;
    const token = localStorage.getItem("sa_token");
    if (!token) return;

    // Close any previous stream
    if (esRef.current) { esRef.current.close(); }

    setResults([]);
    setSummary(null);
    setScanning(true);
    setProgress({ done: 0, total: scope === "nifty50" ? 50 : 100 });

    const url = `/api/scan/stream?scope=${scope}`;

    // Use fetch+ReadableStream instead of EventSource so we can pass JWT
    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream",
      },
    }).then(async (response) => {
      if (!response.ok) { setScanning(false); return; }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "progress") {
              const r = event.data;
              setResults((prev) => {
                // Insert in score-descending order
                const next = [...prev, r].sort((a, b) => b.score - a.score);
                return next;
              });
              setProgress((p) => ({ ...p, done: p.done + 1 }));
            } else if (event.type === "done") {
              setSummary(event.data);
              setLastScan(new Date().toISOString());
              setScanning(false);
            }
          } catch { /* malformed event — skip */ }
        }
      }
      setScanning(false);
    }).catch(() => setScanning(false));
  }, [scanning, scope]);

  // Filtered results
  const filtered = results.filter((r) => {
    if (filter === "Strong Buy")  return r.recommendation === "STRONG BUY";
    if (filter === "Buy")         return r.recommendation === "BUY";
    if (filter === "In Watchlist") return r.in_watchlist;
    return true;
  });

  const bullishCount = results.filter((r) => ["STRONG BUY", "BUY"].includes(r.recommendation)).length;

  return (
    <div style={{ maxWidth: 960 }}>
      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Scope selector */}
          <div style={{
            display: "flex", background: "var(--surface)",
            border: "1px solid var(--border)", borderRadius: 10, padding: 3,
          }}>
            {[{ v: "nifty50", l: "Nifty 50" }, { v: "nifty100", l: "Nifty 100" }].map(({ v, l }) => (
              <button key={v} onClick={() => !scanning && setScope(v)}
                style={{
                  padding: "6px 14px", borderRadius: 8, border: "none",
                  background: scope === v ? "var(--text-primary)" : "transparent",
                  color: scope === v ? "#fff" : "var(--text-secondary)",
                  fontSize: 12, fontWeight: scope === v ? 600 : 400,
                  cursor: scanning ? "not-allowed" : "pointer",
                  transition: "all 0.15s", fontFamily: "var(--sans)",
                }}
              >
                {l}
              </button>
            ))}
          </div>

          {/* Run scan button */}
          <button
            onClick={startScan}
            disabled={scanning}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "9px 20px",
              background: scanning ? "var(--surface-3)" : "var(--text-primary)",
              border: "none", borderRadius: 10,
              color: scanning ? "var(--text-secondary)" : "#fff",
              fontSize: 13, fontWeight: 600,
              cursor: scanning ? "not-allowed" : "pointer",
              transition: "all 0.15s", fontFamily: "var(--sans)",
            }}
          >
            {scanning ? (
              <>
                <div style={{
                  width: 12, height: 12, border: "2px solid var(--border-strong)",
                  borderTopColor: "var(--blue)", borderRadius: "50%",
                }} className="animate-spin-slow"/>
                Scanning {progress.done}/{progress.total}
              </>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M7 4.5v5M4.5 7h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
                </svg>
                Run Scan
              </>
            )}
          </button>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {lastScan && !scanning && (
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--mono)" }}>
              Last scan: {new Date(lastScan).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
          <NotifBell count={bullishCount} results={results} onSelect={setSelected}/>
        </div>
      </div>

      {/* Progress bar */}
      {scanning && (
        <div style={{ marginBottom: 16, height: 3, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            height: "100%", background: "#16a34a", borderRadius: 3,
            width: `${progress.total > 0 ? (progress.done / progress.total) * 100 : 0}%`,
            transition: "width 0.3s ease",
          }}/>
        </div>
      )}

      {/* Summary strip */}
      {summary && !scanning && (
        <div style={{
          marginBottom: 16, padding: "10px 16px",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          display: "flex", alignItems: "center", gap: 20,
          fontSize: 12, color: "var(--text-secondary)",
          flexWrap: "wrap",
        }} className="animate-fade-in">
          <span>✓ Scan complete in <b style={{ fontFamily: "var(--mono)", color: "var(--text-primary)" }}>{summary.duration_s}s</b></span>
          <span><b style={{ fontFamily: "var(--mono)", color: "#16a34a" }}>{summary.bullish}</b> bullish signals out of <b style={{ fontFamily: "var(--mono)" }}>{summary.completed}</b> stocks</span>
          {results.filter((r) => r.in_watchlist && ["STRONG BUY","BUY"].includes(r.recommendation)).length > 0 && (
            <span style={{ color: "#2563eb", fontWeight: 600 }}>
              ★ {results.filter((r) => r.in_watchlist && ["STRONG BUY","BUY"].includes(r.recommendation)).length} watchlist stocks showing bullish signals
            </span>
          )}
        </div>
      )}

      {/* Filter bar */}
      {results.length > 0 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 14, flexWrap: "wrap" }}>
          {FILTERS.map((f) => {
            const count =
              f === "All"          ? results.length :
              f === "Strong Buy"   ? results.filter((r) => r.recommendation === "STRONG BUY").length :
              f === "Buy"          ? results.filter((r) => r.recommendation === "BUY").length :
              results.filter((r) => r.in_watchlist).length;
            return (
              <button key={f} onClick={() => setFilter(f)}
                style={{
                  padding: "5px 14px", borderRadius: 20,
                  border: `1px solid ${filter === f ? "var(--text-primary)" : "var(--border)"}`,
                  background: filter === f ? "var(--text-primary)" : "var(--surface)",
                  color: filter === f ? "#fff" : "var(--text-secondary)",
                  fontSize: 12, cursor: "pointer",
                  transition: "all 0.15s", fontFamily: "var(--sans)",
                  display: "flex", alignItems: "center", gap: 6,
                }}
              >
                {f}
                <span style={{
                  fontSize: 10, fontFamily: "var(--mono)",
                  background: filter === f ? "rgba(255,255,255,0.2)" : "var(--surface-3)",
                  padding: "1px 5px", borderRadius: 10,
                }}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Results table */}
      {filtered.length > 0 ? (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12, overflow: "hidden",
        }}>
          {/* Table header */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 80px 90px 80px 70px 60px 90px",
            padding: "8px 20px",
            background: "var(--surface-2)",
            borderBottom: "1px solid var(--border)",
            fontSize: 10, fontWeight: 700,
            letterSpacing: "0.08em", textTransform: "uppercase",
            color: "var(--text-muted)",
          }}>
            <span>Symbol</span>
            <span>Score</span>
            <span>Signal</span>
            <span style={{ textAlign: "right" }}>Price</span>
            <span style={{ textAlign: "right" }}>RSI</span>
            <span style={{ textAlign: "center" }}>Momo</span>
            <span style={{ textAlign: "right" }}>5d %</span>
          </div>

          {/* Rows */}
          {filtered.map((r) => (
            <div
              key={r.symbol}
              onClick={() => setSelected(r)}
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 80px 90px 80px 70px 60px 90px",
                padding: "12px 20px",
                borderBottom: "1px solid var(--border)",
                cursor: "pointer",
                transition: "background 0.1s",
                alignItems: "center",
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface-2)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontFamily: "var(--mono)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  {r.symbol.replace(".NS", "")}
                </span>
                {r.in_watchlist && (
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: "2px 6px", borderRadius: 10,
                    background: "rgba(37,99,235,0.1)", color: "#2563eb",
                    border: "1px solid rgba(37,99,235,0.2)",
                  }}>
                    WL
                  </span>
                )}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <span style={{ fontFamily: "var(--mono)", fontSize: 12, fontWeight: 600 }}>{r.score}</span>
                <ScoreBar score={r.score}/>
              </div>
              <div><RecBadge rec={r.recommendation}/></div>
              <div style={{ fontFamily: "var(--mono)", fontSize: 12, textAlign: "right", color: "var(--text-primary)" }}>
                ₹{r.latest_close?.toLocaleString("en-IN")}
              </div>
              <div style={{
                fontFamily: "var(--mono)", fontSize: 12, textAlign: "right",
                color: r.rsi < 30 ? "#16a34a" : r.rsi > 70 ? "#dc2626" : "var(--text-secondary)",
                fontWeight: r.rsi < 30 || r.rsi > 70 ? 700 : 400,
              }}>
                {r.rsi?.toFixed(1)}
              </div>
              <div style={{ display: "flex", justifyContent: "center", gap: 4 }}>
                {r.volume_spike && (
                  <span title="Volume spike" style={{ fontSize: 12 }}>⚡</span>
                )}
                {r.breakout && (
                  <span title="20-day breakout" style={{ fontSize: 12 }}>🔼</span>
                )}
              </div>
              <div style={{
                fontFamily: "var(--mono)", fontSize: 12, textAlign: "right", fontWeight: 600,
                color: r.momentum_5d >= 0 ? "#16a34a" : "#dc2626",
              }}>
                {r.momentum_5d >= 0 ? "+" : ""}{r.momentum_5d?.toFixed(2)}%
              </div>
            </div>
          ))}
        </div>
      ) : !scanning && (
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 12, padding: "64px 0", textAlign: "center",
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📡</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>
            No scan results yet
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Select a scope and click Run Scan — results stream in as each stock completes.
          </div>
        </div>
      )}

      {/* Detail drawer */}
      <DetailDrawer result={selected} onClose={() => setSelected(null)}/>
    </div>
  );
}
