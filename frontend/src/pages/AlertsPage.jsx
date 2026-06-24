import { useEffect, useState } from "react";
import client from "../api/client";

const CONDITIONS = [
  ["PRICE_ABOVE", "Price above"],
  ["PRICE_BELOW", "Price below"],
  ["RSI_ABOVE", "RSI above"],
  ["RSI_BELOW", "RSI below"],
  ["MOMENTUM_NEG", "Negative momentum"],
  ["SCORE_DROP", "Score at or below"],
  ["EXIT_SIGNAL", "Exit signal"],
];

const field = {
  padding: "9px 11px", border: "1px solid var(--border-strong)",
  borderRadius: 8, background: "var(--surface)", fontSize: 13,
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [form, setForm] = useState({
    symbol: "", condition_type: "PRICE_ABOVE", threshold: "", cooldown_hours: 24,
  });
  const [error, setError] = useState("");

  const load = () => client.get("/alerts").then((r) => setAlerts(r.data));
  useEffect(() => { load().catch(() => setError("Could not load alerts.")); }, []);

  const needsThreshold = form.condition_type !== "EXIT_SIGNAL";
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await client.post("/alerts", {
        ...form,
        symbol: form.symbol.trim().toUpperCase(),
        threshold: needsThreshold ? Number(form.threshold) : null,
        cooldown_hours: Number(form.cooldown_hours),
      });
      setForm((current) => ({ ...current, symbol: "", threshold: "" }));
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create alert.");
    }
  };

  const toggle = async (id) => { await client.patch(`/alerts/${id}/toggle`); await load(); };
  const remove = async (id) => { await client.delete(`/alerts/${id}`); await load(); };

  return (
    <div style={{ maxWidth: 980 }}>
      <form onSubmit={submit} style={{
        display: "grid", gridTemplateColumns: "1fr 1.4fr 1fr 110px auto",
        gap: 10, padding: 16, background: "var(--surface)",
        border: "1px solid var(--border)", borderRadius: 12, marginBottom: 20,
      }}>
        <input style={field} value={form.symbol} required placeholder="Symbol (INFY)"
          onChange={(e) => setForm({ ...form, symbol: e.target.value })}/>
        <select style={field} value={form.condition_type}
          onChange={(e) => setForm({ ...form, condition_type: e.target.value })}>
          {CONDITIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <input style={field} type="number" step="0.01" required={needsThreshold}
          disabled={!needsThreshold} placeholder={needsThreshold ? "Threshold" : "Not required"}
          value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })}/>
        <input style={field} type="number" min="0" max="720" title="Cooldown hours"
          value={form.cooldown_hours} onChange={(e) => setForm({ ...form, cooldown_hours: e.target.value })}/>
        <button style={{
          border: 0, borderRadius: 8, background: "var(--text-primary)",
          color: "#fff", padding: "0 18px", fontWeight: 600, cursor: "pointer",
        }}>Create</button>
      </form>

      {error && <div style={{ color: "var(--danger)", fontSize: 12, marginBottom: 12 }}>{error}</div>}

      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {alerts.length === 0 ? (
          <div style={{ padding: 56, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            No alerts yet. Create one above and the scheduled scanner will watch it.
          </div>
        ) : alerts.map((alert) => (
          <div key={alert.id} style={{
            display: "grid", gridTemplateColumns: "1fr 1.4fr 1fr 100px 130px",
            alignItems: "center", padding: "14px 18px", borderBottom: "1px solid var(--border)",
          }}>
            <strong style={{ fontFamily: "var(--mono)", fontSize: 13 }}>{alert.symbol}</strong>
            <span style={{ fontSize: 12 }}>{alert.condition_type.replaceAll("_", " ")}</span>
            <span style={{ fontFamily: "var(--mono)", fontSize: 12 }}>
              {alert.threshold ?? "Automatic"}
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{alert.cooldown_hours}h cooldown</span>
            <div style={{ display: "flex", gap: 7, justifyContent: "flex-end" }}>
              <button onClick={() => toggle(alert.id)} style={{
                ...field, padding: "5px 9px", cursor: "pointer",
                color: alert.active === "Y" ? "var(--accent-text)" : "var(--text-muted)",
              }}>{alert.active === "Y" ? "Active" : "Paused"}</button>
              <button onClick={() => remove(alert.id)} style={{
                ...field, padding: "5px 9px", cursor: "pointer", color: "var(--danger)",
              }}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}