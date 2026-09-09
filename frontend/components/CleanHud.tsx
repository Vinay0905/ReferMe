"use client";

import React from "react";
import { BookOpen, FileCheck, Layers, Sparkles, Activity } from "lucide-react";

interface CleanHudProps {
  totalTests: number;
  totalTopics: number;
  physicsCount: number;
  chemistryCount: number;
  biologyCount: number;
}

export const CleanHud: React.FC<CleanHudProps> = ({
  totalTests,
  totalTopics,
  physicsCount,
  chemistryCount,
  biologyCount,
}) => {
  const safeTotalTopics = Math.max(1, totalTopics);
  const physPct = Math.round((physicsCount / safeTotalTopics) * 100);
  const chemPct = Math.round((chemistryCount / safeTotalTopics) * 100);
  const bioPct = Math.round((biologyCount / safeTotalTopics) * 100);

  return (
    <div className="h-full flex flex-col justify-between p-8 rounded-2xl bg-[#3E0F8D]/15 border border-[#9564DD]/30 backdrop-blur-xl">
      {/* HUD Header */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-[#9564DD]/20">
          <div className="flex items-center gap-2 text-xs font-mono text-[#E4DA72]">
            <Activity className="w-4 h-4 animate-pulse text-[#E4DA72]" />
            <span>INTELLIGENCE RADAR ACTIVE</span>
          </div>
          <span className="text-[11px] font-mono text-[#EEEEEE]/50">v1.0 • SUB-10MS</span>
        </div>

        <div className="mt-8">
          <h2 className="text-2xl font-bold tracking-tight text-[#EEEEEE]">
            NEET Syllabus Studio
          </h2>
          <p className="text-xs text-[#EEEEEE]/60 mt-1.5 leading-relaxed">
            Select any test card to inspect its syllabus or preview its PDF. Select a topic to explore scheduled tests and practice real exam questions.
          </p>
        </div>

        {/* 4 Metric Counter Boxes */}
        <div className="grid grid-cols-2 gap-4 mt-8">
          <div className="p-4 rounded-xl bg-[#3E0F8D]/30 border border-[#9564DD]/40">
            <div className="flex items-center justify-between text-[#9564DD]">
              <Layers className="w-4 h-4" />
              <span className="text-[10px] uppercase tracking-wider font-mono text-[#EEEEEE]/40">Catalog</span>
            </div>
            <div className="text-2xl font-bold font-mono text-[#EEEEEE] mt-2">{totalTopics}</div>
            <div className="text-xs text-[#EEEEEE]/60">Total Topics</div>
          </div>

          <div className="p-4 rounded-xl bg-[#3E0F8D]/30 border border-[#9564DD]/40">
            <div className="flex items-center justify-between text-[#E4DA72]">
              <BookOpen className="w-4 h-4" />
              <span className="text-[10px] uppercase tracking-wider font-mono text-[#EEEEEE]/40">Tests</span>
            </div>
            <div className="text-2xl font-bold font-mono text-[#E4DA72] mt-2">{totalTests}</div>
            <div className="text-xs text-[#EEEEEE]/60">Tests Scheduled</div>
          </div>

          <div className="p-4 rounded-xl bg-[#3E0F8D]/30 border border-[#9564DD]/40">
            <div className="flex items-center justify-between text-[#9564DD]">
              <FileCheck className="w-4 h-4" />
              <span className="text-[10px] uppercase tracking-wider font-mono text-[#EEEEEE]/40">Storage</span>
            </div>
            <div className="text-2xl font-bold font-mono text-[#EEEEEE] mt-2">{totalTests}</div>
            <div className="text-xs text-[#EEEEEE]/60">Syllabi Synced</div>
          </div>

          <div className="p-4 rounded-xl bg-[#3E0F8D]/30 border border-[#9564DD]/40">
            <div className="flex items-center justify-between text-[#E4DA72]">
              <Sparkles className="w-4 h-4" />
              <span className="text-[10px] uppercase tracking-wider font-mono text-[#EEEEEE]/40">Questions</span>
            </div>
            <div className="text-2xl font-bold font-mono text-[#E4DA72] mt-2">3,600</div>
            <div className="text-xs text-[#EEEEEE]/60">Indexed &amp; Mapped</div>
          </div>
        </div>


        {/* Subject Breakdown Distribution Meters */}
        <div className="mt-8 space-y-4">
          <div className="text-xs font-semibold text-[#EEEEEE] uppercase tracking-wider flex items-center justify-between">
            <span>Subject Distribution</span>
            <span className="text-xs font-mono text-[#E4DA72]">{totalTopics} Total</span>
          </div>

          {/* Physics */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-[#EEEEEE]/80">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#9564DD]"></span>
                Physics
              </span>
              <span className="font-mono text-[#EEEEEE]/60">{physicsCount} ({physPct}%)</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[#0A0518] overflow-hidden">
              <div
                className="h-full bg-[#9564DD] rounded-full transition-all duration-500"
                style={{ width: `${physPct}%` }}
              />
            </div>
          </div>

          {/* Chemistry */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-[#EEEEEE]/80">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#E4DA72]"></span>
                Chemistry
              </span>
              <span className="font-mono text-[#EEEEEE]/60">{chemistryCount} ({chemPct}%)</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[#0A0518] overflow-hidden">
              <div
                className="h-full bg-[#E4DA72] rounded-full transition-all duration-500"
                style={{ width: `${chemPct}%` }}
              />
            </div>
          </div>

          {/* Biology */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-[#EEEEEE]/80">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#EEEEEE]"></span>
                Biology
              </span>
              <span className="font-mono text-[#EEEEEE]/60">{biologyCount} ({bioPct}%)</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[#0A0518] overflow-hidden">
              <div
                className="h-full bg-[#EEEEEE] rounded-full transition-all duration-500"
                style={{ width: `${bioPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer Instructions */}
      <div className="pt-6 border-t border-[#9564DD]/20 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0A0518]/60 border border-[#9564DD]/30 text-xs text-[#EEEEEE]/70 font-mono">
          <span className="w-2 h-2 rounded-full bg-[#E4DA72] animate-ping" />
          Click any card to load live preview
        </div>
      </div>
    </div>
  );
};
