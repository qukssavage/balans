import { useState, useEffect } from "react";
import { getTransactions, deleteTransaction, addTransaction, updateTransaction } from "../api";
import { C } from "../App";

const fmtDate = (d) => new Date(d).toLocaleDateString("ru-RU", { day:"numeric", month:"short", year:"numeric" });
const fmt = (n) => new Intl.NumberFormat("ru-RU").format(Math.round(n));

const CATEGORIES = {
  income:  ["Продажи","Услуги","Аренда (доход)","Консалтинг","Комиссия","Прочие доходы"],
  expense: ["Аренда","Зарплата","Логистика","Коммунальные","Сырьё и материалы","Маркетинг","Налоги","Оборудование","Офис","Командировки","Ремонт","Прочие расходы"],
};

const emptyForm = () => ({ type:"income", amount:"", category:"", date: new Date().toISOString().split("T")[0], note:"" });

export default function Transactions() {
  const [txns,    setTxns]    = useState([]);
  const [search,  setSearch]  = useState("");
  const [typeF,   setTypeF]   = useState("all");
  const [catF,    setCatF]    = useState("all");
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form,    setForm]    = useState(emptyForm());

  const load = async () => {
    const params = {};
    if (typeF !== "all") params.type = typeF;
    if (catF  !== "all") params.category = catF;
    const data = await getTransactions(params);
    setTxns(data);
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [typeF, catF]);

  const allCats = [...CATEGORIES.income, ...CATEGORIES.expense];
  const filtered = txns.filter(t =>
    !search || t.category.toLowerCase().includes(search.toLowerCase()) || (t.note||"").toLowerCase().includes(search.toLowerCase())
  );

  const openAdd = () => { setEditing(null); setForm(emptyForm()); setShowAdd(true); };
  const openEdit = (t) => { setEditing(t); setForm({ type:t.type, amount:String(t.amount), category:t.category, date:t.date, note:t.note||"" }); setShowAdd(true); };

  const handleSave = async () => {
    if (!form.amount || !form.category) return alert("Заполните сумму и категорию");
    const data = { ...form, amount: parseFloat(form.amount) };
    if (editing) await updateTransaction(editing.id, data);
    else await addTransaction(data);
    setShowAdd(false); setEditing(null); setForm(emptyForm()); load();
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить транзакцию?")) return;
    await deleteTransaction(id); load();
  };

  const inp = { width:"100%", padding:"10px 14px", border:`1.5px solid ${C.border}`, borderRadius:10, fontSize:14, fontFamily:"inherit", boxSizing:"border-box", outline:"none" };

  return (
    <div style={{ padding:"32px 36px", color: C.text }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:28 }}>
        <h1 style={{ fontSize:26, fontWeight:800, margin:0, letterSpacing:"-0.5px" }}>Транзакции</h1>
        <button onClick={openAdd} style={{ background: C.gold, color:"#fff", border:"none", borderRadius:10, padding:"10px 20px", fontFamily:"inherit", fontWeight:600, fontSize:14, cursor:"pointer" }}>
          + Добавить
        </button>
      </div>

      {/* Modal */}
      {showAdd && (
        <div style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.4)", display:"flex", alignItems:"center", justifyContent:"center", zIndex:1000 }}>
          <div style={{ background:"#fff", borderRadius:20, padding:32, width:480, boxShadow:"0 25px 60px rgba(0,0,0,0.2)" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
              <div style={{ fontWeight:700, fontSize:18 }}>{editing ? "Редактировать" : "Новая транзакция"}</div>
              <button onClick={() => setShowAdd(false)} style={{ background:"none", border:"none", fontSize:20, cursor:"pointer", color: C.muted }}>×</button>
            </div>
            <div style={{ display:"flex", gap:8, marginBottom:16 }}>
              {["income","expense"].map(t => (
                <button key={t} onClick={() => setForm(f => ({...f, type:t, category:""}))}
                  style={{ flex:1, padding:10, borderRadius:10, border:"2px solid", cursor:"pointer", fontFamily:"inherit", fontWeight:600, fontSize:13,
                    borderColor: form.type===t ? (t==="income" ? C.green : C.red) : C.border,
                    background:  form.type===t ? (t==="income" ? "#DCFCE7" : "#FEE2E2") : "#fff",
                    color:       form.type===t ? (t==="income" ? C.green : C.red) : C.muted }}>
                  {t==="income" ? "↑ Доход" : "↓ Расход"}
                </button>
              ))}
            </div>
            {[
              ["Сумма (UZS)", "number", "amount", "5000000"],
              ["Дата",        "date",   "date",   ""],
              ["Заметка",     "text",   "note",   "Описание..."],
            ].map(([label, type, key, ph]) => (
              <label key={key} style={{ display:"block", marginBottom:14 }}>
                <span style={{ display:"block", fontSize:12, fontWeight:500, color: C.muted, marginBottom:6 }}>{label}</span>
                <input style={inp} type={type} placeholder={ph} value={form[key]} onChange={e => setForm(f => ({...f, [key]: e.target.value}))} />
              </label>
            ))}
            <label style={{ display:"block", marginBottom:20 }}>
              <span style={{ display:"block", fontSize:12, fontWeight:500, color: C.muted, marginBottom:6 }}>Категория</span>
              <select style={{ ...inp, background:"#fff" }} value={form.category} onChange={e => setForm(f => ({...f, category:e.target.value}))}>
                <option value="">Выберите...</option>
                {CATEGORIES[form.type].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            <div style={{ display:"flex", gap:10 }}>
              <button onClick={() => setShowAdd(false)} style={{ flex:1, padding:12, borderRadius:12, border:`1.5px solid ${C.border}`, background:"#fff", cursor:"pointer", fontFamily:"inherit", fontWeight:600 }}>Отмена</button>
              <button onClick={handleSave}              style={{ flex:2, padding:12, borderRadius:12, border:"none", background: C.gold, color:"#fff", cursor:"pointer", fontFamily:"inherit", fontWeight:600 }}>Сохранить</button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <input style={{ ...inp, width:220 }} placeholder="Поиск..." value={search} onChange={e => setSearch(e.target.value)} />
        <select style={{ ...inp, background:"#fff", width:"auto" }} value={typeF} onChange={e => setTypeF(e.target.value)}>
          <option value="all">Все типы</option>
          <option value="income">Доходы</option>
          <option value="expense">Расходы</option>
        </select>
        <select style={{ ...inp, background:"#fff", width:"auto" }} value={catF} onChange={e => setCatF(e.target.value)}>
          <option value="all">Все категории</option>
          {allCats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Table */}
      <div style={{ background:"#fff", borderRadius:16, overflow:"hidden", boxShadow:"0 1px 3px rgba(0,0,0,0.07)" }}>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ borderBottom:`1px solid ${C.border}`, background:"#FAFAF8" }}>
              {["Дата","Категория","Заметка","Кто добавил","Сумма",""].map(h => (
                <th key={h} style={{ padding:"12px 16px", fontSize:12, fontWeight:600, color: C.muted, textAlign: h==="Сумма" ? "right" : "left" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ padding:40, textAlign:"center", color: C.muted }}>Транзакций нет</td></tr>
            ) : filtered.map((t, i) => (
              <tr key={t.id} style={{ borderBottom:`1px solid ${C.border}`, background: i%2===0 ? "#fff" : "#FAFAF8" }}>
                <td style={{ padding:"12px 16px", fontSize:13, color: C.muted, whiteSpace:"nowrap" }}>{fmtDate(t.date)}</td>
                <td style={{ padding:"12px 16px", fontSize:13, fontWeight:500 }}>{t.category}</td>
                <td style={{ padding:"12px 16px", fontSize:13, color: C.muted, maxWidth:200 }}>
                  <span style={{ display:"block", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{t.note || "—"}</span>
                </td>
                <td style={{ padding:"12px 16px", fontSize:12, color: C.muted }}>{t.username || "—"}</td>
                <td style={{ padding:"12px 16px", textAlign:"right" }}>
                  <span style={{ fontSize:14, fontWeight:700, color: t.type==="income" ? C.green : C.red }}>
                    {t.type==="income" ? "+" : "−"}{fmt(t.amount)} UZS
                  </span>
                </td>
                <td style={{ padding:"12px 16px" }}>
                  <div style={{ display:"flex", gap:6 }}>
                    <button onClick={() => openEdit(t)} style={{ fontSize:12, padding:"5px 10px", borderRadius:8, border:`1.5px solid ${C.border}`, background:"#fff", cursor:"pointer", fontFamily:"inherit" }}>Изм.</button>
                    <button onClick={() => handleDelete(t.id)} style={{ fontSize:12, padding:"5px 10px", borderRadius:8, border:"none", background:"#FEE2E2", color: C.red, cursor:"pointer", fontFamily:"inherit", fontWeight:600 }}>✕</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding:"12px 20px", borderTop:`1px solid ${C.border}`, fontSize:13, color: C.muted }}>
          Показано {filtered.length} из {txns.length}
        </div>
      </div>
    </div>
  );
}
