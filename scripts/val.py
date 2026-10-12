import re, sys
sys.argv=['x']
exec(open('build.py').read().split('\ndef main')[0])
for eid, pf, *_ in EXAMS:
    L = lines_of(f'dl/{pf}.pdf'); st = stream(L, (lambda p: p != 4) if eid == '23b' else (lambda p: False)); b = regions(st)
    bad=[]
    for k,(kind,val,i) in enumerate(b):
        if kind!='q': continue
        nxt = b[k+1][2] if k+1<len(b) else len(st)
        t = ' '.join(st[j][0]['t'] for j in range(i, nxt))
        cnt = [len(re.findall(r'\(%s\)'%x, t)) for x in 'ABCDE']
        if cnt != [1]*5: bad.append((val, cnt, st[i][0]['p']))
    print(eid, bad)
