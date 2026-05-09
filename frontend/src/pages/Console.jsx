import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Upload, Image as ImageIcon, PlayCircle, RotateCcw, LayoutList } from "lucide-react";
import { toast } from "sonner";
import { forgesight, fileToBase64 } from "@/lib/api";
import TelemetryWidget from "@/components/TelemetryWidget";
import AgentTranscript from "@/components/AgentTranscript";
import ReportDownloader from "@/components/ReportDownloader";

export default function Console() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [notes, setNotes] = useState("");
  const [spec, setSpec] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef    = useRef(null);
  const reportRef   = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f) return;
    if (!/(jpe?g|png|webp)$/i.test(f.type.split("/")[1] || f.name.split(".").pop())) {
      toast.error("Only JPEG / PNG / WEBP images are supported");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }, []);

  const onDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    handleFile(f);
  };

  const runInspection = async () => {
    if (!file) {
      toast.error("Upload an image first");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const image_base64 = await fileToBase64(file);
      const data = await forgesight.createInspection({
        image_base64,
        notes,
        product_spec: spec,
        source: "upload",
      });
      setResult(data);
      toast.success("Inspection complete");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Inspection failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview("");
    setNotes("");
    setSpec("");
    setResult(null);
  };

  const summary = result?.summary;

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-10" data-testid="console-page">
      <header className="mb-8">
        <div className="fs-label mb-3">§ CONSOLE · REAL-TIME INFERENCE</div>
        <h1 className="font-display font-black tracking-tighter text-4xl md:text-5xl">
          Inspection Console
        </h1>
        <p className="text-zinc-400 mt-3 max-w-2xl">
          Upload a construction site, road infrastructure, or housing image. Four agents will collaborate to deliver a structural or safety verdict.
        </p>
      </header>

      <div className="grid lg:grid-cols-12 gap-6">
        {/* LEFT — input */}
        <div className="lg:col-span-5 space-y-6">
          <div className="border border-white/10 bg-[#141416] p-5 fs-corners">
            <div className="flex items-center justify-between mb-4">
              <span className="fs-label">Specimen</span>
              {file && (
                <button
                  onClick={reset}
                  className="fs-chip hover:text-white hover:border-white/40 inline-flex items-center gap-1"
                  data-testid="reset-btn"
                >
                  <RotateCcw className="w-3 h-3" /> Reset
                </button>
              )}
            </div>

            {!preview ? (
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={onDrop}
                className={`fs-drop ${dragActive ? "fs-drop-active" : ""} h-64 flex flex-col items-center justify-center cursor-pointer`}
                onClick={() => inputRef.current?.click()}
                data-testid="drop-zone"
              >
                <Upload className="w-8 h-8 text-zinc-500 mb-3" />
                <div className="font-mono text-sm text-zinc-300">Drop image here</div>
                <div className="fs-mono-small text-zinc-500 mt-1">or click to browse · JPG · PNG · WEBP</div>
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => handleFile(e.target.files?.[0])}
                  data-testid="file-input"
                />
              </div>
            ) : (
              <div className="relative border border-white/10">
                <img src={preview} alt="specimen" className="w-full h-64 object-cover" data-testid="preview-img" />
                <div className="absolute top-2 left-2 fs-chip bg-black/80">
                  <ImageIcon className="w-3 h-3 inline mr-1" />
                  {file?.name?.slice(0, 28)}
                </div>
              </div>
            )}

            <div className="mt-5 space-y-3">
              <div>
                <div className="fs-label mb-2">Inspector Notes</div>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  placeholder="e.g. site 4, highway foundation, sector B…"
                  className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#ED1C24] outline-none px-3 py-2 font-mono text-sm text-white placeholder-zinc-600"
                  data-testid="notes-input"
                />
              </div>
              <div>
                <div className="fs-label mb-2">Building/Civil Spec (optional)</div>
                <textarea
                  value={spec}
                  onChange={(e) => setSpec(e.target.value)}
                  rows={2}
                  placeholder="e.g. concrete grade C30, max surface crack 0.2mm…"
                  className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#ED1C24] outline-none px-3 py-2 font-mono text-sm text-white placeholder-zinc-600"
                  data-testid="spec-input"
                />
              </div>
              <button
                disabled={loading || !file}
                onClick={runInspection}
                className="fs-btn fs-btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                data-testid="run-inspection-btn"
              >
                {loading ? (
                  <>Running pipeline<span className="fs-cursor" /></>
                ) : (
                  <>
                    <PlayCircle className="w-4 h-4" /> Run inspection
                  </>
                )}
              </button>
            </div>
          </div>

          <TelemetryWidget />
        </div>

        {/* RIGHT — transcript */}
        <div className="lg:col-span-7 space-y-6" ref={reportRef}>
          {summary && (
            <div className="border border-white/10 bg-[#141416] p-5 fs-rise" data-testid="summary-panel">
              <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
                  <SummaryStat label="Verdict" value={summary.verdict.toUpperCase()} kind={summary.verdict} />
                  <SummaryStat label="Confidence" value={`${Math.round(summary.confidence * 100)}%`} />
                  <SummaryStat label="Defects" value={summary.defect_count} />
                  <SummaryStat label="Priority" value={summary.priority} />
                </div>
                <div className="flex items-center gap-4">
                  <Link
                    to="/feed"
                    className="fs-chip inline-flex items-center gap-1.5 hover:border-white/40 hover:text-white transition-colors"
                  >
                    <LayoutList className="w-3 h-3" />
                    Feed
                  </Link>
                  <ReportDownloader
                    targetRef={reportRef}
                    inspectionId={result?.id}
                    disabled={!result}
                  />
                </div>
              </div>
            </div>
          )}

          {result ? (
            <AgentTranscript transcript={result.transcript} />
          ) : (
            <EmptyTranscript loading={loading} />
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryStat({ label, value, kind }) {
  const color =
    kind === "pass" ? "text-[#10B981]" :
    kind === "warn" ? "text-[#F59E0B]" :
    kind === "fail" ? "text-[#ED1C24]" : "text-white";
  return (
    <div>
      <div className="fs-label mb-1">{label}</div>
      <div className={`font-display font-black text-2xl tabular-nums ${color}`}>{value}</div>
    </div>
  );
}

function EmptyTranscript({ loading }) {
  return (
    <div className="border border-white/10 bg-[#0d0d10] fs-scanlines p-10 text-center" data-testid="empty-transcript">
      <div className="fs-label mb-4">Awaiting specimen</div>
      <div className="font-mono text-sm text-zinc-500 max-w-md mx-auto">
        {loading ? (
          <>
            Running 4-agent pipeline
            <span className="fs-cursor" />
          </>
        ) : (
          <>Upload an image and hit <kbd>Run inspection</kbd>. Agents stream their reasoning live.</>
        )}
      </div>
    </div>
  );
}
