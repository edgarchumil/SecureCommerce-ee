import { apiClient } from "./client";
import type {
  Answer,
  Evaluation,
  EvaluationResults,
  Framework,
  Question,
} from "../types/evaluations";

export async function getFrameworks(): Promise<Framework[]> {
  return (await apiClient.get<Framework[]>("/frameworks")).data;
}
export async function getQuestions(frameworkId: string): Promise<Question[]> {
  return (
    await apiClient.get<Question[]>(`/frameworks/${frameworkId}/questions`)
  ).data;
}
export async function getEvaluations(): Promise<Evaluation[]> {
  return (await apiClient.get<Evaluation[]>("/evaluations")).data;
}
export async function getEvaluation(id: string): Promise<Evaluation> {
  return (await apiClient.get<Evaluation>(`/evaluations/${id}`)).data;
}
export async function createEvaluation(payload: object): Promise<Evaluation> {
  return (await apiClient.post<Evaluation>("/evaluations", payload)).data;
}
export async function getAnswers(id: string): Promise<Answer[]> {
  return (await apiClient.get<Answer[]>(`/evaluations/${id}/answers`)).data;
}
export async function saveAnswer(
  evaluationId: string,
  questionId: string,
  maturity: number,
): Promise<Answer> {
  return (
    await apiClient.put<Answer>(
      `/evaluations/${evaluationId}/answers/${questionId}`,
      { maturity },
    )
  ).data;
}
export async function getResults(id: string): Promise<EvaluationResults> {
  return (await apiClient.get<EvaluationResults>(`/evaluations/${id}/results`))
    .data;
}
export async function sendToReview(id: string): Promise<Evaluation> {
  return (
    await apiClient.patch<Evaluation>(`/evaluations/${id}/status`, {
      status: "in_review",
    })
  ).data;
}
