export interface TestItem {
  id: string;
  external_test_id: string;
  name: string;
  date?: string;
  duration_minutes?: number;
  mode?: string;
  status?: string;
  category?: string;
  target_class?: "11th" | "12th" | string;
  course_id?: string;
  course_name?: string;
  processing_status: string;
  has_syllabus: boolean;
  has_question_paper: boolean;
  created_at: string;
  updated_at: string;
}

export interface TopicInTest {
  topic_id: string;
  name: string;
  canonical_key: string;
  subject: "Physics" | "Chemistry" | "Biology";
  source_text: string;
  source_section?: string;
  confidence: number;
}

export interface TestTopicsGrouped {
  test_id: string;
  external_test_id: string;
  test_name: string;
  total_topics: number;
  subjects: {
    physics: TopicInTest[];
    chemistry: TopicInTest[];
    biology: TopicInTest[];
  };
}

export interface TopicItem {
  id: string;
  subject: "Physics" | "Chemistry" | "Biology";
  name: string;
  canonical_key: string;
  aliases: string[];
  test_count: number;
  target_classes?: string[];
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestInTopic {
  test_id: string;
  external_test_id: string;
  name: string;
  date?: string;
  duration_minutes?: number;
  mode?: string;
  status?: string;
  category?: string;
  target_class?: string;
  course_id?: string;
  course_name?: string;
  has_syllabus: boolean;
  has_question_paper: boolean;
  source_text?: string;
  source_section?: string;
}

export interface TopicWithTests {
  topic: TopicItem;
  total_tests: number;
  tests: TestInTopic[];
}

export interface QuestionItem {
  id: string;
  test_id: string;
  external_test_id: string;
  test_name?: string;
  question_number: number;
  subject_question_number?: number;
  subject: "Physics" | "Chemistry" | "Biology";
  question_text: string;
  options: string[];
  answer?: string;
  source_page: number;
  bounding_box?: number[];
  image_url?: string;
  canonical_key: string;
  classification_method: string;
  confidence: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}


import { logger } from "./logger";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

// In-memory cache for ultra-low latency navigation
const cache = new Map<string, { data: any; expiry: number }>();
const CACHE_TTL = 30000; // 30 seconds

async function cachedFetch<T>(url: string): Promise<T> {
  const now = Date.now();
  const cached = cache.get(url);
  if (cached && cached.expiry > now) {
    return cached.data as T;
  }

  const startTime = typeof performance !== "undefined" ? performance.now() : Date.now();
  try {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    const duration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - startTime;
    logger.api("GET", url, res.status, duration);

    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`API Error ${res.status}: ${errText || res.statusText}`);
    }
    const data = await res.json();
    cache.set(url, { data, expiry: now + CACHE_TTL });
    return data;
  } catch (err: any) {
    const duration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - startTime;
    logger.error(`API Fetch Error on ${url} (${duration.toFixed(1)}ms)`, err);
    throw err;
  }
}

export const api = {
  async getTests(params: {
    q?: string;
    status?: string;
    mode?: string;
    targetClass?: string;
    page?: number;
    pageSize?: number;
  } = {}): Promise<PaginatedResponse<TestItem>> {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.status) search.set("status", params.status);
    if (params.mode) search.set("mode", params.mode);
    if (params.targetClass && params.targetClass !== "all") search.set("target_class", params.targetClass);
    if (params.page) search.set("page", params.page.toString());
    if (params.pageSize) search.set("page_size", params.pageSize.toString());

    return cachedFetch<PaginatedResponse<TestItem>>(`${API_BASE}/tests?${search.toString()}`);
  },

  async getTestById(id: string): Promise<TestItem & { total_topics: number; topics_count_by_subject: Record<string, number> }> {
    return cachedFetch(`${API_BASE}/tests/${id}`);
  },

  async getTestTopics(id: string): Promise<TestTopicsGrouped> {
    return cachedFetch<TestTopicsGrouped>(`${API_BASE}/tests/${id}/topics`);
  },

  async getTopics(params: {
    q?: string;
    subject?: string;
    targetClass?: string;
    sortBy?: string;
    order?: string;
    page?: number;
    pageSize?: number;
  } = {}): Promise<PaginatedResponse<TopicItem>> {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.subject) search.set("subject", params.subject);
    if (params.targetClass && params.targetClass !== "all") search.set("target_class", params.targetClass);
    if (params.sortBy) search.set("sort_by", params.sortBy);
    if (params.order) search.set("order", params.order);
    if (params.page) search.set("page", params.page.toString());
    if (params.pageSize) search.set("page_size", params.pageSize.toString());

    return cachedFetch<PaginatedResponse<TopicItem>>(`${API_BASE}/topics?${search.toString()}`);
  },

  async getTopicById(id: string): Promise<TopicItem> {
    return cachedFetch<TopicItem>(`${API_BASE}/topics/${id}`);
  },

  async getTopicTests(id: string): Promise<TopicWithTests> {
    return cachedFetch<TopicWithTests>(`${API_BASE}/topics/${id}/tests`);
  },

  async getTopicQuestions(
    topicIdentifier: string,
    params: {
      testId?: string;
      subject?: string;
      page?: number;
      pageSize?: number;
    } = {}
  ): Promise<PaginatedResponse<QuestionItem>> {
    const search = new URLSearchParams();
    if (params.testId) search.set("test_id", params.testId);
    if (params.subject) search.set("subject", params.subject);
    if (params.page) search.set("page", params.page.toString());
    if (params.pageSize) search.set("page_size", params.pageSize.toString());

    return cachedFetch<PaginatedResponse<QuestionItem>>(
      `${API_BASE}/topics/${encodeURIComponent(topicIdentifier)}/questions?${search.toString()}`
    );
  },

  async getTestQuestions(
    testIdentifier: string,
    params: {
      subject?: string;
      page?: number;
      pageSize?: number;
    } = {}
  ): Promise<PaginatedResponse<QuestionItem>> {
    const search = new URLSearchParams();
    if (params.subject) search.set("subject", params.subject);
    if (params.page) search.set("page", params.page.toString());
    if (params.pageSize) search.set("page_size", params.pageSize.toString());

    return cachedFetch<PaginatedResponse<QuestionItem>>(
      `${API_BASE}/tests/${encodeURIComponent(testIdentifier)}/questions?${search.toString()}`
    );
  },

  getArtifactPdfUrl(testId: string, kind: "syllabus" | "question_paper"): string {

    return `${API_BASE}/tests/${testId}/artifacts/${kind}`;
  }
};
