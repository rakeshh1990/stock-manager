import { useState, useEffect } from "react";
import axios from "axios";
import client from "../api/client";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";

// ---------------------------------------------------------------------------
// Market chart panel (right side — no auth needed)
// ---------------------------------------------------------------------------

function MarketPanel() {
  const [data, setData]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);

  useEffect(() => {
    // Call the public gateway endpoint — no JWT required
    axios.get("/api/market/snapshot", { params: { symbol: "^NSEI", period: "1y" } })
      .then((res) => {
        // Sample down to ~60 points so the chart stays clean
        const raw = res.data;
        const step = Math.max(1, Math.floor(raw.length / 60));
        const sampled = raw.filter((_, i) => i % step === 0 || i === raw.length - 1);
        setData(sampled);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const latest  = data.length ? data[data.length - 1] : null;
  const first   = data.length ? data[0] : null;
  const change  = first && latest ? ((latest.close - first.close) / first.close) * 100 : null;
  const isUp    = change !== null && change >= 0;

  // Format x-axis — show month abbreviation
  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", { month: "short" });
  };

  const formatPrice = (v) =>
    v >= 1000
      ? `₹${(v / 1000).toFixed(1)}k`
      : `₹${v}`;

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const pt = payload[0].payload;
    return (
      <div style={{
        background: "#1a1d2e",
        border: "1px solid #2e3348",
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: 11,
        fontFamily: "var(--mono)",
      }}>
        <div style={{ color: "#8a90ab", marginBottom: 2 }}>{pt.date}</div>
        <div style={{ color: "#fff", fontWeight: 600 }}>₹{pt.close?.toLocaleString("en-IN")}</div>
      </div>
    );
  };

  return (
    <div style={{
      width: 420,
      background: "#0a0d14",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "48px 36px",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Subtle grid background */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: "linear-gradient(rgba(22,163,74,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(22,163,74,0.04) 1px, transparent 1px)",
        backgroundSize: "40px 40px",
        pointerEvents: "none",
      }}/>

      <div style={{ position: "relative", width: "100%", textAlign: "center" }}>
        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ color: "#3a3f58", fontSize: 10, fontFamily: "var(--mono)", letterSpacing: "0.12em", marginBottom: 8 }}>
            NIFTY 50 · 1Y
          </div>
          {loading ? (
            <div style={{ height: 56, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{
                width: 20, height: 20,
                border: "2px solid #1e2130",
                borderTopColor: "#16a34a",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}/>
            </div>
          ) : error ? (
            <div style={{ color: "#4a4f6a", fontSize: 12, fontFamily: "var(--mono)" }}>
              Market data unavailable
            </div>
          ) : (
            <>
              <div style={{
                color: "#ffffff",
                fontFamily: "var(--mono)",
                fontSize: 34,
                fontWeight: 600,
                letterSpacing: "-0.02em",
              }}>
                {latest?.close?.toLocaleString("en-IN")}
              </div>
              <div style={{
                marginTop: 6,
                fontSize: 13,
                fontFamily: "var(--mono)",
                color: isUp ? "var(--accent)" : "var(--danger)",
              }}>
                {isUp ? "▲" : "▼"} {Math.abs(change).toFixed(2)}% past year
              </div>
            </>
          )}
        </div>

        {/* Chart */}
        {!loading && !error && data.length > 0 && (
          <div style={{ width: "100%", height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="niftyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor={isUp ? "#16a34a" : "#dc2626"} stopOpacity={0.25}/>
                    <stop offset="100%" stopColor={isUp ? "#16a34a" : "#dc2626"} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.04)"
                  vertical={false}
                />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={{ fontSize: 10, fill: "#3a3f58", fontFamily: "var(--mono)" }}
                  axisLine={false}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tickFormatter={formatPrice}
                  tick={{ fontSize: 10, fill: "#3a3f58", fontFamily: "var(--mono)" }}
                  axisLine={false}
                  tickLine={false}
                  width={52}
                  domain={["auto", "auto"]}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#2e3348", strokeWidth: 1 }}/>
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={isUp ? "#16a34a" : "#dc2626"}
                  strokeWidth={2}
                  fill="url(#niftyGrad)"
                  dot={false}
                  activeDot={{ r: 4, fill: isUp ? "#16a34a" : "#dc2626", strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Footer note */}
        {!loading && !error && (
          <div style={{
            marginTop: 20,
            fontSize: 10,
            color: "#2e3348",
            fontFamily: "var(--mono)",
          }}>
            Data via Yahoo Finance · updates on login
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login / Register form (left side)
// ---------------------------------------------------------------------------

export default function LoginPage({ onLogin }) {
  const [mode, setMode]         = useState("login");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [registered, setRegistered] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await client.post("/auth/register", { email, password });
        setRegistered(true);
        setMode("login");
      } else {
        const res = await client.post("/auth/login", { email, password });
        const token = res.data.access_token;
        localStorage.setItem("sa_token", token);
        localStorage.setItem("sa_email", email);
        onLogin(token, email);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--sidebar-bg)" }}>
      {/* Left — form */}
      <div style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 48,
        borderRight: "1px solid var(--sidebar-border)",
      }}>
        <div style={{ maxWidth: 420, width: "100%" }} className="animate-fade-up">
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <div style={{
              width: 40, height: 40, background: "var(--accent)",
              borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
                <path d="M2 12l3-5 3 3 3-6 3 4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span style={{ color: "#fff", fontSize: 18, fontWeight: 600 }}>StockAlert</span>
          </div>

          <h1 style={{
            fontFamily: "var(--display)", fontSize: 32, fontWeight: 600,
            color: "#ffffff", margin: "0 0 8px", lineHeight: 1.2,
          }}>
            {mode === "login" ? "Welcome back" : "Create account"}
          </h1>
          <p style={{ color: "#6b7191", fontSize: 14, margin: "0 0 32px" }}>
            {mode === "login"
              ? "Sign in to your investment dashboard"
              : "Start tracking your investments today"}
          </p>

          {/* Tab toggle */}
          <div style={{
            display: "flex", background: "#1a1d2e",
            borderRadius: 10, padding: 3, marginBottom: 24,
            border: "1px solid var(--sidebar-border)",
          }}>
            {["login", "register"].map((m) => (
              <button key={m}
                onClick={() => { setMode(m); setError(""); setRegistered(false); }}
                style={{
                  flex: 1, padding: "8px 0", borderRadius: 8, border: "none",
                  background: mode === m ? "#fff" : "transparent",
                  color: mode === m ? "var(--text-primary)" : "#6b7191",
                  fontSize: 13, fontWeight: mode === m ? 600 : 400,
                  cursor: "pointer", transition: "all 0.15s", fontFamily: "var(--sans)",
                }}
              >
                {m === "login" ? "Sign in" : "Register"}
              </button>
            ))}
          </div>

          {registered && (
            <div style={{
              marginBottom: 16, padding: "10px 14px",
              background: "rgba(22,163,74,0.1)", border: "1px solid rgba(22,163,74,0.3)",
              borderRadius: 8, fontSize: 13, color: "#4ade80",
            }}>
              Account created — sign in to continue.
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[
              { label: "Email address", type: "email",    value: email,    setter: setEmail,    placeholder: "you@example.com" },
              { label: "Password",      type: "password", value: password, setter: setPassword, placeholder: "••••••••" },
            ].map(({ label, type, value, setter, placeholder }) => (
              <div key={label}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#8a90ab", marginBottom: 6 }}>
                  {label}
                </label>
                <input
                  type={type} required value={value}
                  onChange={(e) => setter(e.target.value)}
                  placeholder={placeholder}
                  style={{
                    width: "100%", padding: "10px 14px",
                    background: "#1a1d2e", border: "1px solid var(--sidebar-border)",
                    borderRadius: 8, color: "#e8eaf6", fontSize: 14, outline: "none",
                    fontFamily: type === "email" ? "var(--mono)" : "var(--sans)",
                    transition: "border-color 0.15s", boxSizing: "border-box",
                  }}
                  onFocus={(e) => e.target.style.borderColor = "var(--accent)"}
                  onBlur={(e) => e.target.style.borderColor = "var(--sidebar-border)"}
                />
              </div>
            ))}

            {error && (
              <div style={{
                padding: "10px 14px",
                background: "rgba(220,38,38,0.1)", border: "1px solid rgba(220,38,38,0.3)",
                borderRadius: 8, fontSize: 13, color: "#f87171",
              }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{
              padding: "11px", background: loading ? "#0f5e2a" : "var(--accent)",
              border: "none", borderRadius: 8, color: "#fff",
              fontSize: 14, fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.15s", fontFamily: "var(--sans)",
            }}>
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>

      {/* Right — live market chart */}
      <MarketPanel />
    </div>
  );
}
