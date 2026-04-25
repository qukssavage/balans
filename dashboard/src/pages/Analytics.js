import { useState, useEffect } from "react";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getMonthly, getCategories } from "../api";
import { C } from "../App";

const COLORS = ["#16A34A","#4338CA","#DC2626","#EA580C","#0E7490","#BE185D","#B45309","#4D7C0F","#6D28D9","#78716C","#64748B","#9CA3AF"];
const fmt = (n) => new Intl.NumberFormat("ru-RU").format(Math.round(n));

function Card({ children, style = {} }) {
  return <div style={{ background:"#fff", borderRadius:16, padding:24, boxShadow:"0 1px 3px rgba(0,0,0,0.07)", ...style }}>{children}</div>;
}

export default function Analytics() {
  const [monthly, setMonthly] = useState([]);
  const [cats,    setCats]    = useState([]);

  useEffect(() => {
    getMonthly().then(setMonthly);
    getCategories().then(setCats);
  }, []);

  const expCats = cats.filter(c => c.type === "expense").sort((a,b) => b.total - a.total);
  const incCats = cats.filter(c => c.type === "income").sort((a,b) => b.total - a.total);
  const totalExp = expCats.reduce((s,c) => s + c.total, 0);
  const totalInc = incCats.reduce((s,c) => s + c.total, 0);

  const barData = monthly.map(m => ({
    ...m,
    income:  Math.round(m.income  / 1e6 * 10) / 10,
    expense: Math.round(m.expense / 1e6 * 10) / 10,
  }));

  return (
    <div style={{ padding:"32px 36px", color: C.text }}>
      <h1 style={{ fontSize:26, fontWeight:800, margin:"0 0 8px", letterSpacing:"-0.5px" }}>Аналитика</h1>
      <p style={{ color: C.muted, fontSize:14, marginBottom:28 }}>Текущий месяц и тренды за 6 месяцев</p>

      {/* Donuts */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:20 }}>
        {[
          { title:"Расходы по категориям", data: expCats, total: totalExp },
          { title:"Доходы по категориям",  data: incCats, total: totalInc },
        ].map(({ title, data, total }) => (
          <Card key={title}>
            <div style={{ fontWeight:700, fontSize:15, marginBottom:4 }}>{title}</div>
            <div style={{ fontSize:12, color: C.muted, marginBottom:16 }}>Текущий месяц — {fmt(total)} UZS</div>
            <div style={{ display:"flex", gap:16 }}>
              <ResponsiveContainer width={140} height={140}>
                <PieChart>
                  <Pie data={data} dataKey="total" innerRadius={40} outerRadius={65} paddingAngle={3}>
                    {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => [fmt(v) + " UZS"]} contentStyle={{ borderRadius:10, fontSize:13 }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ flex:1 }}>
                {data.map((c, i) => (
                  <div key={c.category} style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8 }}>
                    <div style={{ width:10, height:10, borderRadius:2, background: COLORS[i % COLORS.length], flexShrink:0 }} />
                    <span style={{ fontSize:12, flex:1, color: C.text }}>{c.category}</span>
                    <span style={{ fontSize:11, color: C.muted }}>{total ? Math.round(c.total/total*100) : 0}%</span>
                  </div>
                ))}
                {data.length === 0 && <div style={{ fontSize:13, color: C.muted, paddingTop:16 }}>Нет данных</div>}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Bar chart */}
      <Card>
        <div style={{ fontWeight:700, fontSize:15, marginBottom:4 }}>Сравнение по месяцам</div>
        <div style={{ display:"flex", gap:14, fontSize:12, color: C.muted, margin:"4px 0 16px" }}>
          <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background: C.green, marginRight:5 }} />Доходы</span>
          <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background:"#FCA5A5", marginRight:5 }} />Расходы</span>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={barData} barCategoryGap="30%" barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EDE8" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize:12, fill: C.muted }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize:12, fill: C.muted }} axisLine={false} tickLine={false} />
            <Tooltip formatter={v => [`${v}M UZS`]} contentStyle={{ borderRadius:10, fontSize:13 }} />
            <Bar dataKey="income"  fill={C.green}   radius={[6,6,0,0]} />
            <Bar dataKey="expense" fill="#FCA5A5"   radius={[6,6,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
