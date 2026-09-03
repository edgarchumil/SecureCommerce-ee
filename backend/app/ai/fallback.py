from app.schemas.ai import GeneratedContent, ProviderResult, RecommendedAction

APPROVED_REFERENCES = ["NIST CSF 2.0", "CIS Controls v8"]


def fallback_recommendation(payload: dict[str, object]) -> ProviderResult:
    level = str(payload["residual_level"])
    priority = "alta" if level in {"critical", "high"} else "media"
    content = GeneratedContent(
        title=f"Tratamiento recomendado para {payload['code']}",
        summary=(
            "Recomendación base generada sin IA externa a partir del nivel de riesgo ya "
            "calculado. Debe revisarse antes de utilizarse."
        ),
        actions=[
            RecommendedAction(
                action="Validar los controles existentes con el responsable del activo",
                rationale="Confirma que el riesgo residual se apoya en controles verificables.",
                priority=priority,
            ),
            RecommendedAction(
                action="Definir responsable, fecha objetivo y evidencia esperada",
                rationale=(
                    "Permite dar seguimiento medible al tratamiento sin aplicar cambios "
                    "automáticamente."
                ),
                priority=priority,
            ),
        ],
        references=APPROVED_REFERENCES,
        disclaimer="Contenido asistido sujeto a revisión humana; no constituye certificación.",
    )
    return ProviderResult(
        content=content,
        provider="local",
        model="deterministic-fallback",
        input_tokens=0,
        output_tokens=0,
    )
