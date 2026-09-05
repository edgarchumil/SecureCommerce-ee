"""Validate/import TecnoMarket through the authenticated API, safely resumable.

No PDF commands are executed. Existing records are never overwritten. Credentials
come from the ignored .env; the generated bootstrap credential stays in ignored tmp/.
"""
import argparse
import json
import secrets
import sys
from collections import Counter
from pathlib import Path
from uuid import UUID

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.schemas.assets import AssetCreate
from app.schemas.risks import CatalogCreate, RiskCreate, TreatmentCreate

SLUG = 'tecnomarket-gt'
ADMIN = 'administrador@demo.local'
BANDS = {'bands': [
    {'level': 'low', 'minimum': 1, 'maximum': 4},
    {'level': 'medium', 'minimum': 5, 'maximum': 9},
    {'level': 'high', 'minimum': 10, 'maximum': 15},
    {'level': 'critical', 'minimum': 16, 'maximum': 25},
]}
ASSETS = [
    ('Servidor web de producción', 'server', (4, 5, 5), 'Crítico', 'Es el punto de entrada al negocio; su caída detiene las ventas.'),
    ('Aplicación web de comercio electrónico', 'application', (4, 5, 5), 'Crítico', 'Procesa pagos y datos de clientes en tiempo real.'),
    ('Base de datos de clientes y ventas', 'database', (5, 5, 4), 'Crítico', 'Contiene datos personales y financieros sensibles.'),
    ('Administrador del sistema', 'other', (4, 4, 4), 'Alto', 'Recurso humano con acceso privilegiado a toda la infraestructura.'),
    ('Servidor de pruebas (staging)', 'server', (2, 3, 3), 'Medio', 'Entorno de pruebas. El inventario declara ausencia de datos reales; la matriz evalúa copias productivas como riesgo, pendiente de validación.'),
    ('Aplicación web en ambiente de pruebas', 'application', (2, 3, 3), 'Medio', 'Ambiente aislado, con bajo impacto directo según el inventario.'),
    ('Base de datos de pruebas', 'database', (2, 3, 2), 'Medio', 'El inventario declara datos sintéticos; R-A07-01 plantea copias productivas sin anonimizar. Contradicción documental pendiente de validación.'),
    ('Analista de QA', 'other', (2, 3, 3), 'Medio', 'Recurso humano con acceso limitado a ambientes no productivos.'),
    ('Computadora de desarrollador', 'computer', (3, 4, 3), 'Alto', 'Puede contener credenciales y accesos a repositorios.'),
    ('Repositorio Git (control de versiones)', 'application', (4, 5, 4), 'Crítico', 'Contiene todo el código fuente e historial del sistema.'),
    ('Código fuente del sistema', 'information', (5, 5, 3), 'Crítico', 'Propiedad intelectual clave del negocio.'),
    ('Desarrollador principal', 'other', (3, 4, 3), 'Alto', 'Recurso humano con conocimiento clave y acceso a sistemas críticos.'),
]


def level(score):
    return next(b['level'] for b in BANDS['bands'] if b['minimum'] <= score <= b['maximum'])


def prepare(data):
    source = f"Fuente: {data['source']}; caso académico 2026."
    assets = []
    for i, (name, kind, cid, criticality, description) in enumerate(ASSETS, 1):
        environment = ['producción', 'pruebas', 'desarrollo'][(i - 1) // 4]
        notes = (f'{source} PDF pp. 9-12 (pp. 1-4 impresas). '
                 f'Criticidad original: {criticality}; promedio C/I/D: {sum(cid)/3:.1f}. '
                 'La criticidad global del sistema se calcula con el máximo C/I/D. '
                 'No se han verificado direcciones IP, sistemas operativos ni controles reales. '
                 'Empresa del caso: fundada en 2015, Ciudad de Guatemala; comercio electrónico '
                 'desde 2018, más de 40 empleados; venta de tecnología, licencias y soporte.')
        assets.append(AssetCreate(name=name, internal_code=f'A{i:02}', asset_type=kind,
                     description=f'{description} {source}', location=f'Ambiente de {environment}',
                     exposure_level='public' if i in (1, 2, 5) else 'internal',
                     confidentiality_criticality=cid[0], integrity_criticality=cid[1],
                     availability_criticality=cid[2], tags=[environment, 'caso-académico', 'tecnomarket']
                     + (['recurso-humano'] if kind == 'other' else []), notes=notes).model_dump(mode='json'))
    risks = []
    for row in data['risks']:
        ref = f"{source} PDF p. {row['pdf_page']} (p. {row['pdf_page']-8} impresa), {row['code']}."
        caveat = ('Escenario documental, no incidente confirmado. Medidas propuestas sin evidencia '
                  'de ejecución. Riesgo residual conservado igual al inherente hasta verificar los controles. '
                  'Las pruebas de las pp. 55-56 se limitaron a una réplica OWASP Juice Shop; '
                  'OpenVAS no produjo resultados válidos de escaneo.')
        description = (f"Activo {row['asset_code']}. Capa: {row['layer']}. "
                       f"Brecha: {row['gap']}. Amenaza: {row['threat']}. "
                       f"Dimensiones: {row['dimensions']}. MAGERIT P×I: {row['score']}. "
                       f"Decisión documental: {row['strategy']}. {caveat} {ref}")
        threat = CatalogCreate(name=f"{row['code']} · {row['threat']}"[:180],
                               description=f"{row['threat']}. {ref} Escenario del caso, pendiente de validación.",
                               rating=row['probability']).model_dump()
        vulnerability = CatalogCreate(name=f"{row['code']} · {row['gap']}"[:180],
                                      description=f"{row['gap']}. {ref} Brecha documental, no hallazgo de un escaneo productivo. La valoración 1-5 corresponde al impacto del riesgo; no es CVSS.",
                                      rating=row['impact']).model_dump()
        risk = RiskCreate(code=row['code'], title=row['threat'][:200], description=description,
                          asset_id=UUID(int=1), probability=row['probability'], impact=row['impact'],
                          existing_controls=None, residual_probability=row['probability'],
                          residual_impact=row['impact'], treatment_strategy={
                              'Mitigar': 'mitigate', 'Transferir': 'transfer',
                              'Evitar': 'avoid', 'Aceptar': 'accept'}[row['strategy']]).model_dump(mode='json')
        treatment = TreatmentCreate(action=f"Propuesta del documento: {row['action']}",
                                    progress=0, notes=f'{ref} Pendiente de implementación y validación; sin fecha ni responsable nominal confirmados.').model_dump(mode='json')
        risks.append(dict(source=row, threat=threat, vulnerability=vulnerability, risk=risk, treatment=treatment))
    assert len(assets) == 12 and len(risks) == 120
    assert Counter(level(r['source']['score']) for r in risks) == {'critical': 28, 'high': 66, 'medium': 26}
    for offset, expected in [(0, (11, 25, 4)), (40, (7, 16, 17)), (80, (10, 25, 5))]:
        counts = Counter(level(r['source']['score']) for r in risks[offset:offset+40])
        assert tuple(counts[x] for x in ('critical', 'high', 'medium')) == expected
    return assets, risks


class API:
    def __init__(self, url):
        self.client = httpx.Client(base_url=url.rstrip('/'), timeout=90)

    def call(self, method, path, **kwargs):
        response = self.client.request(method, path, **kwargs)
        if response.is_error:
            raise RuntimeError(f'{method} {path}: HTTP {response.status_code}; {response.text[:500]}')
        return response.json() if response.content else None

    def login(self, email, password, organization_id=None):
        payload = dict(email=email, password=password, organization_id=organization_id)
        result = self.call('POST', '/auth/login', json=payload)
        if result['organization_selection_required']:
            payload['organization_id'] = result['organizations'][0]['id']
            result = self.call('POST', '/auth/login', json=payload)
        if not result['access_token']:
            raise RuntimeError('No access token; authentication requires user action')
        self.client.headers['Authorization'] = 'Bearer ' + result['access_token']

    def pages(self, path):
        first = self.call('GET', path, params={'page_size': 100})
        items = first['items']
        for page in range(2, first['pages'] + 1):
            items.extend(self.call('GET', path, params={'page_size': 100, 'page': page})['items'])
        return items


def apply(data, url):
    assets, risks = prepare(data)
    env = dotenv_values(ROOT / '.env')
    api = API(url)
    api.login(ADMIN, env['DEMO_PASSWORD'])
    original_user = api.call('GET', '/auth/me')
    organizations = api.call('GET', '/platform/organizations')
    other_counts = {o['id']: o for o in organizations}
    org = next((o for o in organizations if o['slug'] == SLUG), None)
    credential_file = ROOT / 'tmp' / 'tecnomarket-bootstrap.json'
    if org is None:
        credential_file.parent.mkdir(exist_ok=True)
        if credential_file.exists():
            credential = json.loads(credential_file.read_text())
        else:
            credential = {'email': 'administracion.tecnomarket@demo.local', 'password': secrets.token_urlsafe(32)}
            credential_file.write_text(json.dumps(credential), encoding='utf-8')
        org = api.call('POST', '/auth/register', json=dict(
            **credential, full_name='Administración del caso TecnoMarket',
            organization_name='TecnoMarket GT, S.A.', organization_slug=SLUG,
            sector='Comercio electrónico de tecnología', size='Más de 40 empleados (según caso académico)', country='GT'))
        print('Empresa creada:', org['id'], flush=True)
    # The registration API requires a bootstrap account. Link the existing administrator
    # using this local membership endpoint, which does not send invitations or email.
    login_options = api.call('POST', '/auth/login', json={'email': ADMIN, 'password': env['DEMO_PASSWORD']})
    if not any(o['id'] == org['id'] for o in login_options.get('organizations', [])):
        credential = json.loads(credential_file.read_text())
        api.login(credential['email'], credential['password'], org['id'])
        if not any(m['email'] == ADMIN for m in api.call('GET', '/memberships')):
            api.call('POST', '/memberships/invite', json={'email': ADMIN, 'full_name': original_user['full_name'], 'role_code': 'org_admin'})
    api.login(ADMIN, env['DEMO_PASSWORD'], org['id'])
    assert api.call('GET', '/organizations/current')['slug'] == SLUG
    current_assets = {a['internal_code']: a for a in api.pages('/assets')}
    current_risks = {r['code']: r for r in api.pages('/risks')}
    if any(r['code'] not in {row['risk']['code'] for row in risks} for r in current_risks.values()):
        raise RuntimeError('Unexpected existing risks; refusing to change organization thresholds')
    api.call('PUT', '/settings/risk-bands', json=BANDS)
    for asset in assets:
        if asset['internal_code'] not in current_assets:
            current_assets[asset['internal_code']] = api.call('POST', '/assets', json=asset)
    print('Activos verificados: 12', flush=True)
    threats = {r['name']: r for r in api.call('GET', '/threats')}
    vulnerabilities = {r['name']: r for r in api.call('GET', '/vulnerabilities')}
    for index, row in enumerate(risks, 1):
        for path, cache, key in [('/threats', threats, 'threat'), ('/vulnerabilities', vulnerabilities, 'vulnerability')]:
            payload = row[key]
            if payload['name'] not in cache:
                cache[payload['name']] = api.call('POST', path, json=payload)
        payload = row['risk'] | dict(asset_id=current_assets[row['source']['asset_code']]['id'],
                                     threat_id=threats[row['threat']['name']]['id'],
                                     vulnerability_id=vulnerabilities[row['vulnerability']['name']]['id'])
        existing = current_risks.get(payload['code'])
        if existing is None:
            existing = api.call('POST', '/risks', json=payload)
            current_risks[payload['code']] = existing
        treatment_path = f"/risks/{existing['id']}/treatments"
        treatments = api.call('GET', treatment_path)
        if not any(t['action'] == row['treatment']['action'] for t in treatments):
            api.call('POST', treatment_path, json=row['treatment'])
            # API adds a proposed action as in_treatment. Preserve the documented
            # initial state when there is no execution evidence.
            api.call('PUT', f"/risks/{existing['id']}", json=payload)
        if index % 10 == 0:
            print(f'Riesgos y tratamientos cargados: {index}/120', flush=True)
    online_assets = api.pages('/assets')
    online_risks = api.pages('/risks')
    assert len(online_assets) == 12 and len(online_risks) == 120
    by_code = {r['code']: r for r in online_risks}
    for row in risks:
        risk = by_code[row['risk']['code']]
        assert risk['inherent_score'] == row['source']['score']
        assert risk['inherent_level'] == level(row['source']['score'])
        assert risk['residual_score'] == risk['inherent_score']
        assert risk['progress'] == 0 and risk['status'] == 'identified'
        assert risk['organization_id'] == org['id']
    after_orgs = api.call('GET', '/platform/organizations')
    assert all(next(o for o in after_orgs if o['id'] == key) == value for key, value in other_counts.items() if key != org['id'])
    summary = dict(organization_id=org['id'], organization='TecnoMarket GT, S.A.',
                   assets=len(online_assets), threats=len(api.call('GET', '/threats')),
                   vulnerabilities=len(api.call('GET', '/vulnerabilities')), risks=len(online_risks),
                   levels=dict(Counter(r['inherent_level'] for r in online_risks)),
                   dashboard=api.call('GET', '/dashboard'), source_sha256=data['source_sha256'])
    output = ROOT / 'output' / 'tecnomarket'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'verificacion-nube.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    api.call('POST', '/auth/logout')
    api.client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-url', default='https://securecommerce-ee-api.onrender.com/api/v1')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / 'docs/data/tecnomarket.json').read_text(encoding='utf-8'))
    assets, risks = prepare(data)
    print('Validación correcta: 12 activos, 120 amenazas específicas, 120 brechas, 120 riesgos y 120 acciones.', flush=True)
    if args.apply:
        apply(data, args.api_url)
