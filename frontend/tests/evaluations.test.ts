import { describe, expect, it } from "vitest";
import { evaluationSchema } from "../src/schemas/evaluations";

describe("evaluaciones NIST", () => {
  it("valida el perfil objetivo y el alcance", () => {
    const valid = evaluationSchema.safeParse({
      code: "NIST-2026",
      name: "Evaluación anual",
      scope: "Toda la organización",
      target_maturity: 3,
      framework_id: "11111111-1111-4111-8111-111111111111",
      asset_ids: [],
    });
    expect(valid.success).toBe(true);
    const invalid = evaluationSchema.safeParse({
      code: "NIST 2026",
      name: "",
      scope: "x",
      target_maturity: 7,
      framework_id: "",
      asset_ids: [],
    });
    expect(invalid.success).toBe(false);
  });
});
