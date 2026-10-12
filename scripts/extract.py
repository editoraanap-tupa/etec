import re, subprocess, sys, json, os
import xml.etree.ElementTree as ET

DL = sys.argv[1] if len(sys.argv) > 1 else "."
NS = '{http://www.w3.org/1999/xhtml}'

def lines_of(pdf):
    xml = subprocess.run(['pdftotext', '-bbox-layout', pdf, '-'], capture_output=True, text=True).stdout
    xml = re.sub(r'<!DOCTYPE[^>]*>', '', xml)
    xml = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml)
    root = ET.fromstring(xml)
    out = []
    for pi, page in enumerate(root.iter(NS + 'page')):
        H = float(page.get('height')); W = float(page.get('width'))
        for line in page.iter(NS + 'line'):
            words = [(float(w.get('xMin')), w.text or '') for w in line.iter(NS + 'word')]
            out.append(dict(p=pi, y0=float(line.get('yMin')), y1=float(line.get('yMax')),
                            x0=float(line.get('xMin')), x1=float(line.get('xMax')),
                            t=' '.join(w for _, w in words), W=W, H=H))
    out.sort(key=lambda l: (l['p'], round(l['y0']), l['x0']))
    return out

if __name__ == '__main__':
    f = sys.argv[2]
    L = lines_of(os.path.join(DL, f))
    hdr = [l for l in L if re.fullmatch(r'Quest[ãa]o\s*\d{1,2}', l['t'].strip())]
    print(f, len(hdr), [int(re.findall(r'\d+', h['t'])[0]) for h in hdr])
    for l in L:
        if re.search(r'quest(ões|ão)\s+\d', l['t'], re.I) and not re.fullmatch(r'Quest[ãa]o\s*\d{1,2}', l['t'].strip()):
            print('  marker p%d y%.0f: %s' % (l['p'], l['y0'], l['t'][:120]))
