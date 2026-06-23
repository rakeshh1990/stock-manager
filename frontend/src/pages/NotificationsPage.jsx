import { useEffect, useState } from "react";
import client from "../api/client";

export default function NotificationsPage({ onChanged }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = () => client.get("/notifications", { params: { unread: unreadOnly, limit: 100 } })
    .then((r) => setNotifications(r.data));

  useEffect(() => { load(); }, [unreadOnly]);

  const read = async (item) => {
    if (item.read === "N") await client.patch(`/notifications/${item.id}/read`);
    await load();
    onChanged?.();
  };

  const readAll = async () => {
    await client.patch("/notifications/read-all");
    await load();
    onChanged?.();
  };

  return (
    <div style={{ maxWidth: 860 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
        <label style={{ fontSize: 12, color: "var(--text-secondary)", display: "flex", gap: 7, alignItems: "center" }}>
          <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)}/>
          Unread only
        </label>
        <button onClick={readAll} style={{
          padding: "7px 12px", border: "1px solid var(--border-strong)",
          borderRadius: 8, background: "var(--surface)", cursor: "pointer", fontSize: 12,
        }}>Mark all read</button>
      </div>
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {notifications.length === 0 ? (
          <div style={{ padding: 56, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            You’re all caught up.
          </div>
        ) : notifications.map((item) => (
          <button key={item.id} onClick={() => read(item)} style={{
            width: "100%", textAlign: "left", border: 0, borderBottom: "1px solid var(--border)",
            background: item.read === "N" ? "rgba(37,99,235,0.045)" : "var(--surface)",
            padding: "15px 18px", cursor: "pointer", display: "grid",
            gridTemplateColumns: "10px 90px 1fr auto", gap: 12, alignItems: "center",
          }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: item.read === "N" ? "var(--blue)" : "transparent" }}/>
            <strong style={{ fontFamily: "var(--mono)", fontSize: 12 }}>{item.symbol}</strong>
            <span>
              <span style={{ display: "block", fontSize: 13, color: "var(--text-primary)" }}>{item.message}</span>
              <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{item.condition_type.replaceAll("_", " ")}</span>
            </span>
            <time style={{ fontSize: 10, color: "var(--text-muted)" }}>
              {new Date(item.fired_at).toLocaleString("en-IN")}
            </time>
          </button>
        ))}
      </div>
    </div>
  );
}