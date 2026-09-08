"use client";

import React from "react";
import { Search, Sparkles, BookOpen, FileText, CheckCircle2 } from "lucide-react";

interface ControlCenterProps {
  viewMode: "topics" | "tests";
  setViewMode: (mode: "topics" | "tests") => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  selectedSubject: string;
  setSelectedSubject: (s: string) => void;
  topicsCount: number;
  testsCount: number;
}

export const ControlCenter: React.FC<ControlCenterProps> = ({
  viewMode,
  setViewMode,
  searchQuery,
  setSearchQuery,
  selectedSubject,
  setSelectedSubject,
  topicsCount,
  testsCount,
}) => {
  const subjects = [
    { id: "all", label: "All Subjects" },
    { id: "physics", label: "Physics" },
    { id: "chemistry", label: "Chemistry" },
    { id: "biology", label: "Biology" },
  ];

  return (
    <div className="flex flex-col gap-5 pb-6 border-b border-[#9564DD]/20">
      {/* Top Bar: Minimal Header + Floating Mode Pill Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Minimal Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#3E0F8D] border border-[#9564DD] flex items-center justify-center shadow-neon-purple">
            <Sparkles className="w-5 h-5 text-[#E4DA72]" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-[#EEEEEE] flex items-center gap-2">
              ALLEN NEET <span className="text-[#E4DA72] text-xs px-2 py-0.5 rounded bg-[#E4DA72]/10 border border-[#E4DA72]/30 uppercase font-mono">Intelligence</span>
            </h1>
            <p className="text-xs text-[#EEEEEE]/60">Bidirectional Test ↔ Topic Engine</p>
          </div>
        </div>

        {/* Floating Cyber Mode Switcher Pill */}
        <div className="inline-flex p-1.5 rounded-xl bg-[#0A0518]/80 border border-[#9564DD]/40 backdrop-blur-xl shadow-lg self-start md:self-auto">
          <button
            onClick={() => setViewMode("topics")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all duration-300 ${
              viewMode === "topics"
                ? "bg-[#3E0F8D] text-[#E4DA72] border border-[#9564DD] shadow-neon-purple"
                : "text-[#EEEEEE]/70 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/30"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Topics</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
              viewMode === "topics" ? "bg-[#E4DA72]/20 text-[#E4DA72]" : "bg-[#EEEEEE]/10 text-[#EEEEEE]/60"
            }`}>
              {topicsCount}
            </span>
          </button>

          <button
            onClick={() => setViewMode("tests")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all duration-300 ${
              viewMode === "tests"
                ? "bg-[#3E0F8D] text-[#E4DA72] border border-[#9564DD] shadow-neon-purple"
                : "text-[#EEEEEE]/70 hover:text-[#EEEEEE] hover:bg-[#3E0F8D]/30"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Tests</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
              viewMode === "tests" ? "bg-[#E4DA72]/20 text-[#E4DA72]" : "bg-[#EEEEEE]/10 text-[#EEEEEE]/60"
            }`}>
              {testsCount}
            </span>
          </button>
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-[#9564DD]" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={
            viewMode === "topics"
              ? "Search NEET topics (e.g. 'electric', 'kinematics', 'chemical bond')..."
              : "Search tests by title (e.g. 'MINOR TEST', 'MAJOR')..."
          }
          className="w-full pl-11 pr-12 py-3 bg-[#3E0F8D]/20 border border-[#9564DD]/40 hover:border-[#9564DD] focus:border-[#E4DA72] rounded-xl text-sm text-[#EEEEEE] placeholder-[#EEEEEE]/40 focus:outline-none focus:ring-2 focus:ring-[#9564DD]/40 backdrop-blur-md transition-all duration-200"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-xs text-[#EEEEEE]/50 hover:text-[#EEEEEE]"
          >
            Clear
          </button>
        )}
      </div>

      {/* Subject Filter Chips (Only shown in topics mode) */}
      {viewMode === "topics" && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {subjects.map((s) => {
            const isSelected = selectedSubject === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setSelectedSubject(s.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap ${
                  isSelected
                    ? "bg-[#9564DD] text-[#EEEEEE] shadow-neon-purple font-semibold"
                    : "bg-[#3E0F8D]/30 border border-[#9564DD]/20 text-[#EEEEEE]/70 hover:border-[#9564DD]/50 hover:text-[#EEEEEE]"
                }`}
              >
                {s.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
