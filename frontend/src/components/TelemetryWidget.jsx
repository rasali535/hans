import { useEffect, useState } from "react";
import { forgesight } from "@/lib/api";
import { Activity } from "lucide-react";

export default function TelemetryWidget() {
  const [t, setT] = useState(null);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const data = await forgesight.getTelemetry();
        if (alive) setT(data);
      } catch {}
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const vramPct = t ? (t.vram_used_gb / t.vram_total_gb) * 100 : 0;

  return (
    <div className="border border-white/10 bg-[#141416] p-5 fs-corners" data-testid="telemetry-widget">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-[#ED1C24]" />
          <span className="fs-label">Live Telemetry</span>
        </div>
        <span className="fs-chip fs-chip-warn" data-testid="telemetry-simulated-chip">SIMULATED</span>
      </div>

      <div className="font-mono text-xs text-zinc-500 mb-3">
        {t ? t.device : "AMD Instinct MI300X"}
      </div>

      <div className="space-y-3">
        <Row label="GPU Util" value={t ? `${t.gpu_util_pct.toFixed(1)}%` : "—"} pct={t?.gpu_util_pct || 0} />
        <Row
          label="VRAM"
          value={t ? `${t.vram_used_gb.toFixed(1)} / ${t.vram_total_gb} GB` : "—"}
          pct={vramPct}
        />
        <Row label="Tokens/sec" value={t ? t.tokens_per_sec.toLocaleString() : "—"} pct={t ? (t.tokens_per_sec / 4000) * 100 : 0} />
        <Row label="Power" value={t ? `${t.power_watts} W` : "—"} pct={t ? (t.power_watts / 750) * 100 : 0} />
        <Row label="Temp" value={t ? `${t.temp_c.toFixed(1)} °C` : "—"} pct={t ? (t.temp_c / 90) * 100 : 0} />
      </div>
    </div>
  );
}

function Row({ label, value, pct }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="fs-mono-small text-zinc-500 uppercase">{label}</span>
        <span className="font-mono text-sm text-white tabular-nums">{value}</span>
      </div>
      <div className="fs-bar mt-1.5">
        <div style={{ width: `${Math.max(2, Math.min(100, pct))}%` }} />
      </div>
    </div>
  );
}
