import { useEffect, useState } from "react";
import { Eye, Stethoscope, Wrench, FileText, CheckCircle2, AlertTriangle, XCircle, WifiOff } from "lucide-react";

const ICONS = {
  inspector:    Eye,
  diagnostician: Stethoscope,
  action:       Wrench,
  reporter:     FileText,
};

const VERDICT_CONFIG = {
  pass: { label: "PASS", color: "#10B981", Icon: CheckCircle2 },
  warn: { label: "WARN", color: "#F59E0B", Icon: AlertTriangle },
  fail: { label: "FAIL", color: "#ED1C24", Icon: XCircle },
};

// ── Renderers — one per agent role ─────────────────────────────────────────

function InspectorOutput({ parsed, isMock }) {
  const vc = VERDICT_CONFIG[parsed?.verdict] || VERDICT_CONFIG.warn;
  const defects = parsed?.defects || [];
  return (
    <div className="space-y-4">
      {isMock && (
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-yellow-400 font-mono text-xs">
          <WifiOff className="w-3 h-3 shrink-0" />
          AMD server offline — showing demo data. Start the vLLM server for live inference.
        </div>
      )}
      {/* Verdict banner */}
      <div className="flex items-center gap-3 p-4 border rounded" style={{ borderColor: `${vc.color}44`, background: `${vc.color}0d` }}>
        <vc.Icon className="w-5 h-5" style={{ color: vc.color }} />
        <div>
          <div className="font-mono text-xs text-zinc-400 mb-0.5">VERDICT</div>
          <div className="font-display font-black text-xl tracking-tight" style={{ color: vc.color }}>{vc.label}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="font-mono text-xs text-zinc-400 mb-0.5">CONFIDENCE</div>
          <div className="font-display font-black text-xl">{Math.round((parsed?.confidence || 0) * 100)}%</div>
        </div>
      </div>

      {/* Observation */}
      {parsed?.observation && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5">Observation</div>
          <p className="text-sm text-zinc-300 leading-relaxed">{parsed.observation.replace("[LOCAL MOCK — AMD server offline]", "").trim()}</p>
        </div>
      )}

      {/* Defects */}
      {defects.length > 0 && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">Detected Defects ({defects.length})</div>
          <div className="space-y-2">
            {defects.map((d, i) => (
              <div key={i} className="flex gap-3 p-3 border border-white/10 bg-white/[0.02] rounded">
                <div className="shrink-0 w-1.5 rounded-full self-stretch" style={{ background: d.severity === "high" ? "#ED1C24" : d.severity === "medium" ? "#F59E0B" : "#71717A" }} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-0.5">
                    <span className="font-mono text-xs font-bold text-white">{d.type}</span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border" style={{ color: d.severity === "high" ? "#ED1C24" : d.severity === "medium" ? "#F59E0B" : "#71717A", borderColor: "currentColor", background: "transparent" }}>{d.severity?.toUpperCase()}</span>
                    {d.location && <span className="font-mono text-[10px] text-zinc-500">@ {d.location}</span>}
                  </div>
                  <p className="text-xs text-zinc-400">{d.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DiagnosticianOutput({ parsed }) {
  const factors = parsed?.contributing_factors || [];
  return (
    <div className="space-y-3">
      {parsed?.probable_cause && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5">Root Cause</div>
          <p className="text-sm text-zinc-200 leading-relaxed font-medium">{parsed.probable_cause.replace("[LOCAL MOCK]", "").trim()}</p>
        </div>
      )}
      {parsed?.affected_process_step && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5">Affected Process Step</div>
          <span className="font-mono text-xs px-2 py-1 border border-white/20 text-zinc-300">{parsed.affected_process_step}</span>
        </div>
      )}
      {factors.length > 0 && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">Contributing Factors</div>
          <ul className="space-y-1">
            {factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                <span className="text-[#ED1C24] font-mono text-xs mt-0.5 shrink-0">→</span>
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ActionOutput({ parsed }) {
  const steps = parsed?.steps || [];
  const tools = parsed?.parts_or_tools || [];
  const priorityColor = { P0: "#ED1C24", P1: "#F97316", P2: "#F59E0B", P3: "#71717A" }[parsed?.priority] || "#71717A";
  return (
    <div className="space-y-3">
      <div className="flex gap-4 flex-wrap">
        {parsed?.priority && (
          <div>
            <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Priority</div>
            <span className="font-display font-black text-xl" style={{ color: priorityColor }}>{parsed.priority}</span>
          </div>
        )}
        {parsed?.assignee_role && (
          <div>
            <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Assign To</div>
            <span className="font-mono text-sm text-zinc-200">{parsed.assignee_role}</span>
          </div>
        )}
        {parsed?.estimated_minutes && (
          <div>
            <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Est. Time</div>
            <span className="font-mono text-sm text-zinc-200">{parsed.estimated_minutes} min</span>
          </div>
        )}
      </div>
      {steps.length > 0 && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">Work Order Steps</div>
          <ol className="space-y-1.5">
            {steps.map((s, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                <span className="font-mono text-xs text-zinc-500 w-5 shrink-0 text-right">{String(i + 1).padStart(2, "0")}.</span>
                {s}
              </li>
            ))}
          </ol>
        </div>
      )}
      {tools.length > 0 && (
        <div>
          <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">Parts / Tools Required</div>
          <div className="flex flex-wrap gap-1.5">
            {tools.map((t, i) => <span key={i} className="font-mono text-xs px-2 py-1 border border-white/15 text-zinc-400">{t}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}

function ReporterOutput({ parsed }) {
  const tags = parsed?.tags || [];
  return (
    <div className="space-y-3">
      {parsed?.headline && (
        <div className="font-display font-black text-2xl tracking-tighter text-white">{parsed.headline.replace("[Mock]", "").trim()}</div>
      )}
      {parsed?.summary && (
        <p className="text-sm text-zinc-300 leading-relaxed">{parsed.summary}</p>
      )}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((t, i) => (
            <span key={i} className="font-mono text-[10px] px-2 py-1 border border-[#ED1C24]/40 text-[#ED1C24] bg-[#ED1C24]/5">#{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentContent({ agent, isMock }) {
  const { role, output } = agent;
  const parsed = output?.parsed || {};
  if (role === "inspector")     return <InspectorOutput parsed={parsed} isMock={isMock} />;
  if (role === "diagnostician") return <DiagnosticianOutput parsed={parsed} />;
  if (role === "action")        return <ActionOutput parsed={parsed} />;
  if (role === "reporter")      return <ReporterOutput parsed={parsed} />;
  return <pre className="font-mono text-xs text-zinc-400 whitespace-pre-wrap break-words">{JSON.stringify(parsed, null, 2)}</pre>;
}

// ── Main component ──────────────────────────────────────────────────────────

export default function AgentTranscript({ transcript }) {
  const [revealed, setRevealed] = useState(0);

  useEffect(() => {
    if (!transcript) return;
    setRevealed(0);
    const agents = transcript.agents || [];
    agents.forEach((_, i) => {
      setTimeout(() => setRevealed((r) => Math.max(r, i + 1)), i * 400);
    });
  }, [transcript]);

  if (!transcript) return null;
  const agents = transcript.agents || [];

  // Detect mock mode from first agent's source
  const isMock = agents[0]?.output?.source?.includes("mock");

  return (
    <div className="space-y-0 border border-white/10 bg-[#0d0d10]" data-testid="agent-transcript">
      {agents.map((a, idx) => {
        const Icon = ICONS[a.role] || Eye;
        const isVisible = idx < revealed;
        const isActive  = idx === revealed - 1;

        return (
          <div
            key={a.role}
            className={`border-b border-white/10 last:border-b-0 transition-all duration-500 ${isVisible ? "opacity-100" : "opacity-0"}`}
            data-testid={`agent-block-${a.role}`}
          >
            {/* Agent header */}
            <div className={`flex items-center justify-between px-5 py-3 border-b border-white/5 ${isActive ? "bg-[#ED1C24]/5" : "bg-[#141416]"}`}>
              <div className="flex items-center gap-3">
                <div className={`w-7 h-7 flex items-center justify-center border ${isVisible ? "border-[#ED1C24] text-[#ED1C24]" : "border-white/20 text-zinc-500"}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-display font-bold tracking-tight text-sm text-white">{a.label}</div>
                  <div className="font-mono text-[10px] text-zinc-500">{a.model}</div>
                </div>
              </div>
              <StatusPill visible={isVisible} active={isActive} />
            </div>

            {/* Agent body */}
            {isVisible && (
              <div className="p-5">
                <AgentContent agent={a} isMock={isMock} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function StatusPill({ visible, active }) {
  if (!visible) return <span className="fs-chip text-zinc-600">queued</span>;
  if (active)   return <span className="fs-chip" style={{ color: "#ED1C24", borderColor: "#ED1C24", background: "#ED1C2411" }}>complete</span>;
  return <span className="fs-chip fs-chip-pass">complete</span>;
}
