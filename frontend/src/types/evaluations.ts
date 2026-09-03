export interface Framework {
  id: string;
  code: string;
  name: string;
  version: string;
  description: string | null;
}
export interface Evaluation {
  id: string;
  framework_id: string;
  code: string;
  name: string;
  scope: string;
  target_maturity: number;
  status: "draft" | "in_review" | "approved" | "closed";
  version: number;
  comments: string | null;
  asset_ids: string[];
  created_at: string;
  updated_at: string;
}
export interface Question {
  id: string;
  function_code: string;
  function_name: string;
  category_code: string;
  category_name: string;
  control_code: string;
  text: string;
  help_text: string;
  weight: number;
  expected_evidence: string;
  response_options: { value: number; label: string }[];
  base_recommendation: string;
}
export interface Answer {
  id: string;
  question_id: string;
  maturity: number;
  comment: string | null;
  updated_at: string;
}
export interface ScoreItem {
  code: string;
  name: string;
  score: number;
  target: number;
  gap: number;
  answered: number;
  total: number;
}
export interface EvaluationResults {
  current_profile: number;
  target_profile: number;
  gap: number;
  answered: number;
  total: number;
  by_function: ScoreItem[];
  by_category: ScoreItem[];
}
