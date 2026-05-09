import { useEffect, useState, useRef } from "react";
import mermaid from "mermaid";
import { forgesight } from "@/lib/api";
import { Cpu, HardDrive, Server, BookOpen, Bot, Rocket, ArrowRight, Terminal, Zap, ShieldCheck } from "lucide-react";

const LAYER_ICONS = {
  Hardware: Cpu, Runtime: HardDrive, Serving: Server,
  Model: BookOpen, Agents: Bot, Product: Rocket,
};

export default function Blueprint() {
  const [data, setData] = useState(null);
  const mermaidRef = useRef(null);

  useEffect(() => {
    forgesight.getBlueprint().then((d) => setData(d)).catch(() => {});
    
    mermaid.initialize({
      theme: "dark",
      startOnLoad: true,
      securityLevel: "loose",
      themeVariables: {
        primaryColor: "#ED1C24",
        primaryTextColor: "#fff",
        primaryBorderColor: "#ED1C24",
        lineColor: "#333",
        secondaryColor: "#141416",
        tertiaryColor: "#0A0A0A",
        fontSize: "12px",
        fontFamily: "JetBrains Mono",
      },
    });
  }, []);

  useEffect(() => {
    if (data && mermaidRef.current) {
      mermaid.contentLoaded();
    }
  }, [data]);

  const pipelineDiagram = `
graph TD
    subgraph "Data Acquisition"
        IMG[Image Feed]
    end

    subgraph "AMD MI300X Cluster"
        VLLM[vLLM Engine]
        QWEN[Qwen2-VL-7B]
        VLLM --- QWEN
    end

    subgraph "Agentic Pipeline"
        I[Inspector Agent]
        D[Diagnose Agent]
        A[Action Agent]
        R[Report Agent]
        I --> D --> A --> R
    end

    IMG --> I
    I -.-> VLLM
    D -.-> VLLM
    A -.-> VLLM
    R -.-> VLLM
    
    classDef device font-family:Inter,fill:#0d0d10,stroke:#333,color:#888
    classDef compute fill:#ED1C24,stroke:#ED1C24,color:#fff,stroke-width:2px
    classDef agent fill:#141416,stroke:#ED1C24,color:#fff,padding:10px
    
    class IMG device
    class VLLM,QWEN compute
    class I,D,A,R agent
  `;

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-10 space-y-20" data-testid="blueprint-page">
      {/* HERO SECTION */}
      <header className="relative py-10 overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[#ED1C24]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/4 -z-10" />
        
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#ED1C24]/30 bg-[#ED1C24]/5 text-[#ED1C24] font-mono text-[10px] tracking-widest uppercase">
              <Zap className="w-3 h-3" /> System Architecture
            </div>
            <h1 className="font-display font-black tracking-tighter text-5xl md:text-7xl leading-[0.9]">
              Built for <span className="text-[#ED1C24]">Pure Performance.</span>
            </h1>
            <p className="text-zinc-400 text-lg max-w-lg leading-relaxed">
              ForgeSight is architected to leverage the massive memory bandwidth of the AMD MI300X. 
              A six-layer stack designed for zero-latency industrial inference.
            </p>
            <div className="flex items-center gap-8 pt-4">
              <Stat label="Hardware" value="MI300X" />
              <Stat label="VRAM" value="192GB" />
              <Stat label="Bandwidth" value="5.3 TB/s" />
            </div>
          </div>

          <div className="glass p-8 fs-glow border-white/5 relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-[#ED1C24]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="mermaid w-full overflow-hidden" ref={mermaidRef}>
              {pipelineDiagram}
            </div>
          </div>
        </div>
      </header>

      {/* STACK LAYERS */}
      <section>
        <div className="flex items-end justify-between mb-10">
          <div>
            <div className="fs-label mb-2">The Stack</div>
            <h2 className="font-display font-black text-3xl tracking-tight">Top-to-Bottom Integration</h2>
          </div>
          <div className="text-zinc-500 font-mono text-xs hidden md:block">06 TOTAL LAYERS</div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.stack?.map((layer, i) => {
            const Icon = LAYER_ICONS[layer.layer] || Cpu;
            return (
              <div key={i} className="glass p-6 group hover:border-[#ED1C24]/50 transition-all duration-500 fs-glow">
                <div className="flex items-start justify-between mb-6">
                  <div className="w-10 h-10 border border-[#ED1C24]/30 group-hover:border-[#ED1C24] text-[#ED1C24] flex items-center justify-center transition-colors">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="font-mono text-[10px] text-zinc-600">L{String(i + 1).padStart(2, "0")}</span>
                </div>
                <div className="space-y-2">
                  <div className="fs-label text-zinc-500">{layer.layer}</div>
                  <h3 className="font-display font-black text-xl group-hover:text-[#ED1C24] transition-colors">{layer.title}</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed min-h-[60px]">{layer.why}</p>
                </div>
                <div className="mt-6 pt-6 border-t border-white/5">
                  <div className="font-mono text-[10px] text-zinc-500 mb-2 uppercase">Tech Spec</div>
                  <div className="text-xs text-white font-mono bg-white/5 px-2 py-1 inline-block">{layer.detail}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* FINETUNE RECIPE */}
      {data?.finetune_recipe && (
        <section className="relative">
          <div className="absolute inset-0 bg-[#ED1C24]/5 blur-[100px] -z-10" />
          <div className="glass p-10 border-white/5 space-y-10">
            <div className="flex items-start justify-between flex-wrap gap-6">
              <div>
                <div className="fs-label mb-2 flex items-center gap-2">
                   <Terminal className="w-3 h-3" /> Training Protocol
                </div>
                <h2 className="font-display font-black tracking-tighter text-4xl">QLoRA Optimization</h2>
                <p className="text-zinc-400 mt-2">Maximum efficiency training recipe for Qwen2-VL-7B.</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-4 py-2 bg-[#ED1C24] text-white font-display font-black text-sm tracking-tight">8× MI300X</div>
                <div className="px-4 py-2 border border-white/10 text-white font-mono text-xs">BF16 MIXED</div>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <SpecItem icon={BookOpen} label="Base Model" value={data.finetune_recipe.base_model} />
              <SpecItem icon={Server} label="Serving Engine" value={data.finetune_recipe.serve_with} />
              <SpecItem icon={ShieldCheck} label="Compute Platform" value={data.finetune_recipe.hardware} />
            </div>

            <div className="relative">
              <div className="absolute top-4 right-4 flex gap-2">
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
              </div>
              <pre className="font-mono text-[13px] leading-relaxed text-zinc-300 bg-[#050505] border border-white/10 p-8 pt-12 overflow-x-auto custom-scrollbar shadow-2xl">
                <code className="text-blue-400"># ForgeSight ROCm Optimized Fine-tune</code>{"\n"}
                <code className="text-[#ED1C24]">accelerate launch</code> --mixed_precision bf16 train_qlora.py \{"\n"}
                {"  "}--base <span className="text-green-400">Qwen/Qwen2-VL-7B-Instruct</span> \{"\n"}
                {"  "}--data <span className="text-green-400">forgesight/qc-industrial-v1</span> \{"\n"}
                {"  "}--lora_r 64 --lora_alpha 128 \{"\n"}
                {"  "}--epochs 3 --batch_size 4 --grad_accum 8{"\n\n"}
                <code className="text-blue-400"># Production Inference</code>{"\n"}
                <code className="text-[#ED1C24]">vllm serve</code> forgesight/qwen2-vl-mi300x \{"\n"}
                {"  "}--enforce-eager --no-enable-chunked-prefill \{"\n"}
                {"  "}--dtype bfloat16 --port 8000
              </pre>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="space-y-1">
      <div className="fs-label">{label}</div>
      <div className="font-display font-black text-2xl text-white tracking-tighter">{value}</div>
    </div>
  );
}

function SpecItem({ icon: Icon, label, value }) {
  return (
    <div className="flex gap-4 items-center p-4 bg-white/[0.02] border border-white/5">
      <Icon className="w-5 h-5 text-[#ED1C24]" />
      <div>
        <div className="fs-label mb-0.5 text-zinc-500">{label}</div>
        <div className="font-mono text-xs text-white">{value}</div>
      </div>
    </div>
  );
}
