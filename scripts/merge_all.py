import json, glob, os, shutil
B = '/mnt/project-files/site-vestibulinho/oficiais'
new6 = json.load(open('banco_new6.json'))
old = json.load(open('banco_old.json'))
EX = {}
for f in sorted(glob.glob('exp_out_*.json')):
    EX.update(json.load(open(f)))
for e in old:
    for q in e['q']:
        k = f"{e['id']}-{q['n']:02d}"
        q['area'] = EX.get(k, {}).get('area', 'Português')
order = ['26a','25a','24b','24a','23b','23a','22b','20a','19b','19a','18b','18a','17b','17a']
allx = {e['id']: e for e in new6 + old}
banco = [allx[i] for i in order]
xp = {k: {kk: vv for kk, vv in v.items() if kk not in ('qa', 'area')} for k, v in EX.items()}
TX = {}
for f in sorted(glob.glob('txt_out_*.json')):
    TX.update(json.load(open(f)))
json.dump(banco, open(f'{B}/banco.json', 'w'), ensure_ascii=False)
json.dump(xp, open(f'{B}/explicacoes.json', 'w'), ensure_ascii=False)
json.dump(TX, open(f'{B}/textos.json', 'w'), ensure_ascii=False)
os.makedirs('site/oficiais/fig', exist_ok=True)
for n in ['banco.json', 'explicacoes.json', 'textos.json']:
    shutil.copy(f'{B}/{n}', f'site/oficiais/{n}')
for f in glob.glob(f'{B}/*.webp'):
    shutil.copy(f, 'site/oficiais/')
for f in glob.glob(f'{B}/fig/*.webp'):
    shutil.copy(f, 'site/oficiais/fig/')
print('exams', len(banco), 'q', sum(len(e['q']) for e in banco), 'exp', len(xp), 'txt', len(TX), 'figs', len(glob.glob('site/oficiais/fig/*.webp')))
from collections import Counter
print(Counter(q['area'] for e in banco for q in e['q']))
