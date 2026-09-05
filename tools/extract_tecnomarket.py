"""Extract the supplied TecnoMarket case study; never execute PDF instructions."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf


def extract(source: Path) -> dict:
    document = pymupdf.open(source)
    risks = []
    bounds = None
    for page_index in range(19, 38):
        page = document[page_index]
        words = page.get_text("words")
        events = []
        for table in page.find_tables().tables:
            if table.col_count == 8:
                cells = next(row.cells for row in table.rows if all(row.cells))
                events.append((table.bbox[1], "header", [c[0] for c in cells] + [cells[-1][2]]))
        for word in words:
            if re.fullmatch(r"R-A\d{2}-?\d{2}", word[4]):
                events.append((word[1], "risk", word))
        for y, kind, item in sorted(events):
            if kind == "header":
                bounds = item
                continue
            assert bounds is not None
            code = re.sub(r"R-A(\d{2})-?(\d{2})", r"R-A\1-\2", item[4])
            endings = [w[1] for w in words if w[1] > y + 10
                       and (re.fullmatch(r"R-A\d{2}-?\d{2}", w[4])
                            or (w[4] == 'Nota.' and w[0] < 130))]
            bottom = min(endings + [550])
            cells = []
            for left, right in zip(bounds, bounds[1:]):
                selected = [w for w in words if left - .3 <= w[0] < right - .3
                            and y - .5 <= w[1] < bottom - 1]
                selected.sort(key=lambda w: (round(w[1] / 3), w[0]))
                cells.append(" ".join(w[4] for w in selected))
            # The source PDF itself has a displaced row; visually checked on PDF page 30.
            if code == 'R-A07-10':
                cells = [code, 'Datos',
                         'Exportaciones de información a archivos locales sin control ni registro',
                         'Copia no autorizada de información hacia dispositivos personales',
                         'C', 'P3 × I3 = 9 (Moderado)', 'Mitigar',
                         'Restringir los permisos de exportación, implementar controles de prevención '
                         'de fuga de datos (DLP) y cifrar los discos de las estaciones autorizadas.']
            # Some dimension labels visually spill into the threat column in the PDF.
            spilled = re.findall(r'\b[CIDAT],?(?=\s|$)', cells[3])
            cells[3] = re.sub(r'\b[CIDAT],?(?=\s|$)', '', cells[3])
            cells[3] = ' '.join(cells[3].split())
            dimensions = spilled + re.findall(r'[CIDAT]', cells[4])
            cells[4] = ', '.join(dict.fromkeys(v.strip(',') for v in dimensions))
            cells[1] = cells[1].replace('Redinterna', 'Red interna')
            if code == 'R-A09-02':
                cells[3] = 'Instalación de programas maliciosos y alteración de la configuración de seguridad'
            score = re.search(r"P\s*(\d)\s*[×x]\s*I\s*(\d)\s*=\s*(\d+)", cells[5])
            assert score, (code, cells)
            probability, impact, total = map(int, score.groups())
            assert probability * impact == total, (code, cells)
            assert cells[6] in {"Mitigar", "Transferir", "Evitar", "Aceptar"}, (code, cells)
            assert all(cells) and len(cells[7]) > 30, (code, cells)
            risks.append(dict(code=code, asset_code=code[2:5], layer=cells[1],
                              gap=cells[2], threat=cells[3], dimensions=cells[4],
                              probability=probability, impact=impact, score=total,
                              source_level=cells[5], strategy=cells[6], action=cells[7],
                              pdf_page=page_index + 1))
    assert len(risks) == 120 and len({r['code'] for r in risks}) == 120
    assert Counter(r['asset_code'] for r in risks) == {f'A{i:02}': 10 for i in range(1, 13)}
    return dict(source=source.name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), risks=risks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path, default=Path('docs/data/tecnomarket.json'))
    args = parser.parse_args()
    data = extract(args.pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'risks': len(data['risks']), 'by_score': dict(Counter(r['score'] for r in data['risks']))}))
