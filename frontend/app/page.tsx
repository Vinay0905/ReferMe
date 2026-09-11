"use client";

import React, { useEffect, useMemo, useState } from "react";
import { api, TestItem, TopicItem, TestTopicsGrouped, QuestionItem } from "@/lib/api";
import { ControlCenter } from "@/components/ControlCenter";
import { TopicCard } from "@/components/TopicCard";
import { TestCard } from "@/components/TestCard";
import { CleanHud } from "@/components/CleanHud";
import { PdfStudio } from "@/components/PdfStudio";
import { TopicDetailStudio } from "@/components/TopicDetailStudio";
import { TestModeStudio } from "@/components/TestModeStudio";
import { getInitialAppState, persistAppState, TestSessionState } from "@/lib/stateSync";
import { RefreshCw, AlertCircle, GraduationCap, GripVertical } from "lucide-react";

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

  // Draggable Split Pane & Full-Window State
  const [splitPercent, setSplitPercent] = useState<number>(52);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isLgScreen, setIsLgScreen] = useState<boolean>(false);
  const [isStudioExpanded, setIsStudioExpanded] = useState<boolean>(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Interactive Test Mode State
  const [testSession, setTestSession] = useState<TestSessionState | null>(null);
  const [testQuestions, setTestQuestions] = useState<QuestionItem[]>([]);
  const [testTitle, setTestTitle] = useState<string>("");
  const [testSubject, setTestSubject] = useState<string>("Physics");

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

  // Launch Test Mode for a Topic
  const handleStartTopicTest = (questions: QuestionItem[], title: string, subject: string) => {
    if (!questions || questions.length === 0) return;
    setTestQuestions(questions);
    setTestTitle(title);
    setTestSubject(subject);
    setTestSession({
      active: true,
      type: "topic",
      identifier: selectedTopic?.canonical_key || title,
      title,
      currentIndex: 0,
      answers: {},
    });
  };

  // Launch Test Mode for a Test Paper
  const handleStartPaperTest = async () => {
    if (!selectedTest) return;
    try {
      const res = await api.getTestQuestions(selectedTest.external_test_id, { pageSize: 250 });
      if (res.items && res.items.length > 0) {
        setTestQuestions(res.items);
        setTestTitle(selectedTest.name);
        setTestSubject("Full Paper");
        setTestSession({
          active: true,
          type: "test",
          identifier: selectedTest.external_test_id,
          title: selectedTest.name,
          currentIndex: 0,
          answers: {},
        });
      } else {
        alert("No questions have been extracted for this test paper yet.");
      }
    } catch (err) {
      console.error("Failed to load questions for test paper", err);
    }
  };

  // Close Test Mode completely and clear session & URL params
  const handleCloseTestMode = () => {
    setTestSession(null);
    setTestQuestions([]);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("testMode");
      url.searchParams.delete("testType");
      url.searchParams.delete("testId");
      url.searchParams.delete("testQ");
      window.history.replaceState(null, "", url.pathname + (url.search ? url.search : ""));
    }
  };

  // Initial Load & State Restoration
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

      // Hydrate state from URL query params & localStorage
      const saved = getInitialAppState();
      if (saved.selectedClass) setSelectedClass(saved.selectedClass);
      if (saved.viewMode) setViewMode(saved.viewMode);
      if (saved.selectedSubject) setSelectedSubject(saved.selectedSubject);
      if (saved.searchQuery) setSearchQuery(saved.searchQuery);
      if (saved.previewKind) setPreviewKind(saved.previewKind as "syllabus" | "question_paper");
      if (saved.isStudioExpanded) setIsStudioExpanded(saved.isStudioExpanded);

      // Restore active topic if present
      if (saved.selectedTopicKey) {
        const foundTopic = topicsRes.items.find(
          (t) => t.canonical_key === saved.selectedTopicKey
        );
        if (foundTopic) {
          setSelectedTopic(foundTopic);
        } else {
          api
            .getTopicById(saved.selectedTopicKey)
            .then((t) => {
              if (t) setSelectedTopic(t);
            })
            .catch(() => {});
        }
      }

      // Restore active test if present
      if (saved.selectedTestId) {
        const foundTest = testsRes.items.find(
          (t) => t.external_test_id === saved.selectedTestId
        );
        if (foundTest) {
          handleSelectTest(foundTest, (saved.previewKind as any) || "syllabus");
        } else {
          api
            .getTestById(saved.selectedTestId)
            .then((t) => {
              if (t) handleSelectTest(t, (saved.previewKind as any) || "syllabus");
            })
            .catch(() => {});
        }
      }

      // Restore active Test Mode session if user was in a test before reload
      if (saved.testSession && saved.testSession.active && saved.testSession.identifier) {
        if (saved.testSession.type === "topic") {
          api
            .getTopicQuestions(saved.testSession.identifier, { pageSize: 100 })
            .then((qRes) => {
              if (qRes.items.length > 0) {
                setTestQuestions(qRes.items);
                setTestTitle(saved.testSession?.title || saved.testSession!.identifier);
                setTestSubject(qRes.items[0]?.subject || "Physics");
                setTestSession(saved.testSession);
              }
            })
            .catch(() => {});
        } else {
          api
            .getTestQuestions(saved.testSession.identifier, { pageSize: 250 })
            .then((qRes) => {
              if (qRes.items.length > 0) {
                setTestQuestions(qRes.items);
                setTestTitle(saved.testSession?.title || saved.testSession!.identifier);
                setTestSubject("Full Paper");
                setTestSession(saved.testSession);
              }
            })
            .catch(() => {});
        }
      }
    } catch (err: any) {
      console.error("Failed to load catalog data", err);
      setError("Unable to connect to the backend server. Please ensure the FastAPI backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Restore saved split preference
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("referme_split_percent");
      if (saved) {
        const parsed = parseFloat(saved);
        if (!isNaN(parsed) && parsed >= 22 && parsed <= 78) {
          setSplitPercent(parsed);
        }
      }
      const checkLg = () => setIsLgScreen(window.innerWidth >= 1024);
      checkLg();
      window.addEventListener("resize", checkLg);
      return () => window.removeEventListener("resize", checkLg);
    }
  }, []);

  // Synchronize state changes to URL query parameters & localStorage
  useEffect(() => {
    if (loading) return; // Do not overwrite while initial catalog data is loading

    persistAppState({
      selectedClass,
      viewMode,
      selectedSubject,
      searchQuery,
      selectedTopicKey: selectedTopic?.canonical_key || null,
      selectedTestId: selectedTest?.external_test_id || null,
      previewKind,
      isStudioExpanded,
      testSession,
    });
  }, [
    loading,
    selectedClass,
    viewMode,
    selectedSubject,
    searchQuery,
    selectedTopic,
    selectedTest,
    previewKind,
    isStudioExpanded,
    testSession,
  ]);

  // Keyboard shortcut to exit full window
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isStudioExpanded) {
        setIsStudioExpanded(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isStudioExpanded]);

  // Pointer drag handlers for split divider
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
    try {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    } catch {}
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const rawPercent = ((e.clientX - rect.left) / rect.width) * 100;
    const clamped = Math.min(78, Math.max(22, rawPercent));
    setSplitPercent(clamped);
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {}
      localStorage.setItem("referme_split_percent", splitPercent.toFixed(1));
    }
  };

  const handleResetSplit = () => {
    setSplitPercent(52);
    localStorage.setItem("referme_split_percent", "52.0");
  };

  // Filtered Topics
  const filteredTopics = useMemo(() => {
    return topics.filter((t) => {
      const matchesSubject =
        selectedSubject === "all" || t.subject.toLowerCase() === selectedSubject.toLowerCase();
      const matchesClass =
        selectedClass === "all" ||
        (t.target_classes && t.target_classes.map((c) => c.toLowerCase()).includes(selectedClass.toLowerCase()));
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.canonical_key.toLowerCase().includes(q) ||
        t.aliases?.some((a) => a.toLowerCase().includes(q));

      return matchesSubject && matchesClass && matchesQuery;
    });
  }, [topics, selectedSubject, selectedClass, searchQuery]);

  // Filtered Tests
  const filteredTests = useMemo(() => {
    return tests.filter((t) => {
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

  // Topics belonging to the active class selection
  const classTopics = useMemo(() => {
    return topics.filter((t) => {
      if (selectedClass === "all") return true;
      return t.target_classes && t.target_classes.map((c) => c.toLowerCase()).includes(selectedClass.toLowerCase());
    });
  }, [topics, selectedClass]);

  // Tests belonging to the active class selection
  const classTests = useMemo(() => {
    return tests.filter((t) => {
      if (selectedClass === "all") return true;
      const testClass = t.target_class?.toLowerCase() || "12th";
      return testClass === selectedClass.toLowerCase();
    });
  }, [tests, selectedClass]);

  // Subject Counts for HUD
  const classSubjectMetrics = useMemo(() => {
    let phys = 0;
    let chem = 0;
    let bio = 0;
    classTopics.forEach((t) => {
      const s = t.subject.toLowerCase();
      if (s === "physics") phys++;
      else if (s === "chemistry") chem++;
      else if (s === "biology") bio++;
    });
    return { physics: phys, chemistry: chem, biology: bio };
  }, [classTopics]);

  return (
    <main className="min-h-screen p-4 md:p-8 max-w-[1700px] mx-auto">
      {/* INTERACTIVE TEST MODE STUDIO OVERLAY */}
      {testSession && testSession.active && testQuestions.length > 0 && (
        <TestModeStudio
          title={testTitle || "NEET Practice Test"}
          subtitle={testSession.identifier}
          subject={testSubject}
          questions={testQuestions}
          initialSession={testSession}
          onSaveSession={(updated) => setTestSession(updated)}
          onClose={handleCloseTestMode}
        />
      )}

      {/* FULL WINDOW STUDIO FOCUS MODE */}
      {isStudioExpanded && (selectedTest || selectedTopic) && (
        <div className="fixed inset-0 z-50 bg-[#0A0518]/95 backdrop-blur-2xl p-3 md:p-6 flex flex-col animate-in fade-in zoom-in-95 duration-200">
          <div className="h-full w-full max-w-[1800px] mx-auto flex flex-col">
            {selectedTest ? (
              <PdfStudio
                test={selectedTest}
                topicsGrouped={selectedTestTopics}
                initialKind={previewKind}
                onClose={() => {
                  setSelectedTest(null);
                  setSelectedTestTopics(null);
                  setIsStudioExpanded(false);
                }}
                onSelectTopic={(key) => {
                  const found = topics.find((t) => t.canonical_key === key);
                  if (found) handleSelectTopic(found);
                }}
                onStartTestMode={handleStartPaperTest}
                isExpanded={true}
                onToggleExpand={() => setIsStudioExpanded(false)}
              />
            ) : selectedTopic ? (
              <TopicDetailStudio
                topic={selectedTopic}
                onClose={() => {
                  setSelectedTopic(null);
                  setIsStudioExpanded(false);
                }}
                onInspectTest={handleInspectTestFromTopic}
                onStartTestMode={handleStartTopicTest}
                isExpanded={true}
                onToggleExpand={() => setIsStudioExpanded(false)}
              />
            ) : null}
          </div>
        </div>
      )}

      {/* Studio Split Layout: Left 3D Stream + Draggable Divider + Right Inline Studio */}
      <div
        ref={containerRef}
        className={`flex flex-col lg:flex-row items-start gap-0 relative w-full ${
          isDragging ? "select-none cursor-col-resize" : ""
        }`}
      >
        {/* LEFT COLUMN: Control Center & 3D Cards Stream */}
        <section
          className="w-full flex flex-col gap-6 shrink-0 transition-none"
          style={{
            width: isLgScreen ? `${splitPercent}%` : "100%",
            maxWidth: isLgScreen ? `${splitPercent}%` : "100%",
          }}
        >
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
            topicsCount={classTopics.length}
            testsCount={classTests.length}
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
            <div className="grid grid-cols-[repeat(auto-fill,minmax(270px,1fr))] gap-4">
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
              <div className="grid grid-cols-[repeat(auto-fill,minmax(270px,1fr))] gap-4 pb-12">
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
              <div className="grid grid-cols-[repeat(auto-fill,minmax(270px,1fr))] gap-4 pb-12">
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

        {/* DRAGGABLE DIVIDER (Desktop lg+) */}
        <div
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onDoubleClick={handleResetSplit}
          className="hidden lg:flex items-center justify-center w-6 cursor-col-resize shrink-0 group relative select-none touch-none h-[calc(100vh-4rem)] sticky top-8 z-30 mx-1"
          title="Drag to resize • Double-click to reset (52/48)"
        >
          {/* Visual Divider Line */}
          <div
            className={`w-1 rounded-full h-full transition-all duration-150 ${
              isDragging
                ? "bg-[#E4DA72] shadow-[0_0_14px_rgba(228,218,114,0.9)] scale-x-125"
                : "bg-[#9564DD]/30 group-hover:bg-[#E4DA72]/80 group-hover:shadow-[0_0_10px_rgba(228,218,114,0.6)]"
            }`}
          />

          {/* Floating Center Grab Handle Pill */}
          <div
            className={`absolute top-1/2 -translate-y-1/2 flex items-center justify-center w-5 h-12 rounded-full border transition-all duration-200 shadow-xl backdrop-blur-md ${
              isDragging
                ? "bg-[#E4DA72] text-[#0A0518] border-white scale-110 shadow-neon-yellow"
                : "bg-[#0A0518]/90 text-[#EEEEEE]/70 border-[#9564DD]/50 group-hover:border-[#E4DA72] group-hover:text-[#E4DA72] group-hover:scale-105"
            }`}
          >
            <GripVertical className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* RIGHT COLUMN: Sticky Inline Preview Studio */}
        <section
          className={`sticky top-8 h-[calc(100vh-4rem)] hidden lg:block shrink-0 transition-none ${
            isDragging ? "pointer-events-none" : ""
          }`}
          style={{
            width: isLgScreen ? `calc(${100 - splitPercent}% - 2rem)` : "100%",
            maxWidth: isLgScreen ? `calc(${100 - splitPercent}% - 2rem)` : "100%",
          }}
        >
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
              onStartTestMode={handleStartPaperTest}
              isExpanded={false}
              onToggleExpand={() => setIsStudioExpanded(true)}
            />
          ) : selectedTopic ? (
            <TopicDetailStudio
              topic={selectedTopic}
              onClose={() => setSelectedTopic(null)}
              onInspectTest={handleInspectTestFromTopic}
              onStartTestMode={handleStartTopicTest}
              isExpanded={false}
              onToggleExpand={() => setIsStudioExpanded(true)}
            />
          ) : (
            <CleanHud
              totalTests={classTests.length}
              totalTopics={classTopics.length}
              physicsCount={classSubjectMetrics.physics}
              chemistryCount={classSubjectMetrics.chemistry}
              biologyCount={classSubjectMetrics.biology}
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
                onStartTestMode={handleStartPaperTest}
              />
            ) : selectedTopic ? (
              <TopicDetailStudio
                topic={selectedTopic}
                onClose={() => setSelectedTopic(null)}
                onInspectTest={handleInspectTestFromTopic}
                onStartTestMode={handleStartTopicTest}
              />
            ) : null}
          </div>
        </div>
      )}
    </main>
  );
}
