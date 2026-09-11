"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import { QuestionItem } from "@/lib/api";
import { TestSessionState } from "@/lib/stateSync";
import {
  X,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Trophy,
  Award,
  AlertCircle,
  HelpCircle,
  Check,
  ChevronRight,
  LayoutGrid,
  Maximize2,
  Minimize2,
  RefreshCw,
} from "lucide-react";

interface TestModeStudioProps {
  title: string;
  subtitle?: string;
  subject?: string;
  questions: QuestionItem[];
  initialSession?: TestSessionState | null;
  onSaveSession: (session: TestSessionState) => void;
  onClose: () => void;
}

export const TestModeStudio: React.FC<TestModeStudioProps> = ({
  title,
  subtitle,
  subject = "Physics",
  questions,
  initialSession,
  onSaveSession,
  onClose,
}) => {
  const [currentIndex, setCurrentIndex] = useState<number>(() => {
    if (initialSession && initialSession.currentIndex < questions.length) {
      return initialSession.currentIndex;
    }
    return 0;
  });

  // State of answers: key is question id or index string
  const [answers, setAnswers] = useState<
    Record<
      string,
      {
        selectedOption: string;
        isChecked: boolean;
        isCorrect: boolean;
      }
    >
  >(() => initialSession?.answers || {});

  const [isFinished, setIsFinished] = useState<boolean>(() => !!initialSession?.isFinished);
  const [showPalette, setShowPalette] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [isImageModalOpen, setIsImageModalOpen] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);

  const isClosingRef = useRef(false);
  const onSaveRef = useRef(onSaveSession);
  onSaveRef.current = onSaveSession;

  const currentQ = questions[currentIndex];
  const currentKey = currentQ ? (currentQ.id || currentIndex.toString()) : "";
  const currentAnsState = answers[currentKey];

  // Reset zoom & error whenever question index changes
  useEffect(() => {
    setImageError(false);
    setZoomLevel(1);
  }, [currentIndex]);

  // Handle clean exit without triggering re-save loops
  const handleClose = () => {
    isClosingRef.current = true;
    onClose();
  };

  // Sync session state to parent / storage whenever answers or index changes
  useEffect(() => {
    if (isClosingRef.current) return;

    onSaveRef.current({
      active: !isFinished,
      type: subtitle?.includes("Test Paper") ? "test" : "topic",
      identifier: subtitle || title,
      title,
      currentIndex,
      answers,
      isFinished,
    });
  }, [currentIndex, answers, isFinished, title, subtitle]);

  // Handle option selection
  const handleSelectOption = (optNumber: string) => {
    if (!currentQ || currentAnsState?.isChecked) return; // Locked once checked

    setAnswers((prev) => ({
      ...prev,
      [currentKey]: {
        selectedOption: optNumber,
        isChecked: false,
        isCorrect: false,
      },
    }));
  };

  // Check Answer for current question
  const handleCheckAnswer = () => {
    if (!currentQ || !currentAnsState?.selectedOption || currentAnsState.isChecked) return;

    // Standardize comparison: "1" vs "1" or "(1)"
    const chosen = currentAnsState.selectedOption.trim().replace(/[()]/g, "");
    const correct = (currentQ.answer || "").trim().replace(/[()]/g, "");

    const isCorrect = chosen === correct || chosen.toLowerCase() === correct.toLowerCase();

    setAnswers((prev) => ({
      ...prev,
      [currentKey]: {
        selectedOption: currentAnsState.selectedOption,
        isChecked: true,
        isCorrect,
      },
    }));
  };

  // Next / Previous Navigation
  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
    } else {
      setIsFinished(true);
    }
  };

  // Retest All
  const handleRetest = () => {
    setAnswers({});
    setCurrentIndex(0);
    setIsFinished(false);
  };

  // Keyboard accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is inside an input field
      if (["input", "textarea"].includes((e.target as HTMLElement)?.tagName?.toLowerCase())) return;

      if (e.key === "Escape") {
        if (isImageModalOpen) {
          setIsImageModalOpen(false);
        } else {
          handleClose();
        }
      } else if (["1", "2", "3", "4"].includes(e.key) && !isFinished) {
        handleSelectOption(e.key);
      } else if (e.key === "Enter" && !isFinished) {
        if (currentAnsState?.selectedOption && !currentAnsState.isChecked) {
          handleCheckAnswer();
        } else if (currentAnsState?.isChecked) {
          handleNext();
        }
      } else if (e.key === "ArrowRight" && !isFinished) {
        handleNext();
      } else if (e.key === "ArrowLeft" && !isFinished) {
        handlePrev();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, currentAnsState, isFinished, isImageModalOpen]);

  // Aggregate Metrics & NEET Score
  const metrics = useMemo(() => {
    let attempted = 0;
    let correct = 0;
    let incorrect = 0;

    questions.forEach((q, idx) => {
      const key = q.id || idx.toString();
      const ans = answers[key];
      if (ans && ans.isChecked) {
        attempted++;
        if (ans.isCorrect) correct++;
        else incorrect++;
      }
    });

    // NEET scoring: +4 for correct, -1 for incorrect, 0 for unattempted
    const score = correct * 4 - incorrect * 1;
    const maxScore = questions.length * 4;
    const accuracy = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
    const progress = questions.length > 0 ? Math.round((attempted / questions.length) * 100) : 0;

    return {
      attempted,
      correct,
      incorrect,
      unattempted: questions.length - attempted,
      score,
      maxScore,
      accuracy,
      progress,
    };
  }, [questions, answers]);

  if (!questions || questions.length === 0) {
    return (
      <div className="fixed inset-0 z-[100] bg-[#0A0518]/95 backdrop-blur-2xl flex flex-col items-center justify-center p-6 text-center select-none">
        <div className="w-16 h-16 rounded-2xl bg-[#3E0F8D]/40 border border-[#9564DD] flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-[#E4DA72]" />
        </div>
        <h2 className="text-xl font-bold text-[#EEEEEE]">No Questions Available</h2>
        <p className="text-sm text-[#EEEEEE]/60 mt-1 max-w-md">
          There are no extracted questions available for &ldquo;{title}&rdquo; to conduct a test.
        </p>
        <button
          onClick={handleClose}
          className="mt-6 px-6 py-2.5 rounded-xl bg-[#9564DD] hover:bg-[#8048cc] text-white font-medium text-sm transition-all"
        >
          Return to Catalog
        </button>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // RENDER 1: HIGH-IMPACT FINAL SCORECARD
  // --------------------------------------------------------------------------
  if (isFinished) {
    return (
      <div className="fixed inset-0 z-[100] bg-[#0A0518]/95 backdrop-blur-2xl flex flex-col p-4 md:p-8 overflow-y-auto animate-in fade-in zoom-in-95 duration-200">
        <div className="max-w-4xl w-full mx-auto flex flex-col gap-6 py-6">
          {/* Header Controls */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-[#E4DA72] font-semibold">
                NEET Test Mode Results
              </span>
              <h1 className="text-2xl font-bold text-[#EEEEEE] mt-0.5">{title}</h1>
            </div>
            <button
              onClick={handleClose}
              className="p-2.5 rounded-xl bg-[#3E0F8D]/40 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
              title="Close Test Mode"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Hero Scorecard Banner */}
          <div className="relative rounded-2xl p-6 md:p-8 bg-gradient-to-br from-[#3E0F8D]/40 via-[#190933]/70 to-[#0A0518] border border-[#9564DD]/50 shadow-2xl overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2 text-center md:text-left">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E4DA72]/15 border border-[#E4DA72]/30 text-[#E4DA72] text-xs font-semibold">
                <Trophy className="w-3.5 h-3.5" />
                <span>Test Completed</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-extrabold text-[#EEEEEE]">
                {metrics.score >= 0 ? `+${metrics.score}` : metrics.score}{" "}
                <span className="text-lg font-normal text-[#EEEEEE]/50">/ {metrics.maxScore} pts</span>
              </h2>
              <p className="text-xs text-[#EEEEEE]/70 max-w-sm">
                Marked under NEET standard rules: (+4 for correct, -1 for incorrect, 0 for unattempted).
              </p>
            </div>

            {/* Metric Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full md:w-auto">
              <div className="p-3 rounded-xl bg-[#0A0518]/60 border border-[#9564DD]/30 text-center">
                <div className="text-xs text-[#EEEEEE]/50">Accuracy</div>
                <div className="text-xl font-bold text-[#E4DA72] mt-1">{metrics.accuracy}%</div>
              </div>
              <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-center">
                <div className="text-xs text-emerald-300/70">Correct (+4)</div>
                <div className="text-xl font-bold text-emerald-400 mt-1">{metrics.correct}</div>
              </div>
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-center">
                <div className="text-xs text-red-300/70">Incorrect (-1)</div>
                <div className="text-xl font-bold text-red-400 mt-1">{metrics.incorrect}</div>
              </div>
              <div className="p-3 rounded-xl bg-[#0A0518]/60 border border-[#9564DD]/30 text-center">
                <div className="text-xs text-[#EEEEEE]/50">Skipped (0)</div>
                <div className="text-xl font-bold text-[#EEEEEE] mt-1">{metrics.unattempted}</div>
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h3 className="text-base font-bold text-[#EEEEEE]">Question Breakdown</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRetest}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-xs font-semibold text-[#EEEEEE] transition-all shadow-md"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retest All</span>
              </button>
              <button
                onClick={handleClose}
                className="px-5 py-2 rounded-xl bg-[#9564DD] hover:bg-[#8048cc] text-xs font-semibold text-white transition-all shadow-neon-purple"
              >
                Exit Test Mode
              </button>
            </div>
          </div>

          {/* Itemized Question Review List */}
          <div className="space-y-3 pb-8">
            {questions.map((q, idx) => {
              const key = q.id || idx.toString();
              const ansState = answers[key];
              const isChecked = ansState?.isChecked;
              const isCorrect = ansState?.isCorrect;
              const userOpt = ansState?.selectedOption;
              const officialAns = q.answer;

              return (
                <div
                  key={key}
                  onClick={() => {
                    setCurrentIndex(idx);
                    setIsFinished(false);
                  }}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-4 group ${
                    isChecked
                      ? isCorrect
                        ? "bg-emerald-950/20 hover:bg-emerald-950/30 border-emerald-500/40"
                        : "bg-red-950/20 hover:bg-red-950/30 border-red-500/40"
                      : "bg-[#3E0F8D]/15 hover:bg-[#3E0F8D]/30 border-[#9564DD]/20"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono text-xs font-bold border ${
                        isChecked
                          ? isCorrect
                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                            : "bg-red-500/20 border-red-500 text-red-400"
                          : "bg-[#3E0F8D]/40 border-[#9564DD]/40 text-[#EEEEEE]/60"
                      }`}
                    >
                      {idx + 1}
                    </span>

                    <div>
                      <div className="text-xs font-semibold text-[#EEEEEE] group-hover:text-white flex items-center gap-2">
                        <span>
                          Q.{q.question_number}
                          {q.subject_question_number && ` (${q.subject} #${q.subject_question_number})`}
                        </span>
                        {q.test_name && (
                          <span className="font-mono text-[10px] text-[#EEEEEE]/40 truncate max-w-[240px]">
                            {q.test_name}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-[#EEEEEE]/50 mt-0.5 line-clamp-1">
                        {q.question_text || "Visual PDF Snippet"}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-mono font-medium">
                        {isChecked ? (
                          isCorrect ? (
                            <span className="text-emerald-400 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Your Choice: ({userOpt}) [+4]
                            </span>
                          ) : (
                            <span className="text-red-400 font-bold flex items-center gap-1">
                              <XCircle className="w-3.5 h-3.5" />
                              Your Choice: ({userOpt}) [-1]
                            </span>
                          )
                        ) : (
                          <span className="text-[#EEEEEE]/40">Unattempted [0]</span>
                        )}
                      </div>
                      {officialAns && (
                        <div className="text-[11px] font-mono text-[#E4DA72] mt-0.5">
                          Correct: ({officialAns})
                        </div>
                      )}
                    </div>

                    <ChevronRight className="w-4 h-4 text-[#EEEEEE]/30 group-hover:text-[#E4DA72] group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // RENDER 2: ACTIVE QUESTION-BY-QUESTION TEST STUDIO
  // --------------------------------------------------------------------------
  return (
    <div className="fixed inset-0 z-[100] bg-[#0A0518]/95 backdrop-blur-2xl flex flex-col select-none overflow-hidden animate-in fade-in duration-200">
      {/* Top Header & Ticker Bar */}
      <header className="p-3 sm:p-4 border-b border-[#9564DD]/30 bg-[#0A0518]/80 backdrop-blur-md flex items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={handleClose}
            className="p-2 rounded-xl bg-[#3E0F8D]/40 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
            title="Exit Test Mode"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-[#E4DA72]/20 text-[#E4DA72] border border-[#E4DA72]/40 font-bold">
                Test Mode
              </span>
              <span className="text-xs font-mono text-[#EEEEEE]/50 truncate max-w-[200px]">
                {subject} • {title}
              </span>
            </div>
            <h1 className="text-sm sm:text-base font-bold text-[#EEEEEE] truncate">
              Question {currentIndex + 1} of {questions.length}
            </h1>
          </div>
        </div>

        {/* Center/Right NEET Score HUD & Question Palette Toggle */}
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={() => setShowPalette((v) => !v)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
              showPalette
                ? "bg-[#E4DA72] text-[#0A0518] border-[#E4DA72]"
                : "bg-[#3E0F8D]/40 border-[#9564DD]/40 text-[#EEEEEE] hover:bg-[#9564DD]/50"
            }`}
            title="Toggle Question Palette"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Palette</span>
            <span className="font-mono text-[11px] opacity-80">
              ({metrics.attempted}/{questions.length})
            </span>
          </button>

          {/* NEET Score Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#0A0518]/90 border border-[#9564DD]/40 text-xs">
            <span className="text-[#EEEEEE]/50 text-[11px]">NEET Score:</span>
            <span
              className={`font-mono font-bold ${
                metrics.score > 0
                  ? "text-emerald-400"
                  : metrics.score < 0
                  ? "text-red-400"
                  : "text-[#E4DA72]"
              }`}
            >
              {metrics.score >= 0 ? `+${metrics.score}` : metrics.score}
            </span>
          </div>

          <button
            onClick={() => setIsFinished(true)}
            className="px-3 py-1.5 rounded-xl bg-[#3E0F8D] hover:bg-[#9564DD] border border-[#9564DD] text-xs font-semibold text-[#EEEEEE] transition-all shadow-sm"
          >
            Finish Test
          </button>

          <button
            onClick={handleClose}
            className="p-2 rounded-xl bg-[#3E0F8D]/40 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Progress Line */}
      <div className="w-full bg-[#3E0F8D]/30 h-1 relative shrink-0">
        <div
          className="h-full bg-gradient-to-r from-[#9564DD] to-[#E4DA72] transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
        />
      </div>

      {/* Collapsible Question Palette Drawer */}
      {showPalette && (
        <div className="border-b border-[#9564DD]/30 bg-[#0A0518]/95 p-3 sm:p-4 max-h-48 overflow-y-auto shrink-0 animate-in slide-in-from-top-4 duration-200">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#9564DD]/20 text-xs text-[#EEEEEE]/60">
              <span>Jump to Question</span>
              <div className="flex items-center gap-3 text-[11px]">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" /> Correct
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500" /> Incorrect
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-[#3E0F8D]" /> Unattempted
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {questions.map((q, idx) => {
                const key = q.id || idx.toString();
                const ans = answers[key];
                const isSelected = idx === currentIndex;
                const isChecked = ans?.isChecked;
                const isCorrect = ans?.isCorrect;

                return (
                  <button
                    key={key}
                    onClick={() => {
                      setCurrentIndex(idx);
                    }}
                    className={`w-8 h-8 rounded-lg font-mono text-xs font-bold transition-all border ${
                      isSelected
                        ? "ring-2 ring-[#E4DA72] ring-offset-2 ring-offset-[#0A0518] scale-110"
                        : ""
                    } ${
                      isChecked
                        ? isCorrect
                          ? "bg-emerald-500/25 border-emerald-500 text-emerald-300"
                          : "bg-red-500/25 border-red-500 text-red-300"
                        : "bg-[#3E0F8D]/30 border-[#9564DD]/30 text-[#EEEEEE]/70 hover:bg-[#9564DD]/40"
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Main Interactive Stage */}
      <main className="flex-1 flex flex-col md:flex-row overflow-hidden max-w-7xl w-full mx-auto p-3 sm:p-6 gap-4 sm:gap-6">
        {/* LEFT COLUMN: Question Image / Visual Display */}
        <section className="flex-1 flex flex-col rounded-2xl bg-[#3E0F8D]/15 border border-[#9564DD]/30 overflow-hidden relative shadow-2xl">
          {/* Canvas Subheader */}
          <div className="p-3 border-b border-[#9564DD]/20 bg-[#0A0518]/50 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2.5 py-1 rounded-lg bg-[#3E0F8D] border border-[#9564DD]/50 text-[#E4DA72] font-bold">
                Q.{currentQ.question_number}
                {currentQ.subject_question_number && ` (${currentQ.subject} #${currentQ.subject_question_number})`}
              </span>
              {currentQ.test_name && (
                <span className="text-xs text-[#EEEEEE]/80 font-medium truncate max-w-[240px]">
                  {currentQ.test_name}
                </span>
              )}
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-[#0A0518]/60 border border-[#9564DD]/30 text-xs text-[#EEEEEE]">
                <button
                  onClick={() => setZoomLevel((z) => Math.max(0.7, +(z - 0.2).toFixed(1)))}
                  disabled={zoomLevel <= 0.7}
                  className="p-1 rounded hover:bg-[#9564DD]/40 disabled:opacity-40"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="font-mono text-[11px] px-1 text-[#E4DA72]">
                  {Math.round(zoomLevel * 100)}%
                </span>
                <button
                  onClick={() => setZoomLevel((z) => Math.min(2.5, +(z + 0.2).toFixed(1)))}
                  disabled={zoomLevel >= 2.5}
                  className="p-1 rounded hover:bg-[#9564DD]/40 disabled:opacity-40"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                {zoomLevel !== 1 && (
                  <button
                    onClick={() => setZoomLevel(1)}
                    className="p-1 rounded hover:bg-[#9564DD]/40 text-[#EEEEEE]/50 hover:text-white ml-0.5"
                    title="Reset Zoom"
                  >
                    <RotateCcw className="w-3 h-3" />
                  </button>
                )}
              </div>

              <button
                onClick={() => setIsImageModalOpen(true)}
                className="p-1.5 rounded-lg bg-[#0A0518]/60 hover:bg-[#9564DD]/40 border border-[#9564DD]/30 text-[#EEEEEE]"
                title="Enlarge Image"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Question Visual Container: Clean Exam Booklet Surface */}
          <div className="flex-1 overflow-auto p-4 sm:p-6 flex items-center justify-center bg-black/30">
            <div
              className="relative w-full max-w-3xl bg-white rounded-2xl p-4 sm:p-8 shadow-2xl transition-transform duration-100 ease-out border border-white/20"
              style={{
                transform: `scale(${zoomLevel})`,
                transformOrigin: "center center",
              }}
            >
              {imageError ? (
                /* Fallback only if image fails to load */
                <div className="p-4 text-black select-text">
                  <div className="text-xs font-mono font-bold text-black/40 mb-2 uppercase tracking-wider">
                    Question Text
                  </div>
                  <div className="text-base font-semibold leading-relaxed">
                    {currentQ.question_text || "No question text available."}
                  </div>
                </div>
              ) : (
                <img
                  src={
                    currentQ.image_url
                      ? `http://127.0.0.1:8000${currentQ.image_url}`
                      : `http://127.0.0.1:8000/api/v1/questions/${currentQ.id}/image`
                  }
                  alt={`Question ${currentQ.question_number}`}
                  className="w-full h-auto object-contain max-h-[60vh] select-none rounded"
                  onError={() => setImageError(true)}
                />
              )}
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: 4 Option Cards & Check Answer Control */}
        <section className="w-full md:w-[380px] lg:w-[420px] flex flex-col justify-between gap-4 shrink-0">
          {/* Options Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-[#EEEEEE]/60 px-1">
              <span>Select the correct option (1-4):</span>
              <span className="font-mono text-[11px] text-[#E4DA72]">
                Key: 1, 2, 3, 4
              </span>
            </div>

            {[1, 2, 3, 4].map((optNum) => {
              const optStr = optNum.toString();
              const isSelected = currentAnsState?.selectedOption === optStr;
              const isChecked = !!currentAnsState?.isChecked;
              const officialAns = (currentQ.answer || "").trim().replace(/[()]/g, "");
              const isThisCorrect = isChecked && (optStr === officialAns || optStr.toLowerCase() === officialAns.toLowerCase());
              const isThisWrong = isChecked && isSelected && !currentAnsState.isCorrect;

              // Display option text if extracted
              const optText = currentQ.options && currentQ.options[optNum - 1];

              return (
                <button
                  key={optNum}
                  onClick={() => handleSelectOption(optStr)}
                  disabled={isChecked}
                  className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between gap-3 group relative shadow-md ${
                    isChecked
                      ? isThisCorrect
                        ? "bg-emerald-950/40 border-emerald-500 text-emerald-200 shadow-emerald-950/50"
                        : isThisWrong
                        ? "bg-red-950/40 border-red-500 text-red-200 shadow-red-950/50"
                        : "bg-[#0A0518]/40 border-[#9564DD]/20 text-[#EEEEEE]/40 opacity-60"
                      : isSelected
                      ? "bg-[#3E0F8D]/60 border-[#E4DA72] text-white shadow-neon-yellow scale-[1.01]"
                      : "bg-[#3E0F8D]/20 hover:bg-[#3E0F8D]/35 border-[#9564DD]/30 text-[#EEEEEE] hover:border-[#9564DD]/60"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono text-sm font-bold shrink-0 transition-all ${
                        isChecked
                          ? isThisCorrect
                            ? "bg-emerald-500 text-black font-extrabold"
                            : isThisWrong
                            ? "bg-red-500 text-white font-extrabold"
                            : "bg-[#3E0F8D]/40 text-[#EEEEEE]/40"
                          : isSelected
                          ? "bg-[#E4DA72] text-[#0A0518] font-extrabold"
                          : "bg-[#0A0518]/60 text-[#EEEEEE]/80 border border-[#9564DD]/40 group-hover:border-[#E4DA72]"
                      }`}
                    >
                      {optNum}
                    </span>

                    <span className="text-sm font-medium leading-snug select-text">
                      {optText ? optText : `Option (${optNum})`}
                    </span>
                  </div>

                  {/* Status Indicator Icon */}
                  <div className="shrink-0">
                    {isChecked ? (
                      isThisCorrect ? (
                        <div className="flex items-center gap-1 text-xs font-bold text-emerald-400">
                          <CheckCircle2 className="w-5 h-5" />
                        </div>
                      ) : isThisWrong ? (
                        <div className="flex items-center gap-1 text-xs font-bold text-red-400">
                          <XCircle className="w-5 h-5" />
                        </div>
                      ) : null
                    ) : isSelected ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-[#E4DA72] shadow-neon-yellow" />
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Submission & Score Impact Feedback Card */}
          <div className="p-4 rounded-xl bg-[#0A0518]/70 border border-[#9564DD]/30 flex flex-col gap-3">
            {currentAnsState?.isChecked ? (
              <div className="flex items-center justify-between animate-in fade-in duration-150">
                <div className="flex items-center gap-2">
                  {currentAnsState.isCorrect ? (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>Correct (+4 Points)</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-red-950/60 border border-red-500/50 text-red-300 font-bold text-xs">
                      <XCircle className="w-4 h-4 text-red-400" />
                      <span>Incorrect (-1 Point)</span>
                    </div>
                  )}
                </div>

                <div className="font-mono text-xs text-[#E4DA72] font-semibold">
                  Official Ans: ({currentQ.answer || "N/A"})
                </div>
              </div>
            ) : (
              <button
                onClick={handleCheckAnswer}
                disabled={!currentAnsState?.selectedOption}
                className={`w-full py-3 px-4 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg ${
                  currentAnsState?.selectedOption
                    ? "bg-[#E4DA72] text-[#0A0518] hover:bg-[#d4ca62] shadow-neon-yellow cursor-pointer"
                    : "bg-[#3E0F8D]/30 border border-[#9564DD]/30 text-[#EEEEEE]/30 cursor-not-allowed"
                }`}
              >
                <Check className="w-4 h-4" />
                <span>Check Answer</span>
              </button>
            )}

            {/* Bottom Nav: Prev / Next Question */}
            <div className="flex items-center justify-between gap-2 pt-1 border-t border-[#9564DD]/20">
              <button
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="flex items-center gap-1 px-3 py-2 rounded-lg bg-[#3E0F8D]/40 hover:bg-[#9564DD] disabled:opacity-30 disabled:hover:bg-[#3E0F8D]/40 text-xs font-medium text-[#EEEEEE] transition-all"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>

              <span className="font-mono text-[11px] text-[#EEEEEE]/50">
                {currentIndex + 1} / {questions.length}
              </span>

              <button
                onClick={handleNext}
                className="flex items-center gap-1 px-4 py-2 rounded-lg bg-[#9564DD] hover:bg-[#8048cc] text-xs font-semibold text-white transition-all shadow-neon-purple"
              >
                <span>{currentIndex === questions.length - 1 ? "Finish" : "Next"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Full Window Enlarged Image Lightbox */}
      {isImageModalOpen && (
        <div
          className="fixed inset-0 z-[110] bg-[#0A0518]/95 backdrop-blur-xl flex flex-col p-4 select-none animate-in fade-in duration-200"
          onClick={() => setIsImageModalOpen(false)}
        >
          <div className="flex items-center justify-between pb-3 border-b border-[#9564DD]/30 shrink-0">
            <span className="font-mono text-sm text-[#E4DA72] font-bold">
              Question {currentQ.question_number} Inspection
            </span>
            <button
              onClick={() => setIsImageModalOpen(false)}
              className="px-3 py-1.5 rounded-xl bg-red-950/60 hover:bg-red-800 border border-red-500/50 text-white text-xs font-semibold"
            >
              Close (Esc)
            </button>
          </div>

          <div
            className="flex-1 flex items-center justify-center p-4 overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-white p-6 rounded-2xl max-w-full max-h-full shadow-2xl">
              <img
                src={
                  currentQ.image_url
                    ? `http://127.0.0.1:8000${currentQ.image_url}`
                    : `http://127.0.0.1:8000/api/v1/questions/${currentQ.id}/image`
                }
                alt={`Question ${currentQ.question_number}`}
                className="max-w-[90vw] max-h-[80vh] object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
