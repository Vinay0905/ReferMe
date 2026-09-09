"use client";

import React, { useState } from "react";
import { TestItem, TestTopicsGrouped, api } from "@/lib/api";
import { ExternalLink, X, FileText, CheckCircle2, AlertCircle, ListFilter, Download, Maximize2, Minimize2 } from "lucide-react";

interface PdfStudioProps {
  test: TestItem;
  topicsGrouped?: TestTopicsGrouped | null;
  initialKind?: "syllabus" | "question_paper";
  onClose: () => void;
  onSelectTopic?: (canonicalKey: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export const PdfStudio: React.FC<PdfStudioProps> = ({
  test,
  topicsGrouped,
  initialKind = "syllabus",
  onClose,
  onSelectTopic,
  isExpanded = false,
  onToggleExpand,
}) => {
  const [activeTab, setActiveTab] = useState<"syllabus" | "question_paper" | "breakdown">(initialKind);

  const pdfUrl = api.getArtifactPdfUrl(test.external_test_id, activeTab === "question_paper" ? "question_paper" : "syllabus");

  return (
    <div className="h-full flex flex-col rounded-2xl bg-[#3E0F8D]/20 border border-[#9564DD]/40 backdrop-blur-xl overflow-hidden shadow-2xl">
      {/* Studio Header */}
      <div className="p-4 border-b border-[#9564DD]/30 bg-[#0A0518]/60 flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-[#E4DA72]/20 text-[#E4DA72] border border-[#E4DA72]/40">
              Live Preview
            </span>
            <span className="text-xs font-mono text-[#EEEEEE]/50">ID: {test.external_test_id}</span>
          </div>
          <h2 className="text-base font-bold text-[#EEEEEE] truncate mt-1">
            {test.name}
          </h2>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {activeTab !== "breakdown" && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
              title="Open PDF in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
              title={isExpanded ? "Exit Full Window (Esc)" : "Expand to Full Window"}
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          )}
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
            title="Close Preview"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#0A0518]/40 border-b border-[#9564DD]/20 overflow-x-auto scrollbar-none">
        <button
          onClick={() => setActiveTab("syllabus")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === "syllabus"
              ? "bg-[#9564DD] text-[#EEEEEE] shadow-neon-purple font-semibold"
              : "text-[#EEEEEE]/70 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/30"
          }`}
        >
          <FileText className="w-3.5 h-3.5 text-[#E4DA72]" />
          <span>Syllabus PDF</span>
        </button>

        <button
          onClick={() => test.has_question_paper && setActiveTab("question_paper")}
          disabled={!test.has_question_paper}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === "question_paper"
              ? "bg-[#9564DD] text-[#EEEEEE] shadow-neon-purple font-semibold"
              : test.has_question_paper
              ? "text-[#EEEEEE]/70 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/30"
              : "text-[#EEEEEE]/30 cursor-not-allowed opacity-60"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Question Paper</span>
          {!test.has_question_paper && <span className="text-[10px] text-[#E4DA72]">(Pending)</span>}
        </button>

        <button
          onClick={() => setActiveTab("breakdown")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === "breakdown"
              ? "bg-[#9564DD] text-[#EEEEEE] shadow-neon-purple font-semibold"
              : "text-[#EEEEEE]/70 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/30"
          }`}
        >
          <ListFilter className="w-3.5 h-3.5" />
          <span>Extracted Topics ({topicsGrouped?.total_topics || 0})</span>
        </button>
      </div>

      {/* Main Studio Body */}
      <div className="flex-1 w-full bg-[#0A0518]/90 relative overflow-hidden">
        {activeTab === "breakdown" ? (
          /* Structured Topic Breakdown */
          <div className="h-full overflow-y-auto p-6 space-y-6">
            {!topicsGrouped || topicsGrouped.total_topics === 0 ? (
              <div className="text-center py-12 text-[#EEEEEE]/50 text-sm">
                No topics extracted yet for this test.
              </div>
            ) : (
              <>
                {/* Physics */}
                {topicsGrouped.subjects.physics.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-[#9564DD] font-semibold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#9564DD]" />
                      Physics ({topicsGrouped.subjects.physics.length})
                    </h3>
                    <div className="grid grid-cols-1 gap-2">
                      {topicsGrouped.subjects.physics.map((t) => (
                        <div
                          key={t.canonical_key}
                          onClick={() => onSelectTopic && onSelectTopic(t.canonical_key)}
                          className="p-3 rounded-lg bg-[#3E0F8D]/20 border border-[#9564DD]/30 hover:border-[#E4DA72] cursor-pointer transition-all flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-medium text-[#EEEEEE]">{t.name}</div>
                            <div className="text-[10px] font-mono text-[#EEEEEE]/50 mt-0.5">{t.source_text}</div>
                          </div>
                          <span className="text-[10px] font-mono text-[#E4DA72]">Explore ➔</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Chemistry */}
                {topicsGrouped.subjects.chemistry.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-[#E4DA72] font-semibold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#E4DA72]" />
                      Chemistry ({topicsGrouped.subjects.chemistry.length})
                    </h3>
                    <div className="grid grid-cols-1 gap-2">
                      {topicsGrouped.subjects.chemistry.map((t) => (
                        <div
                          key={t.canonical_key}
                          onClick={() => onSelectTopic && onSelectTopic(t.canonical_key)}
                          className="p-3 rounded-lg bg-[#3E0F8D]/20 border border-[#9564DD]/30 hover:border-[#E4DA72] cursor-pointer transition-all flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-medium text-[#EEEEEE]">{t.name}</div>
                            <div className="text-[10px] font-mono text-[#EEEEEE]/50 mt-0.5">{t.source_text}</div>
                          </div>
                          <span className="text-[10px] font-mono text-[#E4DA72]">Explore ➔</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Biology */}
                {topicsGrouped.subjects.biology.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-[#EEEEEE] font-semibold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#EEEEEE]" />
                      Biology ({topicsGrouped.subjects.biology.length})
                    </h3>
                    <div className="grid grid-cols-1 gap-2">
                      {topicsGrouped.subjects.biology.map((t) => (
                        <div
                          key={t.canonical_key}
                          onClick={() => onSelectTopic && onSelectTopic(t.canonical_key)}
                          className="p-3 rounded-lg bg-[#3E0F8D]/20 border border-[#9564DD]/30 hover:border-[#E4DA72] cursor-pointer transition-all flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-medium text-[#EEEEEE]">{t.name}</div>
                            <div className="text-[10px] font-mono text-[#EEEEEE]/50 mt-0.5">{t.source_text}</div>
                          </div>
                          <span className="text-[10px] font-mono text-[#E4DA72]">Explore ➔</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          /* Live Streamed PDF Embed */
          <iframe
            src={pdfUrl}
            title={`${test.name} - ${activeTab}`}
            className="w-full h-full border-0 bg-white"
          />
        )}
      </div>
    </div>
  );
};
