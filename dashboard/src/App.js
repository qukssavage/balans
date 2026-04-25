import { useState } from "react";
import Overview     from "./pages/Overview";
import Transactions from "./pages/Transactions";
import Analytics    from "./pages/Analytics";

const NAV = [
  { id: "overview",     label: "Обзор",        icon: "⬡" },
  { id: "transactions", label: "Транзакции",    icon: "≡" },
  { id: "analytics",   label: "Аналитика",     icon: "◎" },
];

const C = {
  navy: "#0B1120", gold: "#C9A84C",
  cream: "#F6F4EF", white: "#FFFFFF",
  green: "#16A34A", red: "#DC2626",
  text: "#1C1917", muted: "#6B7280",
  border: "#E7E3DC",
};

export { C };

export default function App() {
  const [page, setPage] = useState("overview");

  return (
    <div style={{ display: "flex", height: "100vh", background: C.cream, fontFamily: "'Inter','Segoe UI',system-ui,sans-serif" }}>
      {/* Sidebar */}
      <div style={{ width: 220, background: C.navy, display: "flex", flexDirection: "column", flexShrink: 0 }}>
        {/* Logo */}
        <div style={{ padding: "26px 22px 18px", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: C.gold, letterSpacing: "-0.5px" }}>Balans</div>
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginTop: 2, fontWeight: 600, letterSpacing: 1.5 }}>FINANCE DASHBOARD</div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "14px 10px" }}>
          {NAV.map(item => {
            const active = page === item.id;
            return (
              <button key={item.id} onClick={() => setPage(item.id)}
                style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "10px 13px",
                  borderRadius: 10, border: "none", cursor: "pointer", marginBottom: 2,
                  background: active ? "rgba(201,168,76,0.18)" : "transparent",
                  color: active ? C.gold : "rgba(255,255,255,0.5)",
                  fontFamily: "inherit", fontSize: 14, fontWeight: active ? 600 : 400, textAlign: "left" }}>
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Bot status */}
        <div style={{ padding: "14px 20px", borderTop: "1px solid rgba(255,255,255,0.07)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22C55E" }} />
            <div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.75)", fontWeight: 600 }}>@botdata365_bot</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>Telegram подключён</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <main style={{ flex: 1, overflow: "auto" }}>
        {page === "overview"     && <Overview     onNavigate={setPage} />}
        {page === "transactions" && <Transactions />}
        {page === "analytics"    && <Analytics    />}
      </main>
    </div>
  );
}
