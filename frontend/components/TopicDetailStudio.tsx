"use client";

import React, { useEffect, useState } from "react";
import { TopicItem, TopicWithTests, TestInTopic, api } from "@/lib/api";
import { X, Calendar, Clock, FileText, ArrowRight, Layers, ExternalLink } from "lucide-react";

interface TopicDetailStudioProps {
  topic: TopicItem;
  onClose: () => void;
  onInspectTest: (testId: string) => void;
}

export const TopicDetailStudio: React.FC<TopicDetailStudioProps> = ({
  topic,
  onClose,
  onInspectTest,
}) => {
  const [topicDetails, setTopicDetails] = useState<TopicWithTests | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    api
      .getTopicTests(topic.canonical_key)
      .then((res) => {
        if (isMounted) {
          setTopicDetails(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load topic tests", err);
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [topic.canonical_key]);

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
            <span className="text-xs font-mono text-[#EEEEEE]/50">
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

        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-[#3E0F8D]/60 hover:bg-[#9564DD] border border-[#9564DD]/40 text-[#EEEEEE] transition-all"
          title="Close"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tests Coverage Overview Banner */}
      <div className="px-6 py-4 bg-[#3E0F8D]/15 border-b border-[#9564DD]/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#E4DA72]" />
          <span className="text-xs font-semibold text-[#EEEEEE]">
            Appears in {topicDetails?.total_tests || topic.test_count} Scheduled Tests
          </span>
        </div>
        <span className="text-[11px] font-mono text-[#E4DA72]">BIDIRECTIONAL RADAR</span>
      </div>

      {/* Test List Covering this Topic */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {loading ? (
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
    </div>
  );
};
