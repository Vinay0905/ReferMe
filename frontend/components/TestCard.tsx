"use client";

import React from "react";
import { TestItem } from "@/lib/api";
import { TiltCard } from "./TiltCard";
import { Calendar, Clock, FileText, CheckCircle, AlertCircle, ChevronRight, Eye } from "lucide-react";

interface TestCardProps {
  test: TestItem;
  isSelected?: boolean;
  onSelect: (test: TestItem) => void;
  onPreviewPdf: (test: TestItem, kind: "syllabus" | "question_paper") => void;
}

export const TestCard: React.FC<TestCardProps> = ({
  test,
  isSelected = false,
  onSelect,
  onPreviewPdf,
}) => {
  return (
    <TiltCard
      active={isSelected}
      onClick={() => onSelect(test)}
      className="p-5"
    >
      <div className="flex flex-col gap-4">
        {/* Header: Mode, Status, Category */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            {test.mode && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#3E0F8D] border border-[#9564DD]/50 text-[#EEEEEE]">
                {test.mode}
              </span>
            )}
            {test.category && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#E4DA72]/15 border border-[#E4DA72]/30 text-[#E4DA72]">
                {test.category}
              </span>
            )}
          </div>

          <span
            className={`text-[11px] font-mono px-2 py-0.5 rounded-full ${
              test.status?.toUpperCase().includes("UPCOMING")
                ? "bg-[#E4DA72]/15 text-[#E4DA72] border border-[#E4DA72]/30"
                : "bg-[#9564DD]/20 text-[#9564DD] border border-[#9564DD]/30"
            }`}
          >
            {test.status || "SCHEDULED"}
          </span>
        </div>

        {/* Title */}
        <div>
          <h3 className="text-base font-bold text-[#EEEEEE] group-hover:text-white leading-snug">
            {test.name}
          </h3>
          <p className="text-xs text-[#EEEEEE]/50 font-mono mt-0.5">
            ID: {test.external_test_id}
          </p>
        </div>

        {/* Metadata Badges: Date, Duration */}
        <div className="flex items-center gap-4 text-xs text-[#EEEEEE]/70 flex-wrap">
          {test.date && (
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#9564DD]" />
              <span>{test.date}</span>
            </div>
          )}
          {test.duration_minutes && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#9564DD]" />
              <span>{test.duration_minutes} Mins</span>
            </div>
          )}
        </div>

        {/* Artifact Availability & Quick Action */}
        <div className="pt-3 border-t border-[#9564DD]/15 flex items-center justify-between flex-wrap gap-2">
          {/* Artifacts badges */}
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded ${
                test.has_syllabus
                  ? "bg-[#9564DD]/20 text-[#EEEEEE] border border-[#9564DD]/40"
                  : "bg-[#EEEEEE]/5 text-[#EEEEEE]/40"
              }`}
            >
              <FileText className="w-3 h-3 text-[#E4DA72]" />
              Syllabus
            </span>

            <span
              className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded ${
                test.has_question_paper
                  ? "bg-[#9564DD]/20 text-[#EEEEEE] border border-[#9564DD]/40"
                  : "bg-[#EEEEEE]/5 text-[#EEEEEE]/40"
              }`}
            >
              <CheckCircle className={`w-3 h-3 ${test.has_question_paper ? "text-[#E4DA72]" : "text-[#EEEEEE]/30"}`} />
              Paper
            </span>
          </div>

          {/* Quick PDF Preview Button */}
          {test.has_syllabus && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onPreviewPdf(test, "syllabus");
              }}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#3E0F8D] hover:bg-[#9564DD] border border-[#9564DD] text-xs text-[#EEEEEE] transition-all duration-200 shadow-sm"
              title="Preview Syllabus PDF"
            >
              <Eye className="w-3.5 h-3.5 text-[#E4DA72]" />
              <span>Preview</span>
            </button>
          )}
        </div>
      </div>
    </TiltCard>
  );
};
