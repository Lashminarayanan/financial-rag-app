export type StatusEvent = {
  type: 'status';
  stage?: string;
  message?: string;
  verified?: boolean;
  warnings?: string[];
};

export type SourceItem = {
  id?: string;
  document_id?: string;
  chunk_index?: number;
  page_no?: number | null;
  section?: string | null;
  chunk_text: string;
  chunk_type?: string;
  table_markdown?: string | null;
  metadata?: Record<string, unknown>;
  file_name?: string;
  similarity?: number | null;
};

export type PlanEvent = { type: 'plan'; plan: string[] };
export type SourcesEvent = { type: 'sources'; sources: SourceItem[] };
export type ComparisonEvent = { type: 'comparison'; notes: string[] };
export type TokenEvent = { type: 'token'; token: string };
export type FinalEvent = { type: 'final'; answer: string; verified?: boolean; warnings?: string[] };
export type StderrEvent = { type: 'stderr'; message: string };
export type DoneEvent = { type: 'done'; exitCode?: number | null; signal?: string | null };

export type StreamEvent = StatusEvent | PlanEvent | SourcesEvent | ComparisonEvent | TokenEvent | FinalEvent | StderrEvent | DoneEvent;
