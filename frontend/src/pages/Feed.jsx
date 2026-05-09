import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { forgesight } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { AlertTriangle, CheckCircle2, XCircle, TrendingUp } from "lucide-react";

export default function Feed() {
  const [metrics, setMetrics] = useState(null);
  const [items, setItems] = useState([]);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const [m, l] = await Promise.all([
        forgesight.getMetrics(),
        forgesight.listInspections(),
      ]);
      setMetrics(m);
      setItems(l.items || []);
    } catch {}
  };

  useEffect(() => {
    load();
  }, []);

  const verdictChart = metrics
    ? [
        { name: "pass", value: metrics.verdict_counts.pass, color: "#10B981" },
        { name: "warn", value: metrics.verdict_counts.warn, color: "#F59E0B" },
        { name: "fail", value: metrics.verdict_counts.fail, color: "#ED1C24" },
      ]
    : [];

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-10" data-testid="feed-page">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="fs-label mb-3">§ FEED · DASHBOARD</div>
          <h1 className="font-display font-black tracking-tighter text-4xl md:text-5xl">
            Defect Feed
          </h1>
          <p className="text-zinc-400 mt-3">Every inspection. Live quality score.</p>
        </div>
        <Link to="/console" className="fs-btn fs-btn-primary" data-testid="feed-run-btn">
          + New inspection
        </Link>
      </header>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-0 border-t border-l border-white/10 mb-8">
        <Kpi label="Total inspections" value={metrics?.total_inspections ?? "—"} icon={TrendingUp} />
        <Kpi label="Quality score" value={metrics ? `${metrics.quality_score}%` : "—"} icon={CheckCircle2} accent />
        <Kpi label="Avg confidence" value={metrics ? `${Math.round(metrics.avg_confidence * 100)}%` : "—"} icon={AlertTriangle} />
        <Kpi label="Fail rate" value={metrics && metrics.total_inspections ? `${Math.round((metrics.verdict_counts.fail / metrics.total_inspections) * 100)}%` : "—"} icon={XCircle} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Verdict chart */}
        <div className="border border-white/10 bg-[#141416] p-5 fs-corners">
          <div className="flex items-center justify-between mb-4">
            <span className="fs-label">Verdict distribution</span>
            <span className="fs-mono-small text-zinc-500">ALL TIME</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={verdictChart}>
                <XAxis dataKey="name" stroke="#71717A" tick={{ fontFamily: "JetBrains Mono", fontSize: 11 }} axisLine={{ stroke: "#27272A" }} tickLine={false} />
                <YAxis stroke="#71717A" tick={{ fontFamily: "JetBrains Mono", fontSize: 11 }} axisLine={{ stroke: "#27272A" }} tickLine={false} />
                <Tooltip
                  cursor={{ fill: "rgba(237,28,36,0.08)" }}
                  contentStyle={{ background: "#0A0A0A", border: "1px solid #27272A", fontFamily: "JetBrains Mono" }}
                  labelStyle={{ color: "#fff" }}
                />
                <Bar dataKey="value">
                  {verdictChart.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top defects */}
        <div className="border border-white/10 bg-[#141416] p-5 fs-corners">
          <div className="flex items-center justify-between mb-4">
            <span className="fs-label">Top defect types</span>
          </div>
          {metrics && metrics.top_defects.length ? (
            <div className="space-y-2.5">
              {metrics.top_defects.map((d) => {
                const max = metrics.top_defects[0].count || 1;
                const pct = (d.count / max) * 100;
                return (
                  <div key={d.type}>
                    <div className="flex items-baseline justify-between mb-1">
                      <span className="font-mono text-xs text-zinc-300">{d.type}</span>
                      <span className="font-mono text-xs text-zinc-500 tabular-nums">{d.count}</span>
                    </div>
                    <div className="fs-bar">
                      <div style={{ width: `${Math.max(8, pct)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center font-mono text-sm text-zinc-600">
              No inspections yet.
            </div>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border border-white/10 bg-[#141416]">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <span className="fs-label">Inspection log · {items.length}</span>
        </div>
        {items.length === 0 ? (
          <div className="p-10 text-center font-mono text-sm text-zinc-500">
            No inspections yet. Head to the Console to run the first one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="inspections-table">
              <thead>
                <tr className="text-left border-b border-white/10">
                  <Th>Time</Th>
                  <Th>Verdict</Th>
                  <Th>Headline</Th>
                  <Th>Defects</Th>
                  <Th>Priority</Th>
                  <Th>Confidence</Th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr 
                    key={it.id} 
                    onClick={() => navigate(`/report/${it.id}`)}
                    className="border-b border-white/5 hover:bg-white/[0.04] cursor-pointer transition-colors"
                  >
                    <Td mono>{new Date(it.created_at).toLocaleString()}</Td>
                    <Td>
                      <span className={`fs-chip fs-chip-${it.verdict}`}>{it.verdict}</span>
                    </Td>
                    <Td>{it.headline}</Td>
                    <Td mono>{it.defect_count}</Td>
                    <Td mono>{it.priority}</Td>
                    <Td mono>{Math.round(it.confidence * 100)}%</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Kpi({ label, value, icon: Icon, accent }) {
  return (
    <div className="border-r border-b border-white/10 p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="fs-label">{label}</span>
        <Icon className={`w-3.5 h-3.5 ${accent ? "text-[#ED1C24]" : "text-zinc-500"}`} />
      </div>
      <div className={`font-display font-black text-3xl md:text-4xl tracking-tighter ${accent ? "text-[#ED1C24]" : "text-white"}`}>
        {value}
      </div>
    </div>
  );
}
function Th({ children }) {
  return <th className="px-5 py-3 fs-label font-normal">{children}</th>;
}
function Td({ children, mono }) {
  return <td className={`px-5 py-3 ${mono ? "font-mono text-xs" : "text-sm"} text-zinc-300`}>{children}</td>;
}
