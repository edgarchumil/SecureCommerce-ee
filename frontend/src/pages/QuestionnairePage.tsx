import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import {
  getAnswers,
  getEvaluation,
  getQuestions,
  saveAnswer,
  sendToReview,
} from "../api/evaluations";

export function QuestionnairePage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const evaluation = useQuery({
    queryKey: ["evaluation", id],
    queryFn: () => getEvaluation(id),
  });
  const questions = useQuery({
    queryKey: ["questions", evaluation.data?.framework_id],
    queryFn: () => getQuestions(evaluation.data!.framework_id),
    enabled: Boolean(evaluation.data),
  });
  const answers = useQuery({
    queryKey: ["answers", id],
    queryFn: () => getAnswers(id),
  });
  const answerMap = new Map(
    answers.data?.map((answer) => [answer.question_id, answer.maturity]),
  );
  const save = useMutation({
    mutationFn: ({
      questionId,
      maturity,
    }: {
      questionId: string;
      maturity: number;
    }) => saveAnswer(id, questionId, maturity),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["answers", id] }),
  });
  const review = useMutation({
    mutationFn: () => sendToReview(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["evaluation", id] }),
  });
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8">
      <section className="mx-auto max-w-4xl">
        <Link
          className="inline-flex items-center gap-2 text-sm text-blue-700"
          to="/evaluaciones"
        >
          <ArrowLeft size={16} />
          Evaluaciones
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-blue-950">
          {evaluation.data?.name ?? "Cuestionario NIST"}
        </h1>
        <p className="mt-2 text-slate-600">
          Los cambios se guardan al seleccionar una respuesta.
        </p>
        <div className="mt-7 space-y-5">
          {questions.data?.map((question) => (
            <article
              key={question.id}
              className="rounded-xl border border-slate-200 bg-white p-6"
            >
              <p className="text-sm font-semibold text-blue-700">
                {question.function_name} · {question.category_code}
              </p>
              <h2 className="mt-2 font-semibold text-slate-950">
                {question.text}
              </h2>
              <p className="mt-2 text-sm text-slate-600">
                {question.help_text}
              </p>
              <fieldset className="mt-4">
                <legend className="sr-only">Nivel de madurez</legend>
                <div className="grid gap-2 sm:grid-cols-5">
                  {question.response_options.map((option) => (
                    <label
                      key={option.value}
                      className="flex cursor-pointer gap-2 rounded-lg border border-slate-200 p-2 text-sm"
                    >
                      <input
                        checked={answerMap.get(question.id) === option.value}
                        name={question.id}
                        type="radio"
                        onChange={() =>
                          save.mutate({
                            questionId: question.id,
                            maturity: option.value,
                          })
                        }
                      />
                      <span>
                        {option.value}: {option.label}
                      </span>
                    </label>
                  ))}
                </div>
              </fieldset>
              <details className="mt-4 text-sm">
                <summary className="cursor-pointer font-medium text-blue-700">
                  Evidencia y recomendación
                </summary>
                <p className="mt-2 text-slate-600">
                  <strong>Evidencia esperada:</strong>{" "}
                  {question.expected_evidence}
                </p>
                <p className="mt-1 text-slate-600">
                  <strong>Si existe una brecha:</strong>{" "}
                  {question.base_recommendation}
                </p>
              </details>
            </article>
          ))}
        </div>
        {evaluation.data?.status === "draft" && (
          <button
            className="mt-7 inline-flex items-center gap-2 rounded-lg bg-blue-950 px-5 py-3 font-semibold text-white"
            disabled={review.isPending}
            onClick={() => review.mutate()}
          >
            <CheckCircle2 size={18} />
            Enviar a revisión
          </button>
        )}
      </section>
    </main>
  );
}
