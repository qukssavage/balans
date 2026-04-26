import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getKPI, getMonthly, getTransactions, addTransaction } from "../api";
import { C } from "../App";

const fmt = (n) => {
  n = Math.round(n);
  if (Math.abs(n) >= 1e6) return `${(n/1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `${Math.round(n/1e3)}K`;
  return String(n);
};
const fmtDate = (d) => new Date(d).toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
const pct = (a, b) => b === 0 ? null : Math.round((a - b) / b * 100);

const CATEGORIES = {
  income:  ["Продажи","Услуги","Аренда (доход)","Консалтинг","Комиссия","Прочие доходы"],
  expense: ["Аренда","Зарплата","Логистика","Коммунальные","Сырьё и материалы","Маркетинг","Налоги","Оборудование","Офис","Командировки","Ремонт","Прочие расходы"],
};

function Card({ children, style = {} }) {
  return <div style={{ background: C.white, borderRadius: 16, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.07)", ...style }}>{children}</div>;
}

function KPICard({ label, value, prev, invert }) {
  const change = pct(value, prev);
  const positive = invert ? change <= 0 : change >= 0;
  return (
    <Card style={{ padding: 20 }}>
      <div style={{ fontSize: 12, color: C.muted, fontWeight: 500, marginBottom: 10 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.5px", marginBottom: 8 }}>{fmt(value)} UZS</div>
      {change !== null && (
        <div style={{ fontSize: 12, fontWeight: 600, color: positive ? C.green : C.red }}>
          {change >= 0 ? "▲" : "▼"} {Math.abs(change)}% vs прошлый месяц
        </div>
      )}
    </Card>
  );
}

function Onboarding({ onAdd }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "70vh", textAlign: "center", padding: 40 }}>
      <div style={{ fontSize: 56, marginBottom: 20 }}>📊</div>
      <h2 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 12px", letterSpacing: "-0.5px", color: C.text }}>Добро пожаловать в Balans</h2>
      <p style={{ color: C.muted, fontSize: 15, maxWidth: 420, lineHeight: 1.7, margin: "0 0 32px" }}>
        Здесь будут отображаться доходы и расходы вашей компании. Начните с добавления первой транзакции — через форму ниже или через Telegram бота.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, maxWidth: 540, marginBottom: 36 }}>
        {[
          ["💬", "Telegram Bot", "Пишите боту @botdata365_bot голосом или текстом"],
          ["📈", "Живой дашборд", "Все данные обновляются в реальном времени"],
          ["📁", "Категории", "18 категорий для доходов и расходов"],
        ].map(([icon, title, desc]) => (
          <div key={title} style={{ background: "#fff", border: `1.5px solid ${C.border}`, borderRadius: 14, padding: 18, textAlign: "left" }}>
            <div style={{ fontSize: 24, marginBottom: 10 }}>{icon}</div>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6, color: C.text }}>{title}</div>
            <div style={{ fontSize: 12, color: C.muted, lineHeight: 1.5 }}>{desc}</div>
          </div>
        ))}
      </div>
      <button onClick={onAdd}
        style={{ background: C.gold, color: "#fff", border: "none", borderRadius: 12, padding: "12px 28px", fontFamily: "inherit", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
        + Добавить первую транзакцию
      </button>
    </div>
  );
}

export default function Overview({ onNavigate }) {
  const [kpi,     setKpi]     = useState(null);
  const [monthly, setMonthly] = useState([]);
  const [recent,  setRecent]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form,    setForm]    = useState({ type:"income", amount:"", category:"", date: new Date().toISOString().split("T")[0], note:"" });

  const load = async () => {
    const [k, m, t] = await Promise.all([getKPI(), getMonthly(), getTransactions({ limit: 5 })]);
    setKpi(k); setMonthly(m); setRecent(t);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!form.amount || !form.category) return alert("Заполните сумму и категорию");
    await addTransaction({ ...form, amount: parseFloat(form.amount) });
    setShowAdd(false);
    setForm({ type:"income", amount:"", category:"", date: new Date().toISOString().split("T")[0], note:"" });
    load();
  };

  const inp = { width: "100%", padding: "10px 14px", border: `1.5px solid ${C.border}`, borderRadius: 10, fontSize: 14, fontFamily: "inherit", boxSizing: "border-box", outline: "none" };
  const isEmpty = !loading && recent.length === 0;

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "70vh", color: C.muted, fontSize: 15 }}>
        Загрузка...
      </div>
    );
  }

  if (isEmpty) {
    return <Onboarding onAdd={() => setShowAdd(true)} />;
  }

  return (
    <div style={{ padding: "32px 36px", color: C.text }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 4 }}>
            {new Date().toLocaleDateString("ru-RU", { weekday:"long", day:"numeric", month:"long", year:"numeric" })}
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: "-0.5px" }}>Обзор</h1>
        </div>
        <button onClick={() => setShowAdd(true)}
          style={{ background: C.gold, color: "#fff", border: "none", borderRadius: 10, padding: "10px 20px", fontFamily: "inherit", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
          + Добавить
        </button>
      </div>

      {showAdd && (
        <Card style={{ marginBottom: 24, padding: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Новая транзакция</div>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {["income","expense"].map(t => (
              <button key={t} onClick={() => setForm(f => ({...f, type: t, category: ""}))}
                style={{ flex: 1, padding: 10, borderRadius: 10, border: "2px solid", cursor: "pointer", fontFamily: "inherit", fontWeight: 600, fontSize: 13,
                  borderColor: form.type === t ? (t==="income" ? C.green : C.red) : C.border,
                  background: form.type === t ? (t==="income" ? "#DCFCE7" : "#FEE2E2") : "#fff",
                  color: form.type === t ? (t==="income" ? C.green : C.red) : C.muted }}>
                {t === "income" ? "↑ Доход" : "↓ Расход"}
              </button>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <input style={inp} type="number" placeholder="Сумма (UZS)" value={form.amount} onChange={e => setForm(f => ({...f, amount: e.target.value}))} />
            <select style={{ ...inp, background: "#fff" }} value={form.category} onChange={e => setForm(f => ({...f, category: e.target.value}))}>
              <option value="">Категория...</option>
              {CATEGORIES[form.type].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input style={inp} type="date" value={form.date} onChange={e => setForm(f => ({...f, date: e.target.value}))} />
            <input style={inp} type="text" placeholder="Заметка (необязательно)" value={form.note} onChange={e => setForm(f => ({...f, note: e.target.value}))} />
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => setShowAdd(false)} style={{ flex: 1, padding: 10, borderRadius: 10, border: `1.5px solid ${C.border}`, background: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 600 }}>Отмена</button>
            <button onClick={handleAdd} style={{ flex: 2, padding: 10, borderRadius: 10, border: "none", background: C.gold, color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 600 }}>Сохранить</button>
          </div>
        </Card>
      )}

      {kpi && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 24 }}>
          <KPICard label="Доходы (этот месяц)"  value={kpi.this_month.income}  prev={kpi.prev_month.income} />
          <KPICard label="Расходы (этот месяц)" value={kpi.this_month.expense} prev={kpi.prev_month.expense} invert />
          <KPICard label="Прибыль"              value={kpi.this_month.net}     prev={kpi.prev_month.net} />
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20 }}>
        <Card>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>Доходы и расходы</div>
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 16 }}>Последние 6 месяцев (млн UZS)</div>
          <div style={{ display: "flex", gap: 16, fontSize: 12, color: C.muted, marginBottom: 12 }}>
            <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background: C.green, marginRight:5 }} />Доходы</span>
            <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background:"#FCA5A5", marginRight:5 }} />Расходы</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={monthly.map(m => ({ ...m, income: Math.round(m.income/1e6*10)/10, expense: Math.round(m.expense/1e6*10)/10 }))}>
              <defs>
                <linearGradient id="gInc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.green} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={C.green} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gExp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.red} stopOpacity={0.1} />
                  <stop offset="95%" stopColor={C.red} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0EDE8" />
              <XAxis dataKey="label" tick={{ fontSize:12, fill: C.muted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize:12, fill: C.muted }} axisLine={false} tickLine={false} />
              <Tooltip formatter={v => [`${v}M UZS`]} contentStyle={{ borderRadius:10, fontSize:13 }} />
              <Area type="monotone" dataKey="income"  stroke={C.green} strokeWidth={2.5} fill="url(#gInc)" />
              <Area type="monotone" dataKey="expense" stroke={C.red}   strokeWidth={2.5} fill="url(#gExp)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card style={{ padding: 20 }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
            <div style={{ fontWeight:700, fontSize:15 }}>Последние записи</div>
            <button onClick={() => onNavigate("transactions")} style={{ fontSize:12, color: C.gold, background:"none", border:"none", cursor:"pointer", fontWeight:600 }}>Все →</button>
          </div>
          {recent.length === 0 ? (
            <div style={{ textAlign: "center", padding: "20px 0", color: C.muted, fontSize: 13 }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
              Транзакций пока нет
            </div>
          ) : recent.map(t => (
            <div key={t.id} style={{ display:"flex", alignItems:"center", gap:10, marginBottom:14 }}>
              <div style={{ width:36, height:36, borderRadius:10, background:"#F6F4EF", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, flexShrink:0 }}>
                {t.type === "income" ? "💰" : "💸"}
              </div>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ fontSize:13, fontWeight:600, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{t.category}</div>
                <div style={{ fontSize:11, color: C.muted }}>{fmtDate(t.date)} · {t.username}</div>
              </div>
              <div style={{ fontSize:13, fontWeight:700, color: t.type==="income" ? C.green : C.red, flexShrink:0 }}>
                {t.type==="income" ? "+" : "−"}{fmt(t.amount)}
              </div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}
