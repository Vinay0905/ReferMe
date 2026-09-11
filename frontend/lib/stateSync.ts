"use client";

export interface TestSessionState {
  active: boolean;
  type: "topic" | "test";
  identifier: string; // canonical_key or external_test_id
  title?: string;
  currentIndex: number;
  // Map questionId or number to status
  answers: Record<
    string,
    {
      selectedOption: string; // e.g. "1", "2", "3", "4"
      isChecked: boolean;
      isCorrect: boolean;
    }
  >;
  isFinished?: boolean;
}

export interface AppPersistedState {
  selectedClass: "all" | "12th" | "11th";
  viewMode: "topics" | "tests";
  selectedSubject: string;
  searchQuery: string;
  selectedTopicKey: string | null;
  selectedTestId: string | null;
  previewKind: "syllabus" | "question_paper" | "breakdown";
  isStudioExpanded: boolean;
  testSession: TestSessionState | null;
}

const STORAGE_KEY = "referme_persisted_state_v2";

export const defaultAppState: AppPersistedState = {
  selectedClass: "12th",
  viewMode: "topics",
  selectedSubject: "all",
  searchQuery: "",
  selectedTopicKey: null,
  selectedTestId: null,
  previewKind: "syllabus",
  isStudioExpanded: false,
  testSession: null,
};

/**
 * Loads initial persisted state from URL search params with fallback to localStorage.
 */
export function getInitialAppState(): AppPersistedState {
  if (typeof window === "undefined") {
    return defaultAppState;
  }

  // 1. Start with defaults
  let state: AppPersistedState = { ...defaultAppState };

  // 2. Read from localStorage
  try {
    const rawLocal = localStorage.getItem(STORAGE_KEY);
    if (rawLocal) {
      const parsed = JSON.parse(rawLocal);
      state = { ...state, ...parsed };
    }
  } catch (err) {
    console.warn("Failed to parse localStorage state", err);
  }

  // 3. Overlay explicit URL parameters (highest priority for shareable links / browser history)
  try {
    const params = new URLSearchParams(window.location.search);

    const cls = params.get("class");
    if (cls === "all" || cls === "12th" || cls === "11th") {
      state.selectedClass = cls;
    }

    const view = params.get("view");
    if (view === "topics" || view === "tests") {
      state.viewMode = view;
    }

    const subj = params.get("subject");
    if (subj) {
      state.selectedSubject = subj;
    }

    const q = params.get("q");
    if (q !== null) {
      state.searchQuery = q;
    }

    const topicKey = params.get("topic");
    if (topicKey) {
      state.selectedTopicKey = topicKey;
      state.selectedTestId = null;
    }

    const testId = params.get("test");
    if (testId) {
      state.selectedTestId = testId;
      state.selectedTopicKey = null;
    }

    const tab = params.get("tab");
    if (tab === "syllabus" || tab === "question_paper" || tab === "breakdown") {
      state.previewKind = tab;
    }

    const expanded = params.get("expanded");
    if (expanded !== null) {
      state.isStudioExpanded = expanded === "true";
    }

    const inTest = params.get("testMode");
    if (inTest === "true") {
      const testType = (params.get("testType") as "topic" | "test") || (state.selectedTopicKey ? "topic" : "test");
      const ident = params.get("testId") || state.selectedTopicKey || state.selectedTestId || "";
      const currentIdx = parseInt(params.get("testQ") || "0", 10);

      // Preserve any answers previously saved in local state for this identifier
      const existingAnswers =
        state.testSession?.identifier === ident ? state.testSession.answers : {};

      state.testSession = {
        active: true,
        type: testType,
        identifier: ident,
        currentIndex: isNaN(currentIdx) ? 0 : currentIdx,
        answers: existingAnswers,
      };
    } else {
      // If URL does not explicitly specify testMode=true, do NOT auto-activate test session
      state.testSession = null;
    }
  } catch (err) {
    console.warn("Failed to parse URL search params", err);
  }

  return state;
}

/**
 * Saves current app state to both localStorage and URL search params without triggering Next.js re-render cycles.
 */
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

export function persistAppState(state: AppPersistedState) {
  if (typeof window === "undefined") return;

  // Save to localStorage immediately
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (err) {
    console.warn("Failed to save state to localStorage", err);
  }

  // Debounce URL replaceState to prevent URL bar spam during rapid typing or dragging
  if (debounceTimer) clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    try {
      const params = new URLSearchParams();

      if (state.selectedClass !== "12th") params.set("class", state.selectedClass);
      if (state.viewMode !== "topics") params.set("view", state.viewMode);
      if (state.selectedSubject !== "all") params.set("subject", state.selectedSubject);
      if (state.searchQuery.trim()) params.set("q", state.searchQuery.trim());
      if (state.selectedTopicKey) params.set("topic", state.selectedTopicKey);
      if (state.selectedTestId) params.set("test", state.selectedTestId);
      if (state.previewKind !== "syllabus") params.set("tab", state.previewKind);
      if (state.isStudioExpanded) params.set("expanded", "true");

      if (state.testSession && state.testSession.active) {
        params.set("testMode", "true");
        params.set("testType", state.testSession.type);
        params.set("testId", state.testSession.identifier);
        params.set("testQ", state.testSession.currentIndex.toString());
      }

      const queryString = params.toString();
      const newUrl = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname;
      window.history.replaceState(null, "", newUrl);
    } catch (err) {
      console.warn("Failed to update URL search params", err);
    }
  }, 100);
}
