import { useEffect, useState } from "react";
import { forgesight } from "@/lib/api";
import { toast } from "sonner";
import { Twitter, Linkedin, Copy, Plus, Sparkles } from "lucide-react";

export default function Journal() {
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const data = await forgesight.listJournal();
      setItems(data.items || []);
      if ((data.items || []).length === 0) {
        await forgesight.seedJournal();
        const r = await forgesight.listJournal();
        setItems(r.items || []);
      }
    } catch {}
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async () => {
    if (!title.trim() || !body.trim()) {
      toast.error("Title + body required");
      return;
    }
    setBusy(true);
    try {
      const data = await forgesight.createJournal({
        title,
        body,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      setItems((prev) => [data, ...prev]);
      setTitle("");
      setBody("");
      setTags("");
      toast.success("Milestone logged + social drafts generated");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to log milestone");
    } finally {
      setBusy(false);
    }
  };

  const copy = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied`);
    } catch {
      toast.error("Copy failed");
    }
  };

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-10" data-testid="journal-page">
      <header className="mb-8">
        <div className="fs-label mb-3">§ JOURNAL · BUILD-IN-PUBLIC</div>
        <h1 className="font-display font-black tracking-tighter text-4xl md:text-5xl">Build Journal</h1>
        <p className="text-zinc-400 mt-3 max-w-2xl">
          Every milestone auto-drafts social posts — X + LinkedIn — ready to ship, hashtags and AMD / lablab mentions baked in.
        </p>
      </header>

      <div className="grid lg:grid-cols-12 gap-6">
        {/* Composer */}
        <aside className="lg:col-span-4">
          <div className="border border-white/10 bg-[#141416] p-5 fs-corners sticky top-20" data-testid="journal-composer">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-3.5 h-3.5 text-[#ED1C24]" />
              <span className="fs-label">New milestone</span>
            </div>
            <div className="space-y-3">
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title…"
                className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#ED1C24] outline-none px-3 py-2 font-mono text-sm"
                data-testid="journal-title-input" />
              <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={5} placeholder="What happened today?"
                className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#ED1C24] outline-none px-3 py-2 font-mono text-sm"
                data-testid="journal-body-input" />
              <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tags, comma, separated"
                className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#ED1C24] outline-none px-3 py-2 font-mono text-sm"
                data-testid="journal-tags-input" />
              <button disabled={busy} onClick={submit}
                className="fs-btn fs-btn-primary w-full inline-flex items-center justify-center gap-2 disabled:opacity-50"
                data-testid="journal-submit-btn">
                {busy ? (<>Generating drafts<span className="fs-cursor" /></>) : (<><Plus className="w-4 h-4" /> Log + draft posts</>)}
              </button>
            </div>
          </div>
        </aside>

        {/* Timeline */}
        <section className="lg:col-span-8 space-y-5" data-testid="journal-timeline">
          {items.length === 0 && (
            <div className="border border-white/10 bg-[#141416] p-10 text-center font-mono text-sm text-zinc-500">
              No entries yet. Log your first milestone →
            </div>
          )}
          {items.map((e) => (
            <article key={e.id} className="border border-white/10 bg-[#141416] p-6 fs-rise" data-testid={`journal-entry-${e.id}`}>
              <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="fs-chip fs-chip-fail">{new Date(e.created_at).toLocaleDateString()}</span>
                  {e.tags?.map((t) => (<span key={t} className="fs-chip">#{t}</span>))}
                </div>
              </div>
              <h3 className="font-display font-black tracking-tight text-xl mb-2">{e.title}</h3>
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">{e.body}</p>
              <div className="grid md:grid-cols-2 gap-3 mt-5">
                {e.x_post && (
                  <SocialCard icon={Twitter} label="X POST" text={e.x_post}
                    onCopy={() => copy(e.x_post, "X post")} testid={`x-post-${e.id}`} />
                )}
                {e.linkedin_post && (
                  <SocialCard icon={Linkedin} label="LINKEDIN POST" text={e.linkedin_post}
                    onCopy={() => copy(e.linkedin_post, "LinkedIn post")} testid={`li-post-${e.id}`} />
                )}
              </div>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}

function SocialCard({ icon: Icon, label, text, onCopy, testid }) {
  return (
    <div className="border border-white/10 bg-[#0A0A0A] p-4" data-testid={testid}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="w-3.5 h-3.5 text-[#ED1C24]" />
          <span className="fs-label">{label}</span>
        </div>
        <button onClick={onCopy} className="fs-chip hover:text-white hover:border-white/40 inline-flex items-center gap-1">
          <Copy className="w-3 h-3" /> copy
        </button>
      </div>
      <div className="font-mono text-xs text-zinc-300 leading-relaxed whitespace-pre-line">{text}</div>
    </div>
  );
}
