import { Link } from "react-router-dom";
import { ArrowRight, Activity, Eye, Cpu, Megaphone, Layers, Zap } from "lucide-react";

const HERO = "https://static.prod-images.emergentagent.com/jobs/d5829a2e-bc03-4880-adcd-73acc809a3bd/images/184a8bf32b150669152ea3aa72546730d8caad845b1b8eb0233eeb35e4255eeb.png";

export default function Landing() {
  return (
    <div className="text-white" data-testid="landing-page">
      {/* HERO */}
      <section className="relative border-b border-white/10 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${HERO})` }}
        />
        <div className="absolute inset-0 bg-black/70" />
        <div className="absolute inset-0 fs-grid-dots opacity-40" />

        <div className="relative mx-auto max-w-[1400px] px-6 py-24 md:py-32 lg:py-40">
          <div className="flex items-center gap-2 mb-8 fs-rise">
            <span className="fs-chip fs-chip-fail">LIVE DEMO</span>
            <span className="fs-chip">AMD HACKATHON · TRACKS 1 · 2 · 3</span>
            <span className="fs-chip hidden md:inline-flex">QWEN CATEGORY</span>
          </div>

          <h1 className="font-display font-black tracking-tighter leading-[0.88] text-5xl md:text-7xl lg:text-8xl max-w-4xl fs-rise">
            MULTIMODAL<br />
            <span className="fs-stroke">QUALITY-CONTROL</span><br />
            COPILOT.
          </h1>

          <p className="mt-10 max-w-2xl text-zinc-300 text-base md:text-lg leading-relaxed fs-rise">
            ForgeSight ships a 4-agent pipeline that inspects assembly-line images,
            diagnoses root cause, drafts work orders, and publishes reports — fine-tuned
            on <span className="text-white font-semibold">Qwen2-VL</span> and served on
            <span className="text-white font-semibold"> AMD Instinct MI300X</span> via ROCm + vLLM.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-3 fs-rise">
            <Link
              to="/console"
              className="fs-btn fs-btn-primary inline-flex items-center gap-2"
              data-testid="hero-cta-console"
            >
              Run a live inspection <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link to="/blueprint" className="fs-btn inline-flex items-center gap-2" data-testid="hero-cta-blueprint">
              See the MI300X blueprint
            </Link>
          </div>

          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-0 max-w-3xl fs-rise border-t border-white/10">
            <Stat k="192 GB" v="HBM3 per GPU" />
            <Stat k="5.3 TB/s" v="memory bandwidth" />
            <Stat k="4" v="cooperating agents" />
            <Stat k="~6 h" v="QLoRA wall-clock" />
          </div>
        </div>
      </section>

      {/* MANIFESTO */}
      <section className="border-b border-white/10">
        <div className="mx-auto max-w-[1400px] px-6 py-20 grid md:grid-cols-12 gap-10">
          <div className="md:col-span-4">
            <div className="fs-label mb-4">§ 01 · THESIS</div>
            <h2 className="font-display font-black tracking-tighter text-3xl md:text-4xl leading-[0.95]">
              Generic VLMs<br />don't know what<br />a bad weld looks like.
            </h2>
          </div>
          <div className="md:col-span-8 text-zinc-300 space-y-5 text-base leading-relaxed">
            <p>
              Manufacturing QC is context-heavy, privacy-sensitive, and latency-critical.
              Zero-shot vision models hallucinate on defects they've never seen.
            </p>
            <p>
              ForgeSight fine-tunes <span className="text-white">Qwen2-VL</span> on
              domain pairs of <span className="font-mono text-[#ED1C24]">{"{defect image → work order}"}</span>,
              then serves the result with <span className="text-white">vLLM on ROCm</span> across an
              MI300X node. The massive 192 GB HBM3 per device lets us keep the full 72B model resident
              without sharding overhead — real-time inference on the factory floor.
            </p>
            <p>
              Around the model, four cooperating agents (Inspector → Diagnostician → Action → Reporter)
              produce strict-JSON hand-offs so every verdict is auditable.
            </p>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="border-b border-white/10">
        <div className="mx-auto max-w-[1400px] px-6 py-20">
          <div className="flex items-end justify-between mb-12">
            <div>
              <div className="fs-label mb-4">§ 02 · MODULES</div>
              <h2 className="font-display font-black tracking-tighter text-3xl md:text-4xl">What's in the box.</h2>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-0 border-t border-l border-white/10">
            <Feat icon={Eye} title="Inspection Console" body="Drag, drop, inspect. Watch four agents stream strict-JSON hand-offs in real time." to="/console" testid="feat-console" />
            <Feat icon={Activity} title="Defect Feed" body="Every inspection, quality score, and defect-type breakdown — charted live." to="/feed" testid="feat-feed" />
            <Feat icon={Layers} title="Deployment Blueprint" body="The exact stack: MI300X → ROCm → vLLM → Qwen2-VL fine-tune recipe." to="/blueprint" testid="feat-blueprint" />
            <Feat icon={Megaphone} title="Build Journal" body="Every milestone auto-drafts X and LinkedIn posts. Ship it, tell the story." to="/journal" testid="feat-journal" />
            <Feat icon={Cpu} title="Live GPU Telemetry" body="Simulated MI300X util, VRAM, tokens/sec — the factory-floor HMI feel." to="/console" testid="feat-telemetry" />
            <Feat icon={Zap} title="Qwen-first" body="Qwen2-VL for vision, Qwen2.5 for text reasoning. Built for the Qwen category prize." to="/blueprint" testid="feat-qwen" />
          </div>
        </div>
      </section>

      {/* FOOTER CTA */}
      <section className="border-b border-white/10">
        <div className="mx-auto max-w-[1400px] px-6 py-20 text-center">
          <div className="fs-label mb-4">§ 03 · NEXT</div>
          <h2 className="font-display font-black tracking-tighter text-4xl md:text-6xl leading-[0.9]">
            Upload an image.<br />
            <span className="text-[#ED1C24]">Get a verdict in 20 seconds.</span>
          </h2>
          <div className="mt-10 flex items-center justify-center gap-3">
            <Link to="/console" className="fs-btn fs-btn-primary inline-flex items-center gap-2" data-testid="footer-cta-console">
              Open Inspection Console <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-b border-white/10">
        <div className="mx-auto max-w-[1400px] px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="fs-mono-small text-zinc-500">FORGESIGHT · BUILT FOR AMD + LABLAB HACKATHON · FEB 2026</div>
          <div className="flex items-center gap-3">
            <span className="fs-chip">#AMDHACKATHON</span>
            <span className="fs-chip">#ROCM</span>
            <span className="fs-chip">#QWEN</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Stat({ k, v }) {
  return (
    <div className="border-r border-b border-white/10 last:border-r-0 p-4">
      <div className="font-display font-black text-2xl md:text-3xl tracking-tighter">{k}</div>
      <div className="fs-mono-small text-zinc-500 uppercase mt-1">{v}</div>
    </div>
  );
}

function Feat({ icon: Icon, title, body, to, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="group border-r border-b border-white/10 p-8 hover:bg-[#141416] transition-colors block"
    >
      <Icon className="w-5 h-5 text-[#ED1C24] mb-5" />
      <div className="font-display font-bold text-lg mb-2">{title}</div>
      <div className="text-sm text-zinc-400 leading-relaxed">{body}</div>
      <div className="mt-6 fs-mono-small text-zinc-500 group-hover:text-[#ED1C24] transition-colors inline-flex items-center gap-1">
        OPEN <ArrowRight className="w-3 h-3" />
      </div>
    </Link>
  );
}
