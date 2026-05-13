import { useState, useEffect, useCallback } from "react";
import client from "../api/client";

function Toast({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div style={{
      marginBottom: 16, padding: "10px 16px",
      background: message.type === "success" ? "var(--accent-light)" : "var(--danger-light)",
      border: `1px solid ${message.type === "success" ? "#86efac" : "#fca5a5"}`,
      borderRadius: 8, fontSize: 13,
      color: message.type === "success" ? "var(--accent-text)" : "var(--danger-text)",
      display: "flex", justifyContent: "space-between", alignItems: "center",
    }}>
      {message.text}
      <button onClick={onDismiss} style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.6, fontSize: 12 }}>✕</button>
    </div>
  );
}

function AddItemForm({ watchlistId, onAdded }) {
  const [symbol, setSymbol]           = useState("");
  const [notes, setNotes]             = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [open, setOpen]               = useState(false);
  const [saving, setSaving]           = useState(false);
  const [error, setError]             = useState("");

  const reset = () => { setSymbol(""); setNotes(""); setTargetPrice(""); setError(""); setOpen(false); };

  const handleAdd = async () => {
    const sym = symbol.trim().toUpperCase();
    if (!sym) { setError("Symbol is required"); return; }
    setSaving(true); setError("");
    try {
      const payload = { symbol: sym };
      if (notes.trim()) payload.notes = notes.trim();
      if (targetPrice.trim()) payload.target_price = parseFloat(targetPrice);
      const res = await client.post(`/watchlists/${watchlistId}/items`, payload);
      onAdded(res.data);
      reset();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to add symbol");
    } finally {
      setSaving(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        style={{
          marginTop: 12, width: "100%", padding: "9px",
          background: "none",
          border: "1px dashed var(--border-strong)",
          borderRadius: 8, fontSize: 12,
          color: "var(--text-muted)", cursor: "pointer",
          transition: "all 0.15s", fontFamily: "var(--sans)",
        }}
        onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--blue)"; e.currentTarget.style.color = "var(--blue)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-strong)"; e.currentTarget.style.color = "var(--text-muted)"; }}
      >
        + Add symbol
      </button>
    );
  }

  return (
    <div style={{
      marginTop: 12, padding: 14,
      background: "var(--surface-2)",
      border: "1px solid var(--border)",
      borderRadius: 10,
    }}>
      {error && <p style={{ fontSize: 12, color: "var(--danger)", marginBottom: 10 }}>{error}</p>}
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input
          autoFocus value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="Symbol e.g. INFY.NS"
          style={{
            flex: 1, padding: "8px 12px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, fontSize: 13, outline: "none",
            color: "var(--text-primary)", fontFamily: "var(--mono)",
          }}
        />
        <input
          value={targetPrice}
          onChange={(e) => setTargetPrice(e.target.value)}
          placeholder="Target ₹" type="number" min="0"
          style={{
            width: 110, padding: "8px 12px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, fontSize: 13, outline: "none",
            color: "var(--text-primary)", fontFamily: "var(--mono)",
          }}
        />
      </div>
      <input
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notes — e.g. Waiting for RSI dip below 40"
        style={{
          width: "100%", padding: "8px 12px",
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 8, fontSize: 13, outline: "none",
          color: "var(--text-primary)", fontFamily: "var(--sans)",
          marginBottom: 10, boxSizing: "border-box",
        }}
      />
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button onClick={reset} style={{
          padding: "7px 14px", background: "none",
          border: "1px solid var(--border)", borderRadius: 8,
          fontSize: 12, color: "var(--text-secondary)", cursor: "pointer",
          fontFamily: "var(--sans)",
        }}>
          Cancel
        </button>
        <button onClick={handleAdd} disabled={saving} style={{
          padding: "7px 16px",
          background: "var(--text-primary)", border: "none",
          borderRadius: 8, fontSize: 12, fontWeight: 600,
          color: "#fff", cursor: saving ? "not-allowed" : "pointer",
          opacity: saving ? 0.6 : 1, fontFamily: "var(--sans)",
        }}>
          {saving ? "Adding…" : "Add"}
        </button>
      </div>
    </div>
  );
}

function WatchlistCard({ watchlist, onDeleted, onItemAdded, onItemRemoved }) {
  const [removing, setRemoving] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const handleRemoveItem = async (symbol) => {
    setRemoving(symbol);
    try {
      await client.delete(`/watchlists/${watchlist.id}/items/${symbol}`);
      onItemRemoved(watchlist.id, symbol);
    } finally { setRemoving(null); }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${watchlist.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await client.delete(`/watchlists/${watchlist.id}`);
      onDeleted(watchlist.id);
    } catch { setDeleting(false); }
  };

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12, overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 20px",
        borderBottom: expanded ? "1px solid var(--border)" : "none",
        cursor: "pointer",
      }}
        onClick={() => setExpanded((v) => !v)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: "var(--accent)",
          }}/>
          <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
            {watchlist.name}
          </span>
          <span style={{
            fontSize: 11, padding: "2px 8px", borderRadius: 20,
            background: "var(--surface-3)", color: "var(--text-secondary)",
            fontFamily: "var(--mono)",
          }}>
            {watchlist.items?.length ?? 0}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={(e) => { e.stopPropagation(); handleDelete(); }}
            disabled={deleting}
            style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: 11, color: "var(--text-muted)",
              padding: "4px 8px", borderRadius: 6,
              transition: "all 0.15s", fontFamily: "var(--sans)",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--danger)"; e.currentTarget.style.background = "var(--danger-light)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.background = "none"; }}
          >
            {deleting ? "Deleting…" : "Delete"}
          </button>
          <span style={{ color: "var(--text-muted)", fontSize: 12, userSelect: "none" }}>
            {expanded ? "▾" : "▸"}
          </span>
        </div>
      </div>

      {/* Items */}
      {expanded && (
        <div style={{ padding: "0 20px 16px" }}>
          {watchlist.items?.length === 0 ? (
            <p style={{ fontSize: 13, color: "var(--text-muted)", padding: "16px 0 4px", margin: 0 }}>
              No symbols yet.
            </p>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {watchlist.items.map((item, i) => (
                <li key={item.symbol} style={{
                  display: "flex", alignItems: "flex-start", justifyContent: "space-between",
                  padding: "10px 0",
                  borderBottom: i < watchlist.items.length - 1 ? "1px solid var(--border)" : "none",
                  gap: 12,
                }}>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontFamily: "var(--mono)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                        {item.symbol}
                      </span>
                      {item.target_price && (
                        <span style={{
                          fontSize: 10, padding: "2px 7px", borderRadius: 20,
                          background: "var(--blue-light)", color: "var(--blue-text)",
                          fontFamily: "var(--mono)", fontWeight: 500,
                        }}>
                          ₹{parseFloat(item.target_price).toLocaleString("en-IN")}
                        </span>
                      )}
                    </div>
                    {item.notes && (
                      <p style={{ margin: "3px 0 0", fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>
                        {item.notes}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleRemoveItem(item.symbol)}
                    disabled={removing === item.symbol}
                    style={{
                      background: "none", border: "none", cursor: "pointer",
                      fontSize: 11, color: "var(--text-muted)",
                      padding: "3px 8px", borderRadius: 6,
                      transition: "all 0.15s", flexShrink: 0, marginTop: 1,
                      fontFamily: "var(--sans)",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "var(--danger)"; e.currentTarget.style.background = "var(--danger-light)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.background = "none"; }}
                  >
                    {removing === item.symbol ? "…" : "Remove"}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <AddItemForm watchlistId={watchlist.id} onAdded={(item) => onItemAdded(watchlist.id, item)}/>
        </div>
      )}
    </div>
  );
}

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading]       = useState(true);
  const [newName, setNewName]       = useState("");
  const [creating, setCreating]     = useState(false);
  const [toast, setToast]           = useState(null);

  const showToast = (type, text) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 4000);
  };

  const loadWatchlists = useCallback(async () => {
    setLoading(true);
    try {
      const summaries = await client.get("/watchlists");
      const full = await Promise.all(
        summaries.data.map((wl) => client.get(`/watchlists/${wl.id}`).then((r) => r.data))
      );
      setWatchlists(full);
    } catch {
      showToast("error", "Failed to load watchlists");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadWatchlists(); }, [loadWatchlists]);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    try {
      const res = await client.post("/watchlists", { name });
      setWatchlists((p) => [...p, { ...res.data, items: [] }]);
      setNewName("");
      showToast("success", `"${name}" created`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      showToast("error", typeof detail === "string" ? detail : "Failed to create watchlist");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleted    = (id)           => { setWatchlists((p) => p.filter((wl) => wl.id !== id)); showToast("success", "Watchlist deleted"); };
  const handleItemAdded  = (wid, item)    => setWatchlists((p) => p.map((wl) => wl.id === wid ? { ...wl, items: [...(wl.items ?? []), item] } : wl));
  const handleItemRemoved= (wid, symbol)  => setWatchlists((p) => p.map((wl) => wl.id === wid ? { ...wl, items: (wl.items ?? []).filter((i) => i.symbol !== symbol) } : wl));

  return (
    <div style={{ maxWidth: 680 }}>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "0 0 24px" }}>
        Organise stocks you're monitoring. Add a target price — the alert engine will use it in Phase 2.
      </p>

      <Toast message={toast} onDismiss={() => setToast(null)}/>

      {/* Create */}
      <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          placeholder='New watchlist — e.g. "Midcap picks"'
          style={{
            flex: 1, padding: "10px 14px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, fontSize: 13, color: "var(--text-primary)",
            outline: "none", fontFamily: "var(--sans)",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => e.target.style.borderColor = "var(--blue)"}
          onBlur={(e) => e.target.style.borderColor = "var(--border)"}
        />
        <button
          onClick={handleCreate}
          disabled={creating || !newName.trim()}
          style={{
            padding: "10px 22px",
            background: "var(--text-primary)", border: "none",
            borderRadius: 10, color: "#fff",
            fontSize: 13, fontWeight: 600,
            cursor: creating || !newName.trim() ? "not-allowed" : "pointer",
            opacity: creating || !newName.trim() ? 0.5 : 1,
            transition: "opacity 0.15s", fontFamily: "var(--sans)",
          }}
        >
          {creating ? "Creating…" : "Create"}
        </button>
      </div>

      {/* Cards */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "60px 0" }}>
          <div style={{
            width: 24, height: 24, border: "2px solid var(--border)",
            borderTopColor: "var(--blue)", borderRadius: "50%",
            margin: "0 auto",
          }} className="animate-spin-slow"/>
        </div>
      ) : watchlists.length === 0 ? (
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 12, padding: "56px 0", textAlign: "center",
        }}>
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No watchlists yet</div>
          <div style={{ fontSize: 12, color: "var(--border-strong)", marginTop: 4 }}>Create one above to get started</div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }} className="animate-fade-up">
          {watchlists.map((wl) => (
            <WatchlistCard
              key={wl.id}
              watchlist={wl}
              onDeleted={handleDeleted}
              onItemAdded={handleItemAdded}
              onItemRemoved={handleItemRemoved}
            />
          ))}
        </div>
      )}
    </div>
  );
}
