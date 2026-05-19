import { useState } from "react";
import LoginPage     from "./pages/LoginPage";
import AnalysePage   from "./pages/AnalysePage";
import PortfolioPage from "./pages/PortfolioPage";
import WatchlistPage from "./pages/WatchlistPage";
import ScanPage      from "./pages/ScanPage";

const NAV = [
  { id: "analyse",   label: "Analyse",
    icon: (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 11l3-4 3 2 3-5 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="14" cy="7" r="1" fill="currentColor"/></svg>) },
  { id: "scan",      label: "Scanner",
    icon: (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/><path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><path d="M7 4.5v5M4.5 7h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>) },
  { id: "watchlist", label: "Watchlists",
    icon: (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5"/><path d="M5 8h6M5 5.5h6M5 10.5h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>) },
  { id: "portfolio", label: "Portfolio",
    icon: (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="6" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5"/><path d="M5 6V4.5A3 3 0 0111 4.5V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>) },
];

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("sa_token"));
  const [email, setEmail] = useState(() => localStorage.getItem("sa_email") ?? "");
  const [page, setPage]   = useState("analyse");

  const handleLogin  = (t, e) => { setToken(t); setEmail(e); };
  const handleLogout = () => {
    localStorage.removeItem("sa_token"); localStorage.removeItem("sa_email");
    setToken(null); setEmail("");
  };

  if (!token) return <LoginPage onLogin={handleLogin} />;
  const initials = email ? email[0].toUpperCase() : "U";

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{ width:220, minHeight:"100vh", background:"var(--sidebar-bg)", borderRight:"1px solid var(--sidebar-border)", display:"flex", flexDirection:"column", padding:"24px 0", position:"fixed", top:0, left:0, zIndex:20 }}>
        <div style={{ padding:"0 20px 28px" }}>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <div style={{ width:32, height:32, background:"var(--accent)", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center" }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 12l3-5 3 3 3-6 3 4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            <div>
              <div style={{ color:"#fff", fontSize:13, fontWeight:600 }}>StockAlert</div>
              <div style={{ color:"#4a4f6a", fontSize:10, marginTop:1 }}>Personal Dashboard</div>
            </div>
          </div>
        </div>
        <nav style={{ flex:1, padding:"0 10px" }}>
          <div style={{ fontSize:9, fontWeight:600, letterSpacing:"0.12em", color:"#3a3f58", padding:"0 10px 8px", textTransform:"uppercase" }}>Navigation</div>
          {NAV.map((item) => {
            const active = page === item.id;
            return (
              <button key={item.id} onClick={() => setPage(item.id)}
                style={{ display:"flex", alignItems:"center", gap:10, width:"100%", padding:"9px 10px", borderRadius:8, border:"none", background: active?"rgba(22,163,74,0.12)":"transparent", color: active?"var(--accent)":"#8a90ab", fontSize:13, fontWeight: active?600:400, cursor:"pointer", marginBottom:2, textAlign:"left", transition:"all 0.15s" }}
                onMouseEnter={(e)=>{ if(!active){e.currentTarget.style.background="rgba(255,255,255,0.05)";e.currentTarget.style.color="#c8cde0";}}}
                onMouseLeave={(e)=>{ if(!active){e.currentTarget.style.background="transparent";e.currentTarget.style.color="#8a90ab";}}}
              >
                {item.icon}{item.label}
              </button>
            );
          })}
        </nav>
        <div style={{ margin:"0 10px", paddingTop:16, borderTop:"1px solid var(--sidebar-border)" }}>
          <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:10, padding:"0 0 0 4px" }}>
            <div style={{ width:30, height:30, borderRadius:"50%", background:"#1e2130", border:"1px solid #2e3348", display:"flex", alignItems:"center", justifyContent:"center", color:"#8a90ab", fontSize:12, fontWeight:600 }}>{initials}</div>
            <div style={{ minWidth:0 }}><div style={{ color:"#c8cde0", fontSize:11, fontWeight:500, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{email}</div></div>
          </div>
          <button onClick={handleLogout}
            style={{ width:"100%", padding:"7px 10px", borderRadius:6, border:"1px solid #2e3348", background:"transparent", color:"#6b7191", fontSize:11, cursor:"pointer", transition:"all 0.15s", fontFamily:"var(--sans)" }}
            onMouseEnter={(e)=>{e.currentTarget.style.borderColor="var(--danger)";e.currentTarget.style.color="var(--danger)";}}
            onMouseLeave={(e)=>{e.currentTarget.style.borderColor="#2e3348";e.currentTarget.style.color="#6b7191";}}
          >Sign out</button>
        </div>
      </aside>
      <main style={{ marginLeft:220, flex:1, minHeight:"100vh", background:"var(--surface-2)" }}>
        <div style={{ height:52, background:"var(--surface)", borderBottom:"1px solid var(--border)", display:"flex", alignItems:"center", padding:"0 32px", position:"sticky", top:0, zIndex:10 }}>
          <h1 style={{ fontFamily:"var(--display)", fontSize:18, fontWeight:600, color:"var(--text-primary)", margin:0 }}>{NAV.find((n)=>n.id===page)?.label}</h1>
        </div>
        <div style={{ padding:"32px" }}>
          {page==="analyse"   && <AnalysePage />}
          {page==="scan"      && <ScanPage />}
          {page==="watchlist" && <WatchlistPage />}
          {page==="portfolio" && <PortfolioPage />}
        </div>
      </main>
    </div>
  );
}
