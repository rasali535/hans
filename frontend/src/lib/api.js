import axios from "axios";

// ── Backend configuration ────────────────────────────────────────────────────
// If running in the browser, we default to the current origin
const CURRENT_ORIGIN = typeof window !== "undefined" ? window.location.origin : "";

// Option A: Traditional FastAPI backend
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || CURRENT_ORIGIN;

// Option B: Hugging Face Spaces Gradio backend
// If we are on a .hf.space domain, we default to using Gradio
const isHFSpace = typeof window !== "undefined" && window.location.hostname.endsWith(".hf.space");
const HF_SPACE_URL = process.env.REACT_APP_HF_SPACE_URL || (isHFSpace ? CURRENT_ORIGIN : "");

// When HF_SPACE_URL is set, the frontend routes all calls through Gradio's
// /api/<fn_name> REST endpoints instead of the FastAPI /api/* routes.
const useGradio = !!HF_SPACE_URL && isHFSpace;

// ── Axios instance for FastAPI mode ──────────────────────────────────────────
export const API = `${BACKEND_URL}/api`;
export const api = axios.create({ baseURL: API, timeout: 180000 });

// ── Gradio API caller ────────────────────────────────────────────────────────
// Gradio exposes each function as a POST endpoint at /api/<api_name>
// Request body: { data: [...args] }
// Response body: { data: [...outputs] }
async function gradioCall(fnName, ...args) {
  const url = `${HF_SPACE_URL}/api/${fnName}`;
  const resp = await axios.post(url, { data: args }, { timeout: 180000 });
  // Gradio returns { data: [output1, output2, ...] }
  // Our functions return a single JSON string → parse it
  const raw = resp.data?.data?.[0];
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch {
      return raw;
    }
  }
  return raw;
}

// ── Unified API adapter ─────────────────────────────────────────────────────
// Drop-in replacement: every page keeps calling `forgesight.getMetrics()` etc.
// Under the hood it routes to either FastAPI or Gradio.

export const forgesight = {
  // GET /api/ → health
  async health() {
    if (useGradio) return gradioCall("health");
    const { data } = await api.get("/");
    return data;
  },

  // POST /api/inspections
  async createInspection({ image_base64, notes, product_spec, source }) {
    if (useGradio) {
      return gradioCall("inspect", image_base64, notes || "", product_spec || "", source || "upload");
    }
    const { data } = await api.post("/inspections", { image_base64, notes, product_spec, source });
    return data;
  },

  // GET /api/inspections
  async listInspections(limit = 50) {
    if (useGradio) return gradioCall("list_inspections", limit);
    const { data } = await api.get("/inspections", { params: { limit } });
    return data;
  },

  // GET /api/metrics
  async getMetrics() {
    if (useGradio) return gradioCall("metrics");
    const { data } = await api.get("/metrics");
    return data;
  },

  // GET /api/telemetry
  async getTelemetry() {
    if (useGradio) return gradioCall("telemetry");
    const { data } = await api.get("/telemetry");
    return data;
  },

  // GET /api/blueprint
  async getBlueprint() {
    if (useGradio) return gradioCall("blueprint");
    const { data } = await api.get("/blueprint");
    return data;
  },

  // GET /api/journal
  async listJournal() {
    if (useGradio) return gradioCall("journal_list");
    const { data } = await api.get("/journal");
    return data;
  },

  // POST /api/journal
  async createJournal({ title, body, tags }) {
    if (useGradio) {
      // Gradio version takes tags as comma-separated string
      const tagsStr = Array.isArray(tags) ? tags.join(", ") : tags || "";
      return gradioCall("journal_create", title, body, tagsStr);
    }
    const { data } = await api.post("/journal", { title, body, tags });
    return data;
  },

  // POST /api/journal/seed
  async seedJournal() {
    if (useGradio) {
      // Gradio auto-seeds on journal_list; no-op here
      return { seeded: 0, reason: "auto-seeded via journal_list" };
    }
    const { data } = await api.post("/journal/seed");
    return data;
  },
};

// ── Utility ─────────────────────────────────────────────────────────────────
export const fileToBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const str = reader.result;
      const comma = str.indexOf(",");
      resolve(comma >= 0 ? str.slice(comma + 1) : str);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
