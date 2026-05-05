/**
 * ReportDownloader — exports an inspection result as PNG or PDF.
 * Uses html2canvas to capture the DOM node passed via `targetRef`,
 * then jsPDF to wrap it into a letter-sized PDF if needed.
 */
import { useRef, useState } from "react";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import { Download, Image as ImageIcon, FileText, Loader2 } from "lucide-react";

async function captureNode(node, scale = 2) {
  return html2canvas(node, {
    backgroundColor: "#0A0A0A",
    scale,
    useCORS: true,
    logging: false,
  });
}

export default function ReportDownloader({ targetRef, inspectionId, disabled }) {
  const [busy, setBusy] = useState(null); // "png" | "pdf" | null

  const filename = `forgesight-report-${(inspectionId || "inspection").slice(0, 8)}`;

  const downloadPNG = async () => {
    if (!targetRef?.current || busy) return;
    setBusy("png");
    try {
      const canvas = await captureNode(targetRef.current, 2);
      const link = document.createElement("a");
      link.download = `${filename}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } finally {
      setBusy(null);
    }
  };

  const downloadPDF = async () => {
    if (!targetRef?.current || busy) return;
    setBusy("pdf");
    try {
      const canvas = await captureNode(targetRef.current, 2);
      const imgData = canvas.toDataURL("image/png");

      // A4 portrait in mm
      const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();

      // Scale image to fit full page width, paginate if tall
      const imgW = canvas.width;
      const imgH = canvas.height;
      const ratio = pageW / (imgW / 2);           // /2 because scale=2
      const scaledH = (imgH / 2) * ratio;

      let yOffset = 0;
      let remaining = scaledH;
      let page = 0;

      while (remaining > 0) {
        if (page > 0) pdf.addPage();
        const sliceH = Math.min(remaining, pageH);
        // sourceY in original canvas pixels
        const srcY = page * pageH * (imgW / 2) / pageW;
        pdf.addImage(
          imgData,
          "PNG",
          0, 0,
          pageW, sliceH,
          undefined, "FAST",
          0,
        );
        remaining -= pageH;
        page++;
      }

      // Metadata
      pdf.setProperties({
        title: `ForgeSight Inspection Report`,
        subject: "Automated QC Report — AMD MI300X × Qwen2-VL",
        author: "ForgeSight",
        creator: "ForgeSight · AMD Developer Hackathon",
      });

      pdf.save(`${filename}.pdf`);
    } finally {
      setBusy(null);
    }
  };

  if (disabled) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="fs-label hidden sm:inline">Export</span>

      {/* PNG */}
      <button
        onClick={downloadPNG}
        disabled={!!busy}
        title="Download as PNG"
        className="fs-chip inline-flex items-center gap-1.5 hover:border-white/40 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        data-testid="download-png-btn"
      >
        {busy === "png" ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : (
          <ImageIcon className="w-3 h-3" />
        )}
        PNG
      </button>

      {/* PDF */}
      <button
        onClick={downloadPDF}
        disabled={!!busy}
        title="Download as PDF"
        className="fs-chip inline-flex items-center gap-1.5 hover:border-white/40 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        data-testid="download-pdf-btn"
      >
        {busy === "pdf" ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : (
          <FileText className="w-3 h-3" />
        )}
        PDF
      </button>
    </div>
  );
}
