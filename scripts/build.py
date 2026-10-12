"""Recorta cada questão das provas oficiais em imagem e monta o JSON do banco."""
import re, subprocess, sys, json, os
from PIL import Image, ImageChops
sys.argv = ['x']
from extract import lines_of

DL = 'dl'
OUT = '/mnt/project-files/site-vestibulinho/oficiais'
DPI = 144
S = DPI / 72

EXAMS = [
    # id, prova, gabarito, rótulo, data, url prova, url gabarito
    ('26a', 'p26', 'g26', '1º sem/2026', '30/11/2025', '20261176943/A-CADERNO-VESTIBULINHO-1SEM2026.pdf', '20261176943/A-GABARITO-VESTIBULINHO-1SEM2026.pdf'),
    ('25a', 'p25', 'g25', '1º sem/2025', '15/12/2024', '20251468190/Prova.pdf', '20251468190/Gabarito.pdf'),
    ('24b', 'p24', 'g24', '2º sem/2024', '09/06/2024', '20242918930/Prova.pdf', '20242918930/Gabarito.pdf'),
    ('24a', 'p24a', 'g24a', '1º sem/2024', '10/12/2023', '202423718/Prova.pdf', '202423718/Gabarito.pdf'),
    ('23b', 'p23b', 'g23b', '2º sem/2023', '04/06/2023', '202323718/Prova.pdf', '202323718/Gabarito.pdf'),
    ('23a', 'p23a', 'g23a', '1º sem/2023', '18/12/2022', '202311698/Prova.pdf', '202311698/Gabarito.pdf'),
]
HDR = re.compile(r'Quest[ãa]o\s*(\d{1,2})$')
MARK = re.compile(r'quest(?:ões|ão)\s+(?:de\s+)?(\d{1,2})\s*(?:,\s*\d{1,2}\s*)*(e|a|até a|até)\s*(\d{1,2})', re.I)


def gabarito(pdf):
    t = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    g = {}
    for n, a, c in re.findall(r'(?<!\S)0*(\d{1,2})\s+([A-E]|\*+|ANULADA)\s+(C\d)', t):
        g[int(n)] = (a, c)
    return g


def stream(L, weak_ok=lambda p: False):
    """Ordena linhas em ordem de leitura respeitando duas colunas; devolve (linha, rect_coluna)."""
    out = []
    pages = sorted({l['p'] for l in L})
    for p in pages:
        if p == 0:
            continue  # capa
        PL = [l for l in L if l['p'] == p]
        W, H = PL[0]['W'], PL[0]['H']
        foot = [l for l in PL if re.search(r'VESTIBULINHO\s*\d', l['t']) or re.search(r'semestre\s*\|', l['t'])]
        ybot = min([l['y0'] for l in foot] + [H - 20]) - 4
        PL = [l for l in PL if l['y1'] <= ybot + 4 and not (l['y0'] > ybot)]
        mid = W / 2
        nfull = sum(1 for l in PL if l['x0'] < mid - 30 and l['x1'] > mid + 30 and l['y0'] > 200)
        nbody = sum(1 for l in PL if l['y0'] > 200)
        two = any(HDR.fullmatch(l['t'].strip()) and l['x0'] > W * 0.45 for l in PL) or \
            weak_ok(p) and (nbody > 20 and nfull < nbody * 0.08 and sum(1 for l in PL if l['x0'] > mid + 5) > 8
             and sum(1 for l in PL if l['x1'] < mid - 5) > 8)
        if not two:
            for l in sorted(PL, key=lambda l: (l['y0'], l['x0'])):
                out.append((l, (0, 0, W, ybot)))
            continue
        full = [l for l in PL if l['x0'] < mid - 30 and l['x1'] > mid + 30]
        ftop = max([l['y1'] for l in full if l['y0'] < 200], default=0)
        topfull = [l for l in full if l['y1'] <= ftop]
        for l in sorted(topfull, key=lambda l: l['y0']):
            out.append((l, (0, 0, W, ybot)))
        rest = [l for l in PL if l not in topfull]
        left = [l for l in rest if (l['x0'] + l['x1']) / 2 < mid]
        right = [l for l in rest if (l['x0'] + l['x1']) / 2 >= mid]
        for l in sorted(left, key=lambda l: l['y0']):
            out.append((l, (0, ftop, mid, ybot)))
        for l in sorted(right, key=lambda l: l['y0']):
            out.append((l, (mid, ftop, W, ybot)))
    return out


def regions(st):
    """Encontra cabeçalhos e marcadores de texto compartilhado no fluxo."""
    bounds = []
    for i, (l, r) in enumerate(st):
        t = l['t'].strip()
        m = HDR.fullmatch(t)
        if m:
            bounds.append(('q', int(m.group(1)), i))
            continue
        mm = MARK.search(t)
        if mm and ('responder' in t.lower() or (i and 'responder' in st[i - 1][0]['t'].lower())):
            a, b = int(mm.group(1)), int(mm.group(3))
            qs = list(range(a, b + 1)) if mm.group(2).lower().startswith('a') else [a, b]
            start = i
            if 'responder' not in t.lower() or not re.match(r'(Leia|Observe|Analise|Considere|Com base|Utilize)', t):
                if i and re.match(r'(Leia|Observe|Analise|Considere|Com base|Utilize)', st[i - 1][0]['t'].strip()):
                    start = i - 1
            bounds.append(('m', qs, start))
    bounds.sort(key=lambda b: b[2])
    return bounds


def crop_runs(st, i0, i1, pages):
    """Recorta as linhas st[i0:i1] agrupadas por página/coluna; estende até o próximo limite."""
    runs = []
    for i in range(i0, i1):
        l, r = st[i]
        key = (l['p'], r)
        if runs and runs[-1][0] == key:
            runs[-1][1].append(i)
        else:
            runs.append((key, [i]))
    pieces = []
    for k, ((p, r), idx) in enumerate(runs):
        y0 = min(st[i][0]['y0'] for i in idx) - 6
        last = idx[-1]
        if last + 1 < len(st) and st[last + 1][0]['p'] == p and st[last + 1][1] == r:
            y1 = st[last + 1][0]['y0'] - 4
        else:
            y1 = r[3]
        x0, x1 = r[0], r[2]
        img = pages[p]
        box = tuple(int(v * S) for v in (max(x0, 0), max(y0, r[1]), x1, y1))
        if box[3] - box[1] < 8:
            continue
        pieces.append(trim(img.crop(box)))
    return pieces


def trim(im):
    bg = Image.new('RGB', im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 18 else 0)
    bb = diff.getbbox()
    if not bb:
        return im
    pad = 10
    return im.crop((max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, im.width), min(bb[3] + pad, im.height)))


def stack(pieces, sep=False):
    W = max(p.width for p in pieces)
    gap = 18
    H = sum(p.height for p in pieces) + gap * (len(pieces) - 1)
    out = Image.new('RGB', (W, H), (255, 255, 255))
    y = 0
    for p in pieces:
        out.paste(p, (0, y))
        y += p.height + gap
    return out


def text_of(st, i0, i1):
    return ' '.join(st[i][0]['t'] for i in range(i0, i1)).strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    data = []
    for eid, pf, gf, label, date, purl, gurl in EXAMS:
        pdf = f'{DL}/{pf}.pdf'
        L = lines_of(pdf)
        st = stream(L, (lambda p: p != 4) if eid == '23b' else (lambda p: False))
        gab = gabarito(f'{DL}/{gf}.pdf')
        tmp = f'pgs/{eid}'
        os.makedirs('pgs', exist_ok=True)
        if not os.path.exists(f'{tmp}-01.png') and not os.path.exists(f'{tmp}-1.png'):
            subprocess.run(['pdftoppm', '-r', str(DPI), '-png', pdf, tmp], check=True)
        files = sorted(f for f in os.listdir('pgs') if f.startswith(eid + '-'))
        pages = [Image.open('pgs/' + f).convert('RGB') for f in files]
        b = regions(st)
        shared = {}
        qs = []
        for k, (kind, val, i) in enumerate(b):
            nxt = b[k + 1][2] if k + 1 < len(b) else len(st)
            if kind == 'm':
                # texto compartilhado vai até o próximo cabeçalho
                for q in val:
                    shared.setdefault(q, []).append((i, nxt))
            else:
                # corta páginas que sobram depois da alternativa (E) (folha de rascunho etc.)
                es = [j for j in range(i, nxt) if re.match(r'\(E\)', st[j][0]['t'].strip())]
                if es:
                    e = es[-1]
                    j = e + 1
                    while j < nxt and st[j][0]['p'] == st[e][0]['p'] and st[j][1] == st[e][1]:
                        j += 1
                    nxt = j
                qs.append((val, i, nxt))
        exam_q = []
        seen = set()
        for n, i0, i1 in qs:
            if n in seen or n not in gab:
                print('  skip', eid, n, 'dup' if n in seen else 'sem gabarito')
                continue
            seen.add(n)
            pieces = []
            ctx = ''
            for s0, s1 in shared.get(n, []):
                pieces += crop_runs(st, s0, s1, pages)
                ctx += text_of(st, s0, s1) + ' '
            pieces += crop_runs(st, i0, i1, pages)
            im = stack(pieces)
            if im.width > 1100:
                im = im.resize((1100, int(im.height * 1100 / im.width)), Image.LANCZOS)
            name = f'{eid}-{n:02d}.webp'
            im.save(f'{OUT}/{name}', 'WEBP', quality=72, method=6)
            a, c = gab[n]
            exam_q.append(dict(n=n, img='oficiais/' + name, w=im.width, h=im.height,
                               c='ABCDE'.index(a) if a in 'ABCDE' else -1, crit=c,
                               alt=(ctx + text_of(st, i0 + 1, i1))[:1500]))
        missing = sorted(set(gab) - seen)
        print(eid, 'questões', len(exam_q), 'de', len(gab), 'faltando', missing)
        data.append(dict(id=eid, label=label, date=date, prova='https://fatweb.s3.amazonaws.com/vestibulinhoetec/gabarito/' + purl,
                         gabarito='https://fatweb.s3.amazonaws.com/vestibulinhoetec/gabarito/' + gurl,
                         q=sorted(exam_q, key=lambda x: x['n'])))
    json.dump(data, open(f'{OUT}/banco.json', 'w'), ensure_ascii=False)


main()
