import { useEffect, useState } from "react";
import { forgesight } from "@/lib/api";
import { Cpu, HardDrive, Server, BookOpen, Bot, Rocket, ArrowDown } from "lucide-react";

const LAYER_ICONS = {
  Hardware: Cpu, Runtime: HardDrive, Serving: Server,
  Model: BookOpen, Agents: Bot, Product: Rocket,
};

const BLUEPRINT_IMG = "https://static.prod-images.emergentagent.com/jobs/d5829a2e-bc03-4880-adcd-73acc809a3bd/images/7251062dc0e36ea4218374b05cc959bc4e6c55a2cf4789a8a2cbc38db6392916.png";

export default function Blueprint() {
  const [data, setData] = useState(null);

  useEffect(() => {
    forgesight.getBlueprint().then((d) => setData(d)).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-10" data-testid="blueprint-page">
      <header className="mb-10 grid md:grid-cols-2 gap-10">
        <div>
          <div className="fs-label mb-3">§ BLUEPRINT · DEPLOYMENT STACK</div>
          <h1 className="font-display font-black tracking-tighter text-4xl md:text-5xl">
            The exact stack<br />we ship on MI300X.
          </h1>
          <p className="text-zinc-400 mt-4 max-w-lg">
            Six layers. Zero CUDA lock-in. Every choice is justified against the constraints
            of a factory-floor deployment: latency, privacy, and model memory footprint.
          </p>
        </div>
        <div className="relative border border-white/10 overflow-hidden min-h-[240px]">
          <img src={BLUEPRINT_IMG} alt="MI300X architecture" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-black/40" />
          <div className="absolute bottom-3 left-3 fs-chip fs-chip-fail bg-black/70">AMD INSTINCT MI300X</div>
        </div>
      </header>

      <section className="mb-16">
        <div className="fs-label mb-6">Stack · top to bottom</div>
        <div className="border-l-2 border-[#ED1C24] pl-0">
          {data?.stack?.map((layer, i) => {
            const Icon = LAYER_ICONS[layer.layer] || Cpu;
            return (
              <div key={i} className="relative">
                <div className="grid md:grid-cols-12 gap-6 border-b border-white/10 p-6 hover:bg-[#141416] transition-colors">
                  <div className="md:col-span-2 flex items-start gap-3">
                    <div className="w-9 h-9 border border-[#ED1C24] text-[#ED1C24] flex items-center justify-center">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="fs-mono-small text-zinc-500">LAYER {String(i + 1).padStart(2, "0")}</div>
                      <div className="font-display font-bold text-sm">{layer.layer}</div>
                    </div>
                  </div>
                  <div className="md:col-span-4">
                    <div className="font-display font-black tracking-tight text-xl">{layer.title}</div>
                    <div className="font-mono text-xs text-zinc-500 mt-1">{layer.detail}</div>
                  </div>
                  <div className="md:col-span-6 text-sm text-zinc-400 leading-relaxed">{layer.why}</div>
                </div>
                {i < (data?.stack?.length || 0) - 1 && (
                  <div className="flex justify-start pl-4 -mt-2 -mb-2">
                    <ArrowDown className="w-3.5 h-3.5 text-[#ED1C24]" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {data?.finetune_recipe && (
        <section className="border border-white/10 bg-[#141416] p-8 fs-corners" data-testid="finetune-recipe">
          <div className="flex items-end justify-between mb-6 flex-wrap gap-3">
            <div>
              <div className="fs-label mb-2">§ FINE-TUNE RECIPE · TRACK 2</div>
              <h2 className="font-display font-black tracking-tighter text-2xl md:text-3xl">QLoRA on Qwen2-VL</h2>
            </div>
            <span className="fs-chip fs-chip-fail">MI300X · 8× GPU</span>
          </div>
          <div className="grid md:grid-cols-2 gap-0 border-t border-l border-white/10">
            <Cell k="BASE MODEL" v={data.finetune_recipe.base_model} />
            <Cell k="DATASET" v={data.finetune_recipe.dataset} />
            <Cell k="METHOD" v={data.finetune_recipe.method} />
            <Cell k="HARDWARE" v={data.finetune_recipe.hardware} />
            <Cell k="WALL CLOCK" v={data.finetune_recipe.expected_wall_clock} />
            <Cell k="SERVING" v={data.finetune_recipe.serve_with} />
          </div>
          <pre className="mt-8 font-mono text-[12px] leading-relaxed text-zinc-300 bg-[#0A0A0A] border border-white/10 p-5 overflow-x-auto">{`# ForgeSight fine-tune — MI300X + ROCm
docker run --device=/dev/kfd --device=/dev/dri \\
  --security-opt seccomp=unconfined --group-add video \\
  rocm/pytorch:latest

pip install "transformers>=4.45" "peft" "bitsandbytes" \\
            "optimum-amd" "datasets" "accelerate" "vllm"

# train
accelerate launch --mixed_precision bf16 train_qlora.py \\
  --base Qwen/Qwen2-VL-72B-Instruct \\
  --data forgesight/qc-10k \\
  --lora_r 64 --lora_alpha 128 \\
  --epochs 3 --batch_size 4 --grad_accum 8

# serve
vllm serve forgesight/qwen2-vl-72b-qc \\
  --tensor-parallel-size 8 --dtype bfloat16 --port 8000`}</pre>
        </section>
      )}
    </div>
  );
}

function Cell({ k, v }) {
  return (
    <div className="border-r border-b border-white/10 p-5">
      <div className="fs-label mb-2">{k}</div>
      <div className="font-mono text-sm text-white break-words">{v}</div>
    </div>
  );
}
