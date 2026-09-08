"use client";

import React, { useEffect, useMemo, useState } from "react";
import { api, TestItem, TopicItem, TestTopicsGrouped } from "@/lib/api";
import { ControlCenter } from "@/components/ControlCenter";
import { TopicCard } from "@/components/TopicCard";
import { TestCard } from "@/components/TestCard";
import { CleanHud } from "@/components/CleanHud";
import { PdfStudio } from "@/components/PdfStudio";
import { TopicDetailStudio } from "@/components/TopicDetailStudio";
import { RefreshCw, AlertCircle, GraduationCap } from "lucide-react";

export default function StudioPage() {
  const [viewMode, setViewMode] = useState<"topics" | "tests">("topics");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<string>("all");
  const [selectedClass, setSelectedClass] = useState<"all" | "12th" | "11th">("12th");

  const [tests, setTests] = useState<TestItem[]>([]);
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Studio Selection States
  const [selectedTest, setSelectedTest] = useState<TestItem | null>(null);
  const [selectedTestTopics, setSelectedTestTopics] = useState<TestTopicsGrouped | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<TopicItem | null>(null);
  const [previewKind, setPreviewKind] = useState<"syllabus" | "question_paper">("syllabus");

  // Initial Load
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [testsRes, topicsRes] = await Promise.all([
        api.getTests({ pageSize: 50 }),
        api.getTopics({ pageSize: 200, sortBy: "test_count", order: "desc" }),
      ]);
      setTests(testsRes.items);
      setTopics(topicsRes.items);
    } catch (err: any) {
      console.error("Failed to load catalog data", err);
      setError("Unable to connect to the backend server. Please ensure the FastAPI backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered Topics
  const filteredTopics = useMemo(() => {
    return topics.filter((t) => {
      const matchesSubject =
        selectedSubject === "all" || t.subject.toLowerCase() === selectedSubject.toLowerCase();
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.canonical_key.toLowerCase().includes(q) ||
        t.aliases.some((a) => a.toLowerCase().includes(q));

      return matchesSubject && matchesQuery;
    });
  }, [topics, selectedSubject, searchQuery]);

  // Filtered Tests
  const filteredTests = useMemo(() => {
    return tests.filter((t) => {
      // If target_class is specified on test, filter accordingly; otherwise default to 12th (Leader)
      const testClass = t.target_class?.toLowerCase() || "12th";
      const matchesClass =
        selectedClass === "all" || testClass === selectedClass.toLowerCase();

      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.external_test_id.toLowerCase().includes(q) ||
        (t.category && t.category.toLowerCase().includes(q));

      return matchesClass && matchesQuery;
    });
  }, [tests, selectedClass, searchQuery]);

  // Select a Test
  const handleSelectTest = async (test: TestItem, kind: "syllabus" | "question_paper" = "syllabus") => {
    setSelectedTopic(null);
    setSelectedTest(test);
    setPreviewKind(kind);

    try {
      const grouped = await api.getTestTopics(test.external_test_id);
      setSelectedTestTopics(grouped);
    } catch (err) {
      console.error("Failed to load test topics", err);
      setSelectedTestTopics(null);
    }
  };

  // Select a Topic
  const handleSelectTopic = (topic: TopicItem) => {
    setSelectedTest(null);
    setSelectedTestTopics(null);
    setSelectedTopic(topic);
  };

  // Quick navigation from topic detail or breakdown to a test
  const handleInspectTestFromTopic = (testId: string) => {
    const found = tests.find((t) => t.external_test_id === testId);
    if (found) {
      handleSelectTest(found, "syllabus");
    } else {
      api.getTestById(testId).then((fullTest) => {
        handleSelectTest(fullTest, "syllabus");
      });
    }
  };

  // Subject Counts for HUD
  const subjectMetrics = useMemo(() => {
    let phys = 0;
    let chem = 0;
    let bio = 0;
    topics.forEach((t) => {
      const s = t.subject.toLowerCase();
      if (s === "physics") phys++;
      else if (s === "chemistry") chem++;
      else if (s === "biology") bio++;
    });
    return { physics: phys, chemistry: chem, biology: bio };
  }, [topics]);

  return (
    <main className="min-h-screen p-4 md:p-8 max-w-[1700px] mx-auto">
      {/* Studio Grid: Left 3D Stream + Right Inline Studio */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT COLUMN: Control Center & 3D Cards Stream (col-span-7) */}
        <section className="lg:col-span-7 flex flex-col gap-6">
          <ControlCenter
            viewMode={viewMode}
            setViewMode={(m) => {
              setViewMode(m);
              setSearchQuery("");
            }}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            selectedSubject={selectedSubject}
            setSelectedSubject={setSelectedSubject}
            selectedClass={selectedClass}
            setSelectedClass={setSelectedClass}
            topicsCount={topics.length}
            testsCount={filteredTests.length}
          />

          {/* Connection Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 flex items-center justify-between gap-3 text-red-200 text-xs">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={loadData}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-900/50 hover:bg-red-800 text-xs text-white"
              >
                <RefreshCw className="w-3 h-3" />
                Retry
              </button>
            </div>
          )}

          {/* Card Stream */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="h-44 rounded-xl bg-[#3E0F8D]/20 border border-[#9564DD]/20 animate-pulse"
                />
              ))}
            </div>
          ) : viewMode === "topics" ? (
            /* TOPICS STREAM */
            filteredTopics.length === 0 ? (
              <div className="text-center py-16 rounded-2xl bg-[#3E0F8D]/10 border border-[#9564DD]/20">
                <p className="text-[#EEEEEE]/50 text-sm">No topics match your query or filter.</p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedSubject("all");
                  }}
                  className="mt-3 px-4 py-1.5 rounded-lg bg-[#3E0F8D] hover:bg-[#9564DD] text-xs text-[#EEEEEE]"
                >
                  Reset Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-12">
                {filteredTopics.map((topic) => (
                  <TopicCard
                    key={topic.id}
                    topic={topic}
                    isSelected={selectedTopic?.id === topic.id}
                    onSelect={handleSelectTopic}
                  />
                ))}
              </div>
            )
          ) : (
            /* TESTS STREAM */
            filteredTests.length === 0 ? (
              <div className="text-center py-16 px-6 rounded-2xl bg-[#3E0F8D]/10 border border-[#9564DD]/20 flex flex-col items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-[#3E0F8D]/40 border border-[#9564DD] flex items-center justify-center shadow-neon-purple">
                  <GraduationCap className="w-6 h-6 text-[#E4DA72]" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#EEEEEE]">
                    {selectedClass === "11th" ? "Class 11th • Nurture Test Series (363131)" : "No tests match your query"}
                  </h3>
                  <p className="text-xs text-[#EEEEEE]/60 max-w-md mt-1">
                    {selectedClass === "11th"
                      ? "Class 11th course selected. Switch to Class 11th in your ALLEN portal tab, or click below to view Class 12th tests."
                      : "Try resetting your search query or mode filters."}
                  </p>
                </div>
                {selectedClass === "11th" ? (
                  <button
                    onClick={() => setSelectedClass("12th")}
                    className="mt-2 px-4 py-2 rounded-xl bg-[#3E0F8D] hover:bg-[#9564DD] border border-[#9564DD] text-xs font-semibold text-[#EEEEEE] transition-all shadow-md"
                  >
                    View Class 12th (Leader) Tests
                  </button>
                ) : (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="mt-3 px-4 py-1.5 rounded-lg bg-[#3E0F8D] hover:bg-[#9564DD] text-xs text-[#EEEEEE]"
                  >
                    Clear Search
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-12">
                {filteredTests.map((test) => (
                  <TestCard
                    key={test.id}
                    test={test}
                    isSelected={selectedTest?.id === test.id}
                    onSelect={(t) => handleSelectTest(t, "syllabus")}
                    onPreviewPdf={(t, kind) => handleSelectTest(t, kind)}
                  />
                ))}
              </div>
            )
          )}
        </section>

        {/* RIGHT COLUMN: Sticky Inline Preview Studio (col-span-5) */}
        <section className="lg:col-span-5 sticky top-8 h-[calc(100vh-4rem)] hidden lg:block">
          {selectedTest ? (
            <PdfStudio
              test={selectedTest}
              topicsGrouped={selectedTestTopics}
              initialKind={previewKind}
              onClose={() => {
                setSelectedTest(null);
                setSelectedTestTopics(null);
              }}
              onSelectTopic={(key) => {
                const found = topics.find((t) => t.canonical_key === key);
                if (found) handleSelectTopic(found);
              }}
            />
          ) : selectedTopic ? (
            <TopicDetailStudio
              topic={selectedTopic}
              onClose={() => setSelectedTopic(null)}
              onInspectTest={handleInspectTestFromTopic}
            />
          ) : (
            <CleanHud
              totalTests={tests.length}
              totalTopics={topics.length}
              physicsCount={subjectMetrics.physics}
              chemistryCount={subjectMetrics.chemistry}
              biologyCount={subjectMetrics.biology}
            />
          )}
        </section>
      </div>

      {/* MOBILE POPUP PREVIEW STUDIO (< lg) */}
      {(selectedTest || selectedTopic) && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/80 backdrop-blur-sm lg:hidden p-2">
          <div className="h-[85vh] w-full rounded-2xl overflow-hidden shadow-2xl">
            {selectedTest ? (
              <PdfStudio
                test={selectedTest}
                topicsGrouped={selectedTestTopics}
                initialKind={previewKind}
                onClose={() => {
                  setSelectedTest(null);
                  setSelectedTestTopics(null);
                }}
                onSelectTopic={(key) => {
                  const found = topics.find((t) => t.canonical_key === key);
                  if (found) handleSelectTopic(found);
                }}
              />
            ) : selectedTopic ? (
              <TopicDetailStudio
                topic={selectedTopic}
                onClose={() => setSelectedTopic(null)}
                onInspectTest={handleInspectTestFromTopic}
              />
            ) : null}
          </div>
        </div>
      )}
    </main>
  );
}
