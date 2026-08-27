import React, { useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { Modal } from "./Modal";
import { useUIStore } from "../../lib/store/useUIStore";
import { api } from "../../lib/api";

const SAMPLE_CSV = `Date,Merchant,Amount,Category
2026-08-15,Whole Foods Market,92.50,cat-groceries
2026-08-14,Uber Eats Delivery,34.20,cat-dining
2026-08-12,Chevron Fuel,48.00,cat-transport
2026-08-10,Amazon Order,65.99,cat-shopping`;

export const CsvImportModal: React.FC<{ onImported: () => void }> = ({
  onImported,
}) => {
  const { isCsvImportModalOpen, closeCsvImportModal, showToast } = useUIStore();
  const [csvContent, setCsvContent] = useState("");
  const [isImporting, setIsImporting] = useState(false);

  const handleImport = async () => {
    if (!csvContent.trim()) return;

    setIsImporting(true);
    try {
      const { importedCount } = await api.importTransactionsCSV(csvContent);
      showToast({
        type: "success",
        title: "CSV Import Complete",
        description: `Successfully ingested ${importedCount} transactions.`,
      });
      setCsvContent("");
      closeCsvImportModal();
      onImported();
    } catch (e: any) {
      showToast({
        type: "error",
        title: "Import Failed",
        description: e?.message || "Check your CSV format and column headers.",
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCsvContent(event.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCsvContent(event.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const loadSample = () => {
    setCsvContent(SAMPLE_CSV);
  };

  return (
    <Modal
      isOpen={isCsvImportModalOpen}
      onClose={closeCsvImportModal}
      title="Import Bank CSV / OFX"
      description="Batch upload transactions with automated category resolution"
      maxWidth="md"
    >
      <div className="space-y-4">
        {/* Drop zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          className="border-2 border-dashed border-white/[0.08] hover:border-emerald-500/50 rounded-2xl p-6 text-center bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-300 group"
        >
          <UploadCloud className="w-8 h-8 text-emerald-400 mx-auto mb-2 group-hover:scale-110 transition-transform duration-300" />
          <div className="text-xs font-semibold text-slate-200">
            Drag & drop your CSV file here, or{" "}
            <label className="text-emerald-400 hover:text-emerald-300 hover:underline cursor-pointer font-bold">
              browse
              <input
                type="file"
                accept=".csv,.txt"
                onChange={handleFileInput}
                className="hidden"
              />
            </label>
          </div>
          <div className="text-[11px] text-slate-500 mt-1 font-mono">
            Expected headers:{" "}
            <code className="text-slate-300">
              Date, Merchant, Amount, Category
            </code>
          </div>
        </div>

        {/* Text area or sample preview */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1.5 font-mono">
            <span className="text-slate-400 text-[11px]">
              Or paste raw CSV text:
            </span>
            <button
              onClick={loadSample}
              className="text-emerald-400 hover:text-emerald-300 cursor-pointer text-[11px] font-semibold"
            >
              Load Sample Data
            </button>
          </div>
          <textarea
            value={csvContent}
            onChange={(e) => setCsvContent(e.target.value)}
            rows={5}
            placeholder="Date,Merchant,Amount,Category&#10;2026-08-15,Whole Foods,92.50,cat-groceries"
            className="w-full p-3 font-mono text-xs bg-white/[0.03] border border-white/[0.06] rounded-xl text-slate-200 placeholder-slate-600 input-glow"
          />
        </div>

        <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/[0.06]">
          <button
            type="button"
            onClick={closeCsvImportModal}
            className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleImport}
            disabled={isImporting || !csvContent.trim()}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 cursor-pointer btn-glow"
          >
            {isImporting ? "Parsing..." : "Import Transactions"}
          </button>
        </div>
      </div>
    </Modal>
  );
};
