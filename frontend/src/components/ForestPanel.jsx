import { Bar, CartesianGrid, Cell, Line, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { usePoll } from "../api.js";

export default function ForestPanel() {
  const { data } = usePoll("/api/forest", 600000);
  if (!data) return <div className="panel forest"><div className="empty">Loading tree cover data…</div></div>;
  const s = data.stats;
  const rows = data.years.map((y, i) => ({
    year: y, loss: data.loss_ha[i],
    trend: +(s.projected_next_year_ha - s.trend_ha_per_year * (data.years.at(-1) + 1 - y)).toFixed(1),
    anomaly: s.anomaly_years.includes(y),
  }));
  return (
    <div className="panel forest">
      <div className="panel-head">
        <h2>Tree cover loss</h2>
        <span className="meta">{data.source}</span>
      </div>
      <div className="figures">
        <div><b>{s.total_loss_ha.toLocaleString()}</b><span>ha lost 2001–2023</span></div>
        <div><b>{s.trend_ha_per_year > 0 ? "+" : ""}{s.trend_ha_per_year}</b><span>ha per year trend</span></div>
        <div><b>{s.last5_vs_prev5_pct}%</b><span>last 5 yrs vs previous 5</span></div>
        <div><b>{s.projected_next_year_ha}</b><span>ha projected for 2024</span></div>
      </div>
      <ResponsiveContainer width="100%" height={230}>
        <ComposedChart data={rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="#2f4238" vertical={false} />
          <XAxis dataKey="year" stroke="#8fa396" tick={{ fontSize: 11 }} />
          <YAxis stroke="#8fa396" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#1f2d26", border: "1px solid #2f4238" }} />
          <Bar dataKey="loss" name="Loss (ha)">
            {rows.map((r) => <Cell key={r.year} fill={r.anomaly ? "#e25b45" : "#5fb3a8"} />)}
          </Bar>
          <Line dataKey="trend" name="Linear trend" stroke="#e9a23b" dot={false} strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="note">
        Red bars are anomaly years (z-score ≥ 2): {s.anomaly_years.join(", ") || "none"}. Worst year: {s.worst_year}.
        {data.fallback_reason && ` Real data unavailable (${data.fallback_reason}).`}
      </p>
    </div>
  );
}
