import { useState } from "react";
import client from "../api/client";

const REC_STYLE = {
  "STRONG BUY": { bg: "rgba(22,163,74,0.12)", color: "var(--accent)", border: "rgba(22,163,74,0.3)" },
  "BUY":        { bg: "rgba(37,99,235,0.1)",  color: "var(--blue)",   border: "rgba(37,99,235,0.3)" },
  "HOLD":       { bg: "rgba(217,119,6,0.1)",  color: "var(--warning)",border: "rgba(217,119,6,0.3)" },
  "SELL":       { bg: "rgba(220,38,38,0.1)",  color: "var(--danger)", border: "rgba(220,38,38,0.3)" },
};

function Chip({ value, positive, negative, neutral }) {
  const isPos = positive?.(value);
  const isNeg = negative?.(value);
  const style = isPos
    ? { background: "var(--accent-light)", color: "var(--accent-text)" }
    : isNeg
    ? { background: "var(--danger-light)", color: "var(--danger-text)" }
    : { background: "var(--surface-3)", color: "var(--text-secondary)" };
  return (
    <span style={{
      ...style, fontSize: 11, fontWeight: 600,
      padding: "2px 8px", borderRadius: 20,
      fontFamily: "var(--mono)",
    }}>
      {value}
    </span>
  );
}

function Row({ label, children }) {
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "10px 0",
      borderBottom: "1px solid var(--border)",
    }}>
      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 500, fontFamily: "var(--mono)", color: "var(--text-primary)" }}>
        {children}
      </span>
    </div>
  );
}

function Card({ title, children }) {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "20px 24px",
    }}>
      {title && (
        <div style={{
          fontSize: 11, fontWeight: 600, letterSpacing: "0.08em",
          textTransform: "uppercase", color: "var(--text-muted)",
          marginBottom: 12,
        }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
}

function ScoreBar({ score }) {
  const pct   = Math.min(Math.max(((score + 2) / 10) * 100, 3), 100);
  const color = score >= 4 ? "var(--accent)" : score >= 2 ? "var(--blue)" : score >= 0 ? "var(--warning)" : "var(--danger)";
  return (
    <div style={{ marginTop: 4 }}>
      <div style={{ height: 4, background: "var(--surface-3)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.6s ease" }}/>
      </div>
    </div>
  );
}

export default function AnalysePage() {
  const [symbol, setSymbol]   = useState("");
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleAnalyse = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;
    setError(""); setLoading(true); setData(null);
    try {
      const res = await client.get("/analyse", { params: { symbol: symbol.trim().toUpperCase() } });
      setData(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : `No data found for "${symbol}"`);
    } finally {
      setLoading(false);
    }
  };

  const rec = data ? REC_STYLE[data.recommendation] ?? REC_STYLE["HOLD"] : null;

  return (
    <div style={{ maxWidth: 760 }}>
      {/* Search */}
      <form onSubmit={handleAnalyse} style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter NSE symbol — e.g. INFY.NS, HDFCBANK.NS"
          style={{
            flex: 1, padding: "11px 16px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, fontSize: 14, color: "var(--text-primary)",
            outline: "none", fontFamily: "var(--mono)",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => e.target.style.borderColor = "var(--blue)"}
          onBlur={(e) => e.target.style.borderColor = "var(--border)"}
        />
        <button
          type="submit"
          disabled={loading || !symbol.trim()}
          style={{
            padding: "11px 24px",
            background: "var(--text-primary)", border: "none",
            borderRadius: 10, color: "#fff",
            fontSize: 13, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
            opacity: loading || !symbol.trim() ? 0.5 : 1,
            transition: "opacity 0.15s",
            fontFamily: "var(--sans)",
          }}
        >
          {loading ? "Analysing…" : "Analyse →"}
        </button>
      </form>

      {error && (
        <div style={{
          marginBottom: 20, padding: "12px 16px",
          background: "var(--danger-light)", border: "1px solid #fca5a5",
          borderRadius: 10, fontSize: 13, color: "var(--danger-text)",
        }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: "center", padding: "60px 0" }}>
          <div style={{
            width: 28, height: 28, border: "2px solid var(--border)",
            borderTopColor: "var(--blue)", borderRadius: "50%",
            margin: "0 auto 12px",
          }} className="animate-spin-slow"/>
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Fetching market data…</div>
        </div>
      )}

      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }} className="animate-fade-up">
          {/* Hero card */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: "24px 28px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 22, fontWeight: 600, color: "var(--text-primary)" }}>
                  {data.symbol}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3, fontFamily: "var(--mono)" }}>
                  As of {data.date}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontFamily: "var(--mono)", fontSize: 28, fontWeight: 600, color: "var(--text-primary)" }}>
                  ₹{data.latest_close?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </div>
                <div style={{
                  display: "inline-block", marginTop: 6,
                  padding: "4px 14px", borderRadius: 20,
                  background: rec.bg, color: rec.color,
                  border: `1px solid ${rec.border}`,
                  fontSize: 11, fontWeight: 700, letterSpacing: "0.05em",
                  fontFamily: "var(--mono)",
                }}>
                  {data.recommendation}
                </div>
              </div>
            </div>

            <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Signal Score</span>
                <span style={{ fontSize: 11, fontFamily: "var(--mono)", color: "var(--text-secondary)" }}>
                  {data.score} / 10
                </span>
              </div>
              <ScoreBar score={data.score}/>
            </div>

            {data.note && (
              <div style={{
                marginTop: 14, padding: "8px 12px",
                background: "var(--surface-3)", borderRadius: 8,
                fontSize: 12, color: "var(--text-secondary)",
                fontStyle: "italic",
              }}>
                {data.note}
              </div>
            )}
          </div>

          {/* 2-col grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="Momentum & Trend">
              <Row label="5-day momentum">
                <Chip
                  value={`${data.momentum_5d_pct > 0 ? "+" : ""}${data.momentum_5d_pct?.toFixed(2)}%`}
                  positive={(v) => v.startsWith("+")}
                  negative={(v) => v.startsWith("-")}
                />
              </Row>
              <Row label="MA 50">₹{data.ma50 ?? "—"}</Row>
              <Row label="MA 200">₹{data.ma200 ?? "—"}</Row>
              <Row label="MA Trend">
                <Chip
                  value={data.ma_trend === "bull" ? "Bullish" : data.ma_trend === "bear" ? "Bearish" : "Neutral"}
                  positive={(v) => v === "Bullish"}
                  negative={(v) => v === "Bearish"}
                />
              </Row>
            </Card>

            <Card title="Oscillators">
              <Row label="RSI (14)">
                <Chip
                  value={data.rsi?.toFixed(1)}
                  positive={(v) => parseFloat(v) < 30}
                  negative={(v) => parseFloat(v) > 70}
                />
              </Row>
              <Row label="MACD">{data.macd?.toFixed(4) ?? "—"}</Row>
              <Row label="Signal">{data.macd_signal?.toFixed(4) ?? "—"}</Row>
              <Row label="MACD Trend">
                <Chip
                  value={data.macd_trend === "bull" ? "Bullish" : data.macd_trend === "bear" ? "Bearish" : "Neutral"}
                  positive={(v) => v === "Bullish"}
                  negative={(v) => v === "Bearish"}
                />
              </Row>
            </Card>

            <Card title="52-Week Range">
              <Row label="% from 52w High">
                <Chip value={`${data.pct_from_52w_high?.toFixed(2)}%`} negative={() => data.near_52w_high}/>
              </Row>
              <Row label="% from 52w Low">
                <Chip value={`${data.pct_from_52w_low?.toFixed(2)}%`} positive={() => data.near_52w_low}/>
              </Row>
              <Row label="Near 52w High">
                <Chip value={data.near_52w_high ? "Yes" : "No"} negative={(v) => v === "Yes"}/>
              </Row>
              <Row label="Near 52w Low">
                <Chip value={data.near_52w_low ? "Yes" : "No"} positive={(v) => v === "Yes"}/>
              </Row>
            </Card>

            <Card title="Volume & Breakout">
              <Row label="Avg Vol (20d)">{data.avg_volume_20?.toLocaleString("en-IN") ?? "—"}</Row>
              <Row label="Recent Volume">{data.recent_volume?.toLocaleString("en-IN") ?? "—"}</Row>
              <Row label="Volume Spike">
                <Chip value={data.volume_spike ? "Yes" : "No"} positive={(v) => v === "Yes"}/>
              </Row>
              <Row label="Breakout Confirmed">
                <Chip value={data.breakout_confirmed ? "Yes" : "No"} positive={(v) => v === "Yes"}/>
              </Row>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
