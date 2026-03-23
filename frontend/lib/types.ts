// Backend Pydantic şemalarına karşılık gelen TypeScript tipleri

export interface CVUploadResponse {
  id: number;
  filename: string;
  raw_text: string | null;
  sections: Record<string, string> | null;
  created_at: string;
}

export interface CVListItem {
  id: number;
  filename: string;
  ats_score: number | null;
  created_at: string;
}

export interface CVDetail {
  id: number;
  filename: string;
  file_path: string;
  raw_text: string | null;
  sections: Record<string, string> | null;
  ats_score: number | null;
  ai_feedback: AIFeedback | null;
  optimized_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface CriteriaDetail {
  name: string;
  score: number;
  max_score: number;
  feedback: string;
  details: string[];
}

export interface KeywordMatch {
  found: string[];
  missing: string[];
  match_rate: number;
}

export interface ATSScoreResponse {
  total_score: number;
  grade: string;
  criteria: CriteriaDetail[];
  summary: string;
  keyword_match: KeywordMatch;
}

export interface RewrittenBullet {
  original: string;
  improved: string;
}

export interface KeywordPlacement {
  keyword: string;
  suggestion: string;
}

export interface SectionFeedback {
  section_name: string;
  current_quality: string;
  issues: string[];
  suggestions: string[];
  rewritten_bullets: RewrittenBullet[];
}

export interface AIFeedback {
  overall_assessment: string;
  section_feedback: SectionFeedback[];
  missing_keywords: string[];
  keyword_placement: KeywordPlacement[];
  action_items: string[];
  ats_tips: string[];
}

export interface OptimizationResponse {
  cv_id: number;
  ats_score: ATSScoreResponse;
  ai_feedback: AIFeedback;
  optimization_count: number;
}

export interface OptimizedCVResponse {
  cv_id: number;
  optimized_text: string;
  optimized_sections: Record<string, string>;
  changes_made: string[];
}
