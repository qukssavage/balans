import { useState, useEffect } from "react";
import { getTransactions } from "../api";
import { C } from "../App";

const DEFAULT_CATS = {
  income: [
    { name: "Продажи",       icon: "💰", color: "#16A34A" },
    { name: "Услуги",        icon: "🔧", color: "#4338CA" },
    { name: "Аренда (доход)",icon: "🏢", color: "#B45309" },
    { name: "Консалтинг",    icon: "💼", color: "#6D28D9" },
    { name: "Комиссия",      icon: "📊", color: "#0E7490" },
    { name: "Прочие доходы", icon: "✨", color: "#BE185D" },
  ],
  expense: [
    { name: "Аренда",            icon: "🏠", color: "#DC2626" },
    { name: "Зарплата",          icon: "👥", color: "#EA580C" },
    { name: "Логистика",         icon: "🚛", color: "#4D7C0F" },
    { name: "Коммунальные",      icon: "⚡", color: "#0E7490" },
    { name: "Сырьё и материалы", icon: "📦", color: "#78716C" },
    { name: "Маркетинг",         icon: "📢", color: "#BE185D" },
    { name: "Налоги",            icon: "📋", color: "#64748B" },
    { name: "Оборудование",      icon: "🔩", color: "#B45309" },
    { name: "Офис",              icon: "🖊️", color: "#4338CA" },
    { name: "Командировки",      icon: "✈️", color: "#0E7490" },
    { name: "Ремонт",            icon: "🔨", color: "#DC2626" },
    { name: "Прочие расходы",    icon: "📤", color: "#9CA3AF" },
  ],
};

function Card({ children, style = {} }) {
  return (
    <div style={{ background: "#fff", borderRadius: 16, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.07)", ...style }}>
      {children}
    </div>
  );
}

export default function Categories() {
  const [stats, setStats] = useState({});
  const [search, setSearch] = useState("");

  useEffect(() => {
    getTransactions({ limit: 1000 }).then(txns => {
      const map = {};
      txns.forEach(t => {
        if (!map[t.category]) map[t.category] = { count: 0, total: 0, type: t.type };
        map[t.category].count++;
        map[t.category].total += t.amount;
      });
      setStats(map);
    });
  }, []);

  const fmt = (n) => {
    n = Math.round(n);
    if (n >= 1e6) return `${(n/1e6).toFixed(1)}M`;
    if (n >= 1e3) return `${Math.round(n/1e3)}K`;
    return String(n);
  };

  const filtered = (cats) => cats.filter(c =>
    !search || c.name.toLowerCase().includes(search.toLowerCase())
  );

  const CatCard = ({ cat, type }) => {
    const st = stats[cat.name] || { count: 0, total: 0 };
    return (
      <div style={{ background: "#fff", border: `1.5px solid ${C.border}`, borderRadius: 14, padding: 16, display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: cat.color + "20", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, flexShrink: 0 }}>
          {cat.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: C.text }}>{cat.name}</div>
          <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>
            {st.count} транзакций · {fmt(st.total)} UZS
          </div>
        </div>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: type === "income" ? C.green : C.red, flexShrink: 0 }} />
      </div>
    );
  };

  const inp = { padding: "10px 14px", border: `1.5px solid ${C.border}`, borderRadius: 10, fontSize: 14, fontFamily: "inherit", outline: "none", width: 260 };

  return (
    <div style={{ padding: "32px 36px", color: C.text, fontFamily: "'Inter','Segoe UI',system-ui,sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 4px", letterSpacing: "-0.5px" }}>Категории</h1>
          <p style={{ color: C.muted, fontSize: 14, margin: 0 }}>
            {Object.keys(DEFAULT_CATS.income).length + Object.keys(DEFAULT_CATS.expense).length} категорий · статистика по всем транзакциям
          </p>
        </div>
        <input style={inp} placeholder="Поиск категории..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28 }}>
        {/* Income */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.green }} />
            <span style={{ fontWeight: 700, fontSize: 15 }}>Доходы ({DEFAULT_CATS.income.length})</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {filtered(DEFAULT_CATS.income).map(c => <CatCard key={c.name} cat={c} type="income" />)}
          </div>
        </div>

        {/* Expense */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.red }} />
            <span style={{ fontWeight: 700, fontSize: 15 }}>Расходы ({DEFAULT_CATS.expense.length})</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {filtered(DEFAULT_CATS.expense).map(c => <CatCard key={c.name} cat={c} type="expense" />)}
          </div>
        </div>
      </div>
    </div>
  );
}
