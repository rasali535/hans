import { useEffect, useState } from "react";
import { Eye, Stethoscope, Wrench, FileText } from "lucide-react";

const ICONS = {
  inspector: Eye,
  diagnostician: Stethoscope,
  action: Wrench,
  reporter: FileText,
};

/**
 * Pseudo-streams each agent's raw output character-by-character so the user
 * sees live "thinking". The backend returns the full transcript in one shot.
 */
export default function AgentTranscript({ transcript, onDone }) {
  const [visibleIndex, setVisibleIndex] = useState(-1);
  const [visibleChars, setVisibleChars] = useState(0);

  useEffect(() => {
    if (!transcript) return;
    setVisibleIndex(0);
    setVisibleChars(0);
  }, [transcript]);

  useEffect(() => {
    if (!transcript || visibleIndex < 0) return;
    const agents = transcript.agents || [];
    if (visibleIndex >= agents.length) {
      onDone && onDone();
      return;
    }
    const current = agents[visibleIndex];
    const raw = formatRaw(current);
    if (visibleChars < raw.length) {
      const speed = Math.max(4, Math.floor(raw.length / 140));
      const id = setTimeout(() => setVisibleChars((c) => Math.min(raw.length, c + speed)), 16);
      return () => clearTimeout(id);
    }
    const next = setTimeout(() => {
      setVisibleIndex((i) => i + 1);
      setVisibleChars(0);
    }, 320);
    return () => clearTimeout(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transcript, visibleIndex, visibleChars]);

  if (!transcript) return null;
  const agents = transcript.agents || [];

  return (
    <div className="space-y-0 border border-white/10 bg-[#0d0d10] fs-scanlines" data-testid="agent-transcript">
      {agents.map((a, idx) => {
        const Icon = ICONS[a.role] || Eye;
        const active = idx === visibleIndex;
        const done = idx < visibleIndex;
        const raw = formatRaw(a);
        const shown = done ? raw : active ? raw.slice(0, visibleChars) : "";
        return (
          <div
            key={a.role}
            className={`border-b border-white/10 last:border-b-0 p-5 transition-colors ${
              active ? "bg-[#141416]" : "bg-transparent"
            }`}
            data-testid={`agent-block-${a.role}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className={`w-7 h-7 flex items-center justify-center border ${
                    active || done ? "border-[#ED1C24] text-[#ED1C24]" : "border-white/20 text-zinc-500"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-display font-bold tracking-tight text-sm">{a.label}</div>
                  <div className="fs-mono-small text-zinc-500">{a.model}</div>
                </div>
              </div>
              <StatusPill state={done ? "done" : active ? "active" : "pending"} />
            </div>

            <pre className="font-mono text-[12.5px] leading-relaxed text-zinc-300 whitespace-pre-wrap break-words">
              {shown}
              {active && <span className="fs-cursor" />}
              {!done && !active && <span className="text-zinc-600">awaiting upstream…</span>}
            </pre>
          </div>
        );
      })}
    </div>
  );
}

function StatusPill({ state }) {
  if (state === "done") return <span className="fs-chip fs-chip-pass">complete</span>;
  if (state === "active") return <span className="fs-chip fs-chip-fail">streaming</span>;
  return <span className="fs-chip">queued</span>;
}

function formatRaw(agent) {
  const parsed = agent?.output?.parsed;
  if (parsed && !parsed._raw) {
    try {
      return JSON.stringify(parsed, null, 2);
    } catch {
      return agent?.output?.raw || "";
    }
  }
  return agent?.output?.raw || "";
}
