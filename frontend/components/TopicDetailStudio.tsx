"use client";

import React, { useEffect, useState } from "react";
import { TopicItem, TopicWithTests, QuestionItem, api } from "@/lib/api";
import {
  X,
  Calendar,
  Layers,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Search,
  Image as ImageIcon,
  FileText,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
} from "lucide-react";

interface TopicDetailStudioProps {
  topic: TopicItem;
  onClose: () => void;
  onInspectTest: (testId: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export const TopicDetailStudio: React.FC<TopicDetailStudioProps> = ({
  topic,
  onClose,
  onInspectTest,
  isExpanded = false,
  onToggleExpand,
}) => {
  const [activeTab, setActiveTab] = useState<"questions" | "tests">("questions");

  // Tests Data
  const [topicDetails, setTopicDetails] = useState<TopicWithTests | null>(null);
  const [loadingTests, setLoadingTests] = useState<boolean>(true);

  // Questions Data
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [totalQuestions, setTotalQuestions] = useState<number>(0);
  const [loadingQuestions, setLoadingQuestions] = useState<boolean>(true);
  const [questionSearch, setQuestionSearch] = useState<string>("");
  const [viewMode, setViewMode] = useState<"visual" | "text">("visual");
  const [enlargedQuestion, setEnlargedQuestion] = useState<QuestionItem | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  useEffect(() => {
    let isMounted = true;
    setLoadingTests(true);
    setLoadingQuestions(true);

    // Fetch tests covering this topic
    api
      .getTopicTests(topic.canonical_key)
      .then((res) => {
        if (isMounted) {
          setTopicDetails(res);
          setLoadingTests(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load topic tests", err);
        if (isMounted) setLoadingTests(false);
      });

    // Fetch questions mapped to this topic
    api
      .getTopicQuestions(topic.canonical_key, { pageSize: 50 })
      .then((res) => {
        if (isMounted) {
          setQuestions(res.items);
          setTotalQuestions(res.total);
          setLoadingQuestions(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load topic questions", err);
        if (isMounted) setLoadingQuestions(false);
      });

    return () => {
      isMounted = false;
    };
  }, [topic.canonical_key]);

  const filteredQuestions = questions.filter((q) => {
    if (!questionSearch.trim()) return true;
    const query = questionSearch.toLowerCase();
    return (
      q.question_text.toLowerCase().includes(query) ||
      (q.test_name && q.test_name.toLowerCase().includes(query)) ||
      q.options.some((opt) => opt.toLowerCase().includes(query))
    );
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (enlargedQuestion) {
          setEnlargedQuestion(null);
        } else if (isExpanded && onToggleExpand) {
          onToggleExpand();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enlargedQuestion, isExpanded, onToggleExpand]);

  return (
    <div className="h-full flex flex-col rounded-2xl bg-[#3E0F8D]/20 border border-[#9564DD]/40 backdrop-blur-xl overflow-hidden shadow-2xl">
      {/* Studio Header */}
      <div className="p-4 border-b border-[#9564DD]/30 bg-[#0A0518]/60 flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${
                topic.subject.toLowerCase() === "physics"
                  ? "bg-[#9564DD]/20 text-[#9564DD] border-[#9564DD]/40"
                  : topic.subject.toLowerCase() === "chemistry"
                  ? "bg-[#E4DA72]/20 text-[#E4DA72] border-[#E4DA72]/40"
                  : "bg-[#EEEEEE]/20 text-[#EEEEEE] border-[#EEEEEE]/40"
              }`}
            >
              {topic.subject}
            </span>
            <span className="text-xs font-mono text-[#EEEEEE]/50 truncate max-w-[200px]">
              {topic.canonical_key}
            </span>
            {topic.target_classes && topic.target_classes.length > 0 && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#E4DA72]/15 border border-[#E4DA72]/30 text-[#E4DA72]">
                {topic.target_classes.includes("11th") && topic.target_classes.includes("12th")
                  ? "Class 11th & 12th"
                  : `Class ${topic.target_classes.join(", ")}`}
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-[#EEEEEE] truncate mt-1">
            {topic.name}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
              title={isExpanded ? "Exit Full Window (Esc)" : "Expand Studio to Full Window"}
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          )}
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Navigation Tabs: Questions vs Scheduled Tests */}
      <div className="flex border-b border-[#9564DD]/20 bg-[#0A0518]/40">
        <button
          onClick={() => setActiveTab("questions")}
          className={`flex-1 py-3 px-4 text-xs font-semibold flex items-center justify-center gap-2 transition-all border-b-2 ${
            activeTab === "questions"
              ? "border-[#E4DA72] text-[#E4DA72] bg-[#E4DA72]/10"
              : "border-transparent text-[#EEEEEE]/60 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/20"
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          <span>
            Questions{" "}
            <span className="font-mono text-[11px] px-1.5 py-0.2 rounded-full bg-[#E4DA72]/20 text-[#E4DA72] ml-1">
              {loadingQuestions ? "..." : totalQuestions}
            </span>
          </span>
        </button>

        <button
          onClick={() => setActiveTab("tests")}
          className={`flex-1 py-3 px-4 text-xs font-semibold flex items-center justify-center gap-2 transition-all border-b-2 ${
            activeTab === "tests"
              ? "border-[#9564DD] text-[#9564DD] bg-[#9564DD]/10"
              : "border-transparent text-[#EEEEEE]/60 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/20"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>
            Scheduled Tests{" "}
            <span className="font-mono text-[11px] px-1.5 py-0.2 rounded-full bg-[#9564DD]/20 text-[#EEEEEE] ml-1">
              {loadingTests ? "..." : topicDetails?.total_tests || topic.test_count}
            </span>
          </span>
        </button>
      </div>

      {/* TAB CONTENT 1: QUESTIONS FEED */}
      {activeTab === "questions" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Subheader Search & View Mode Bar */}
          {questions.length > 0 && (
            <div className="p-3 border-b border-[#9564DD]/20 bg-[#3E0F8D]/10 flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-3.5 h-3.5 text-[#EEEEEE]/40 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search questions in this topic..."
                  value={questionSearch}
                  onChange={(e) => setQuestionSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[#0A0518]/60 border border-[#9564DD]/30 text-xs text-[#EEEEEE] placeholder-[#EEEEEE]/40 focus:outline-none focus:border-[#E4DA72]"
                />
              </div>

              {/* View Mode Toggle: Visual vs Text */}
              <div className="flex items-center p-0.5 rounded-lg bg-[#0A0518]/70 border border-[#9564DD]/30 shrink-0">
                <button
                  onClick={() => setViewMode("visual")}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                    viewMode === "visual"
                      ? "bg-[#9564DD] text-[#EEEEEE] shadow-sm"
                      : "text-[#EEEEEE]/60 hover:text-[#EEEEEE]"
                  }`}
                  title="View original high-fidelity question snippet with diagrams and formulas"
                >
                  <ImageIcon className="w-3.5 h-3.5 text-[#E4DA72]" />
                  <span>Visual PDF</span>
                </button>
                <button
                  onClick={() => setViewMode("text")}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                    viewMode === "text"
                      ? "bg-[#9564DD] text-[#EEEEEE] shadow-sm"
                      : "text-[#EEEEEE]/60 hover:text-[#EEEEEE]"
                  }`}
                  title="View extracted text representation"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Text</span>
                </button>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {loadingQuestions ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 rounded-xl bg-[#3E0F8D]/20 animate-pulse" />
                ))}
              </div>
            ) : filteredQuestions.length === 0 ? (
              <div className="text-center py-16 px-4 text-[#EEEEEE]/60 text-sm flex flex-col items-center">
                <HelpCircle className="w-10 h-10 text-[#9564DD]/40 mb-3" />
                <p className="font-semibold text-base text-[#EEEEEE]">No questions found</p>
                <p className="text-xs text-[#EEEEEE]/50 mt-1 max-w-xs text-center">
                  {questionSearch
                    ? "No questions match your search query."
                    : "No questions from conducted test papers have been mapped to this topic yet."}
                </p>
              </div>
            ) : (
              filteredQuestions.map((q, idx) => (
                <div
                  key={q.id || idx}
                  className="p-4 rounded-xl bg-[#3E0F8D]/25 hover:bg-[#3E0F8D]/35 border border-[#9564DD]/30 hover:border-[#E4DA72]/60 transition-all flex flex-col gap-3 group shadow-lg"
                >
                  {/* Question Header Card */}
                  <div className="flex items-start justify-between gap-2 flex-wrap pb-2 border-b border-[#9564DD]/20">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[#9564DD]/30 border border-[#9564DD]/50 text-[#EEEEEE] font-medium">
                        {q.test_name || q.external_test_id}
                      </span>
                      <span className="font-mono text-[11px] text-[#E4DA72] font-semibold">
                        Q.{q.question_number}
                        {q.subject_question_number && ` (${q.subject} #${q.subject_question_number})`}
                      </span>
                      {q.source_page && (
                        <span className="font-mono text-[10px] text-[#EEEEEE]/40">
                          p. {q.source_page}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5">
                      {q.answer && (
                        <span className="flex items-center gap-1 text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[#E4DA72]/20 border border-[#E4DA72]/40 text-[#E4DA72]">
                          <CheckCircle2 className="w-3 h-3" />
                          Ans: ({q.answer})
                        </span>
                      )}
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#3E0F8D]/50 border border-[#9564DD]/30 text-[#EEEEEE]/60">
                        {q.classification_method} ({Math.round(q.confidence * 100)}%)
                      </span>
                    </div>
                  </div>

                  {/* Question Content: Visual PDF Snippet vs Text */}
                  {viewMode === "visual" ? (
                    <div className="space-y-2">
                      <div className="relative rounded-lg overflow-hidden bg-white/95 border border-[#9564DD]/40 p-2 shadow-inner group/img">
                        <img
                          src={q.image_url ? `http://127.0.0.1:8000${q.image_url}` : `http://127.0.0.1:8000/api/v1/questions/${q.id}/image`}
                          alt={`Question ${q.question_number}`}
                          loading="lazy"
                          className="w-full h-auto object-contain max-h-[520px] rounded"
                          onError={(e) => {
                            // If image fails to load, gracefully fall back to text
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                        <button
                          onClick={() => {
                            setEnlargedQuestion(q);
                            setZoomLevel(1);
                          }}
                          className="absolute top-3 right-3 p-2 rounded-lg bg-[#0A0518]/90 text-[#EEEEEE] opacity-0 group-hover/img:opacity-100 transition-all hover:bg-[#9564DD] hover:text-white shadow-lg border border-[#9564DD]/40"
                          title="Expand Question to Full Window"
                        >
                          <Maximize2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* Question Text */}
                      <div className="text-sm font-medium text-[#EEEEEE] leading-relaxed select-text">
                        {q.question_text}
                      </div>

                      {/* Options (1) - (4) */}
                      {q.options && q.options.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                          {q.options.map((opt, optIdx) => {
                            const optNumber = (optIdx + 1).toString();
                            const isCorrect = q.answer === optNumber;
                            return (
                              <div
                                key={optIdx}
                                className={`p-2 rounded-lg border text-xs flex items-start gap-2 transition-all ${
                                  isCorrect
                                    ? "bg-[#E4DA72]/15 border-[#E4DA72] text-[#E4DA72] font-semibold"
                                    : "bg-[#0A0518]/40 border-[#9564DD]/25 text-[#EEEEEE]/80"
                                }`}
                              >
                                <span
                                  className={`font-mono text-[11px] px-1.5 py-0.2 rounded shrink-0 ${
                                    isCorrect
                                      ? "bg-[#E4DA72] text-[#0A0518] font-bold"
                                      : "bg-[#3E0F8D]/60 text-[#EEEEEE]/60"
                                  }`}
                                >
                                  ({optNumber})
                                </span>
                                <span className="select-text leading-snug">{opt || `Option ${optNumber}`}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </>
                  )}

                  {/* Footer Action */}
                  <div className="pt-2 flex items-center justify-end">
                    <button
                      onClick={() => onInspectTest(q.external_test_id)}
                      className="flex items-center gap-1.5 text-xs text-[#9564DD] hover:text-[#E4DA72] transition-colors font-medium"
                    >
                      <span>View Test Paper</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 2: SCHEDULED TESTS LIST */}
      {activeTab === "tests" && (
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loadingTests ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 rounded-xl bg-[#3E0F8D]/20 animate-pulse" />
              ))}
            </div>
          ) : !topicDetails || topicDetails.tests.length === 0 ? (
            <div className="text-center py-12 text-[#EEEEEE]/50 text-sm">
              No tests found covering this topic yet.
            </div>
          ) : (
            topicDetails.tests.map((t) => (
              <div
                key={t.test_id}
                className="p-4 rounded-xl bg-[#3E0F8D]/25 hover:bg-[#3E0F8D]/40 border border-[#9564DD]/30 hover:border-[#E4DA72] transition-all flex flex-col gap-3 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-bold text-[#EEEEEE] group-hover:text-white">
                      {t.name}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-[#EEEEEE]/60 mt-1 flex-wrap">
                      <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-[#9564DD]/20 border border-[#9564DD]/40 text-[#EEEEEE]">
                        {t.target_class || "12th"} • {t.target_class === "11th" ? "Nurture" : "Leader"}
                      </span>
                      {t.date && (
                        <span className="flex items-center gap-1 font-mono text-[11px]">
                          <Calendar className="w-3 h-3 text-[#9564DD]" />
                          {t.date}
                        </span>
                      )}
                      {t.mode && (
                        <span className="font-mono text-[11px] px-1.5 py-0.2 rounded bg-[#3E0F8D] border border-[#9564DD]/40 text-[#EEEEEE]">
                          {t.mode}
                        </span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => onInspectTest(t.external_test_id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#9564DD]/20 hover:bg-[#9564DD] border border-[#9564DD]/50 text-xs text-[#EEEEEE] font-medium transition-all shadow-sm shrink-0"
                  >
                    <span>View Syllabus</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#E4DA72]" />
                  </button>
                </div>

                {/* Exact source snippet extracted from PDF */}
                {t.source_text && (
                  <div className="text-[11px] font-mono p-2 rounded bg-[#0A0518]/50 border border-[#9564DD]/20 text-[#EEEEEE]/70">
                    <span className="text-[#E4DA72] font-semibold">Matched Syllabus Line: </span>
                    &ldquo;{t.source_text}&rdquo;
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Full-Window Immersion Lightbox for Question Preview */}
      {enlargedQuestion && (
        <div
          className="fixed inset-0 z-[9999] bg-[#0A0518]/95 backdrop-blur-xl flex flex-col p-3 sm:p-6 select-none animate-in fade-in duration-200"
          onClick={() => setEnlargedQuestion(null)}
        >
          {/* Top Floating Control Bar */}
          <div
            className="w-full max-w-7xl mx-auto flex items-center justify-between gap-4 pb-3 border-b border-[#9564DD]/30 shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Question Info Pill */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs px-2.5 py-1 rounded-lg bg-[#3E0F8D] text-[#E4DA72] font-bold border border-[#9564DD]">
                Q.{enlargedQuestion.question_number}
                {enlargedQuestion.subject_question_number && ` (${enlargedQuestion.subject} #${enlargedQuestion.subject_question_number})`}
              </span>
              {enlargedQuestion.test_name && (
                <span className="text-xs font-semibold text-[#EEEEEE]/90 px-2 py-0.5 rounded bg-[#3E0F8D]/40 border border-[#9564DD]/30">
                  {enlargedQuestion.test_name}
                </span>
              )}
              {enlargedQuestion.source_page && (
                <span className="font-mono text-xs text-[#EEEEEE]/50">
                  Page {enlargedQuestion.source_page}
                </span>
              )}
              {enlargedQuestion.answer && (
                <span className="flex items-center gap-1 font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#E4DA72]/20 border border-[#E4DA72]/50 text-[#E4DA72]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Answer: ({enlargedQuestion.answer})
                </span>
              )}
            </div>

            {/* Zoom Controls & Close Button */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-[#3E0F8D]/40 border border-[#9564DD]/40 text-xs text-[#EEEEEE]">
                <button
                  onClick={() => setZoomLevel((z) => Math.max(0.7, +(z - 0.2).toFixed(1)))}
                  disabled={zoomLevel <= 0.7}
                  className="p-1 rounded hover:bg-[#9564DD]/60 disabled:opacity-40 disabled:hover:bg-transparent transition-all"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="font-mono text-xs px-1.5 min-w-[46px] text-center text-[#E4DA72]">
                  {Math.round(zoomLevel * 100)}%
                </span>
                <button
                  onClick={() => setZoomLevel((z) => Math.min(2.5, +(z + 0.2).toFixed(1)))}
                  disabled={zoomLevel >= 2.5}
                  className="p-1 rounded hover:bg-[#9564DD]/60 disabled:opacity-40 disabled:hover:bg-transparent transition-all"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                {zoomLevel !== 1 && (
                  <button
                    onClick={() => setZoomLevel(1)}
                    className="p-1 rounded hover:bg-[#9564DD]/60 text-[#EEEEEE]/60 hover:text-white transition-all ml-1"
                    title="Reset Zoom"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              <button
                onClick={() => setEnlargedQuestion(null)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-950/60 hover:bg-red-800 border border-red-500/50 text-white text-xs font-semibold transition-all shadow-lg"
                title="Close Full Window (Esc)"
              >
                <X className="w-4 h-4" />
                <span className="hidden sm:inline">Close (Esc)</span>
              </button>
            </div>
          </div>

          {/* Main Full-Window Canvas */}
          <div
            className="flex-1 w-full max-w-7xl mx-auto flex items-center justify-center overflow-auto p-2 sm:p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div
              className="relative max-w-full max-h-full bg-white rounded-2xl p-4 sm:p-8 shadow-2xl border border-white/20 transition-transform duration-100 ease-out overflow-auto"
              style={{
                transform: `scale(${zoomLevel})`,
                transformOrigin: "center center",
              }}
            >
              <img
                src={
                  enlargedQuestion.image_url
                    ? `http://127.0.0.1:8000${enlargedQuestion.image_url}`
                    : `http://127.0.0.1:8000/api/v1/questions/${enlargedQuestion.id}/image`
                }
                alt={`Question ${enlargedQuestion.question_number}`}
                className="w-auto h-auto max-w-[90vw] max-h-[80vh] object-contain rounded select-none"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
