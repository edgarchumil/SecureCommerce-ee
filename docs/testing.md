# Pruebas y controles de calidad

## Suites funcionales

El backend usa Pytest, cobertura mínima de 80 %, Ruff y mypy estricto. Cubre identidad, permisos, aislamiento multiempresa, activos, NIST, riesgos, dashboard, IA, PDF, auditoría, JWT inválido y correlación. El frontend usa Vitest, Testing Library, TypeScript, ESLint y axe-core para reglas WCAG automatizadas.

```powershell
cd backend
..\.venv\Scripts\ruff.exe check .
..\.venv\Scripts\mypy.exe app
..\.venv\Scripts\pytest.exe --cov=app --cov-report=term-missing
cd ..\frontend
npm run lint
npm test
npm run build
```

## Seguridad de la cadena de suministro

`security.yml` ejecuta Bandit, pip-audit, npm audit, Gitleaks y Trivy, y publica un SBOM SPDX de la imagen backend. Dependabot revisa Python, npm y GitHub Actions semanalmente. Un hallazgo crítico bloquea la entrega; las excepciones requieren propietario, vencimiento y mitigación.

## Rendimiento

El smoke test k6 usa 5 usuarios durante 30 segundos; exige errores menores a 1 % y p95 menor a 500 ms:

```powershell
Get-Content infrastructure/performance/smoke.js -Raw | docker run --rm -i `
  -e BASE_URL=http://host.docker.internal:8080 grafana/k6 run -
```

## Accesibilidad

axe no sustituye revisión humana. Antes de entregar revise teclado completo, foco visible, zoom 200 %, lector de pantalla, errores asociados a campos y que estados no dependan únicamente del color.
