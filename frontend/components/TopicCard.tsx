"use client";

import React from "react";
import { TopicItem } from "@/lib/api";
import { TiltCard } from "./TiltCard";
import { Layers, ChevronRight } from "lucide-react";

interface TopicCardProps {
  topic: TopicItem;
  isSelected?: boolean;
  onSelect: (topic: TopicItem) => void;
}

export const TopicCard: React.FC<TopicCardProps> = ({
  topic,
  isSelected = false,
  onSelect,
}) => {
  const getSubjectBadgeStyle = (subject: string) => {
    switch (subject.toLowerCase()) {
      case "physics":
        return "bg-[#9564DD]/20 text-[#9564DD] border-[#9564DD]/40";
      case "chemistry":
        return "bg-[#E4DA72]/20 text-[#E4DA72] border-[#E4DA72]/40";
      case "biology":
        return "bg-[#EEEEEE]/20 text-[#EEEEEE] border-[#EEEEEE]/40";
      default:
        return "bg-[#9564DD]/20 text-[#9564DD] border-[#9564DD]/40";
    }
  };

  return (
    <TiltCard
      active={isSelected}
      onClick={() => onSelect(topic)}
      className="p-5"
    >
      <div className="flex flex-col gap-3">
        {/* Top Header: Subject Badge, Class Badge & Test Count */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span
              className={`text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-md border ${getSubjectBadgeStyle(
                topic.subject
              )}`}
            >
              {topic.subject}
            </span>
            {topic.target_classes && topic.target_classes.length > 0 && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                topic.target_classes.includes("11th") && topic.target_classes.includes("12th")
                  ? "bg-[#E4DA72]/15 text-[#E4DA72] border-[#E4DA72]/30"
                  : "bg-[#3E0F8D]/50 text-[#EEEEEE]/80 border-[#9564DD]/30"
              }`}>
                {topic.target_classes.includes("11th") && topic.target_classes.includes("12th")
                  ? "11th & 12th"
                  : topic.target_classes.join(", ")}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#E4DA72]/15 border border-[#E4DA72]/30 text-[#E4DA72] text-xs font-mono font-medium">
            <Layers className="w-3 h-3" />
            <span>{topic.test_count} {topic.test_count === 1 ? "test" : "tests"}</span>
          </div>
        </div>

        {/* Topic Name */}
        <div>
          <h3 className="text-base font-semibold text-[#EEEEEE] group-hover:text-white leading-snug">
            {topic.name}
          </h3>
          <p className="text-[11px] font-mono text-[#EEEEEE]/50 mt-1 truncate">
            {topic.canonical_key}
          </p>
        </div>

        {/* Card Footer: Action Hint */}
        <div className="pt-2 border-t border-[#9564DD]/15 flex items-center justify-between text-xs">
          <span className="text-[#EEEEEE]/40 text-[11px]">
            Click to view test occurrences
          </span>
          <div className="flex items-center text-[#9564DD] group-hover:text-[#E4DA72] transition-colors">
            <ChevronRight className="w-4 h-4" />
          </div>
        </div>
      </div>
    </TiltCard>
  );
};
