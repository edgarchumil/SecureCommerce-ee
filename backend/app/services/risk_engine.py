from dataclasses import dataclass

from app.models.risks import RiskLevel


@dataclass(frozen=True)
class RiskBand:
    level: RiskLevel
    minimum: int
    maximum: int


DEFAULT_BANDS = (
    RiskBand(RiskLevel.LOW, 1, 4),
    RiskBand(RiskLevel.MEDIUM, 5, 9),
    RiskBand(RiskLevel.HIGH, 10, 16),
    RiskBand(RiskLevel.CRITICAL, 17, 25),
)


def calculate_risk(
    probability: int, impact: int, bands: tuple[RiskBand, ...] = DEFAULT_BANDS
) -> tuple[int, RiskLevel]:
    if not 1 <= probability <= 5 or not 1 <= impact <= 5:
        raise ValueError("Probabilidad e impacto deben estar entre 1 y 5")
    score = probability * impact
    for band in bands:
        if band.minimum <= score <= band.maximum:
            return score, band.level
    raise ValueError("La configuración de niveles no cubre el puntaje")


def bands_from_setting(value: dict[str, object] | None) -> tuple[RiskBand, ...]:
    if not value:
        return DEFAULT_BANDS
    raw_bands = value.get("bands")
    if not isinstance(raw_bands, list):
        raise ValueError("Configuración de niveles inválida")
    bands = tuple(
        RiskBand(RiskLevel(str(item["level"])), int(item["minimum"]), int(item["maximum"]))
        for item in raw_bands
        if isinstance(item, dict)
    )
    covered = [score for band in bands for score in range(band.minimum, band.maximum + 1)]
    if sorted(covered) != list(range(1, 26)):
        raise ValueError("Los niveles deben cubrir una vez cada puntaje del 1 al 25")
    return bands
