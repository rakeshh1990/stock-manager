import { useState, useEffect } from "react";
import client from "../api/client";

export default function PortfolioPage() {
  const [symbols, setSymbols] = useState([]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [toast, setToast]     = useState(null);

  const showToast = (type, text) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    client.get("/portfolio")
      .then((res) => setSymbols(res.data.symbols || []))
      .catch(() => showToast("error", "Failed to load portfolio"))
      .finally(() => setLoading(false));
  }, []);

  const addSymbol = () => {
    const sym = input.trim().toUpperCase();
    if (!sym) return;
    if (symbols.includes(sym)) { showToast("error", `${sym} already in portfolio`); return; }
    setSymbols((p) => [...p, sym]);
    setInput("");
  };

  const removeSymbol = (sym) => setSymbols((p) => p.filter((s) => s !== sym));

  const save = async () => {
    setSaving(true);
    try {
      await client.post("/portfolio", { symbols });
      showToast("success", "Portfolio saved");
    } catch {
      showToast("error", "Failed to save portfolio");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "0 0 24px" }}>
        Your invested symbols. These feed the alert scheduler once it's wired up in Phase 2.
      </p>

      {toast && (
        <div style={{
          marginBottom: 16, padding: "10px 16px",
          background: toast.type === "success" ? "var(--accent-light)" : "var(--danger-light)",
          border: `1px solid ${toast.type === "success" ? "#86efac" : "#fca5a5"}`,
          borderRadius: 8, fontSize: 13,
          color: toast.type === "success" ? "var(--accent-text)" : "var(--danger-text)",
          display: "flex", justifyContent: "space-between",
        }}>
          {toast.text}
          <button onClick={() => setToast(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.6 }}>✕</button>
        </div>
      )}

      {/* Add symbol */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSymbol()}
          placeholder="Add symbol — e.g. TCS.NS"
          style={{
            flex: 1, padding: "10px 14px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, fontSize: 13, color: "var(--text-primary)",
            outline: "none", fontFamily: "var(--mono)",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => e.target.style.borderColor = "var(--blue)"}
          onBlur={(e) => e.target.style.borderColor = "var(--border)"}
        />
        <button
          onClick={addSymbol}
          style={{
            padding: "10px 20px",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 10, fontSize: 13, fontWeight: 500,
            color: "var(--text-primary)", cursor: "pointer",
            transition: "all 0.15s", fontFamily: "var(--sans)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--blue)"; e.currentTarget.style.color = "var(--blue)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-primary)"; }}
        >
          Add
        </button>
      </div>

      {/* Symbol list */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12, overflow: "hidden",
        marginBottom: 16,
      }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)", fontSize: 13 }}>
            Loading…
          </div>
        ) : symbols.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 0" }}>
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No symbols yet</div>
            <div style={{ fontSize: 12, color: "var(--border-strong)", marginTop: 4 }}>Add one above to get started</div>
          </div>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
            {symbols.map((sym, i) => (
              <li
                key={sym}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "13px 20px",
                  borderBottom: i < symbols.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: "var(--surface-3)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, fontWeight: 700, color: "var(--text-secondary)",
                    fontFamily: "var(--mono)",
                  }}>
                    {sym.replace(".NS", "").slice(0, 3)}
                  </div>
                  <span style={{ fontFamily: "var(--mono)", fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>
                    {sym}
                  </span>
                </div>
                <button
                  onClick={() => removeSymbol(sym)}
                  style={{
                    background: "none", border: "none", cursor: "pointer",
                    fontSize: 12, color: "var(--text-muted)",
                    padding: "4px 8px", borderRadius: 6,
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "var(--danger-light)"; e.currentTarget.style.color = "var(--danger)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "none"; e.currentTarget.style.color = "var(--text-muted)"; }}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          {symbols.length} symbol{symbols.length !== 1 ? "s" : ""}
        </span>
        <button
          onClick={save}
          disabled={saving || loading}
          style={{
            padding: "10px 28px",
            background: "var(--text-primary)", border: "none",
            borderRadius: 10, color: "#fff",
            fontSize: 13, fontWeight: 600,
            cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.6 : 1,
            transition: "opacity 0.15s",
            fontFamily: "var(--sans)",
          }}
        >
          {saving ? "Saving…" : "Save portfolio"}
        </button>
      </div>
    </div>
  );
}
