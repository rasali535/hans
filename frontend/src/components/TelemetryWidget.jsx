import { useEffect, useRef, useState } from "react";
import { forgesight } from "@/lib/api";
import { Activity, Cpu, Zap, Thermometer, BarChart3, Database } from "lucide-react";

/* ── helpers ─────────────────────────────────────────────────────────────── */
function arc(pct, r = 38) {
  const clamp = Math.min(100, Math.max(0, pct));
  const angle = (clamp / 100) * 270 - 135;          // 270° sweep, start -135°
  const rad   = (a) => (a * Math.PI) / 180;
  const x     = 50 + r * Math.cos(rad(angle));
  const y     = 50 + r * Math.sin(rad(angle));
  const large = clamp > 50 ? 1 : 0;
  const sx    = 50 + r * Math.cos(rad(-135));
  const sy    = 50 + r * Math.sin(rad(-135));
  return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${x} ${y}`;
}

function ArcGauge({ pct = 0, label, value, icon: Icon, color = "#ED1C24" }) {
  const prev = useRef(pct);
  const [displayed, setDisplayed] = useState(pct);

  useEffect(() => {
    // smooth interpolation
    const start = prev.current;
    const end   = pct;
    const dur   = 600;
    const t0    = performance.now();
    let raf;
    const step = (now) => {
      const progress = Math.min((now - t0) / dur, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      setDisplayed(start + (end - start) * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
      else prev.current = end;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [pct]);

  const bgPath  = arc(100);
  const fgPath  = arc(displayed);

  return (
    <div className="flex flex-col items-center gap-1 min-w-0">
      <div className="relative w-20 h-20 shrink-0">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90" style={{ transform: "rotate(0deg)" }}>
          {/* Track */}
          <path d={bgPath} fill="none" stroke="#27272A" strokeWidth="8" strokeLinecap="round" />
          {/* Value */}
          <path
            d={fgPath}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 4px ${color}66)` }}
          />
        </svg>
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          {Icon && <Icon className="w-4 h-4" style={{ color }} />}
        </div>
      </div>
      <div className="font-mono text-sm text-white tabular-nums text-center leading-tight">
        {value}
      </div>
      <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider text-center">
        {label}
      </div>
    </div>
  );
}

function StatRow({ label, value, pct, color = "#ED1C24" }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider">{label}</span>
        <span className="font-mono text-xs text-white tabular-nums">{value}</span>
      </div>
      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${Math.max(2, Math.min(100, pct))}%`,
            background: `linear-gradient(90deg, ${color}99, ${color})`,
            boxShadow: `0 0 6px ${color}66`,
          }}
        />
      </div>
    </div>
  );
}

/* ── main component ──────────────────────────────────────────────────────── */
export default function TelemetryWidget() {
  const [t, setT]     = useState(null);
  const [blink, setBlink] = useState(false);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const data = await forgesight.getTelemetry();
        if (alive) {
          setT(data);
          setBlink((b) => !b);
        }
      } catch {}
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const status = t?.status ?? "—";
  const isLive = status === "Connected";
  const isLimited = status === "Limited";

  const statusColor = isLive ? "#10B981" : isLimited ? "#F59E0B" : "#71717A";
  const statusLabel = isLive ? "LIVE" : isLimited ? "LIMITED" : "OFFLINE";

  const vramPct       = t ? (t.vram_used_gb / t.vram_total_gb) * 100 : 0;
  const tokensPct     = t ? (t.tokens_per_sec / 4000) * 100 : 0;
  const powerPct      = t ? (t.power_watts / 750) * 100 : 0;

  return (
    <div
      className="border bg-[#0d0d10] p-5 fs-corners"
      style={{
        borderColor: isLive ? "#10B98133" : "#27272A",
        boxShadow: isLive ? "0 0 20px #10B98111" : "none",
        transition: "border-color 0.6s, box-shadow 0.6s",
      }}
      data-testid="telemetry-widget"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5" style={{ color: statusColor }} />
          <span className="fs-label">Live Telemetry</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Pulse dot */}
          <span
            className="w-2 h-2 rounded-full inline-block"
            style={{
              background: statusColor,
              boxShadow: isLive ? `0 0 6px ${statusColor}` : "none",
              opacity: isLive && blink ? 1 : isLive ? 0.5 : 0.3,
              transition: "opacity 0.5s",
            }}
          />
          <span
            className="font-mono text-[10px] tracking-widest px-2 py-0.5 border rounded"
            style={{ color: statusColor, borderColor: `${statusColor}44`, background: `${statusColor}11` }}
            data-testid="telemetry-status-badge"
          >
            {statusLabel}
          </span>
        </div>
      </div>

      {/* Device */}
      <div className="font-mono text-[10px] text-zinc-600 mb-4 flex items-center justify-between">
        <span>{t?.device ?? "AMD Instinct MI300X"}</span>
        {t?.persistence && (
          <span className="flex items-center gap-1 text-zinc-600">
            <Database className="w-2.5 h-2.5" />
            {t.persistence}
          </span>
        )}
      </div>

      {/* Arc gauges row */}
      <div className="grid grid-cols-3 gap-2 mb-5 pb-5 border-b border-white/5">
        <ArcGauge
          pct={t?.gpu_util_pct ?? 0}
          label="GPU Util"
          value={t ? `${t.gpu_util_pct.toFixed(0)}%` : "—"}
          icon={Cpu}
          color={isLive ? "#ED1C24" : "#3F3F46"}
        />
        <ArcGauge
          pct={vramPct}
          label="VRAM"
          value={t ? `${t.vram_used_gb.toFixed(0)}G` : "—"}
          icon={BarChart3}
          color={isLive ? "#F59E0B" : "#3F3F46"}
        />
        <ArcGauge
          pct={t?.temp_c ? (t.temp_c / 90) * 100 : 0}
          label="Temp"
          value={t ? `${t.temp_c.toFixed(0)}°C` : "—"}
          icon={Thermometer}
          color={isLive ? "#06B6D4" : "#3F3F46"}
        />
      </div>

      {/* Bar stats */}
      <div className="space-y-3">
        <StatRow
          label="Tokens/sec"
          value={t ? t.tokens_per_sec.toLocaleString() : "—"}
          pct={tokensPct}
          color={isLive ? "#10B981" : "#3F3F46"}
        />
        <StatRow
          label="Power Draw"
          value={t ? `${t.power_watts} W` : "—"}
          pct={powerPct}
          color={isLive ? "#ED1C24" : "#3F3F46"}
        />
        <StatRow
          label="VRAM Used"
          value={t ? `${t.vram_used_gb.toFixed(1)} / ${t.vram_total_gb} GB` : "—"}
          pct={vramPct}
          color={isLive ? "#F59E0B" : "#3F3F46"}
        />
      </div>
    </div>
  );
}
