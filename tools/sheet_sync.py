#!/usr/bin/env python3
"""Применить данные из Google-таблицы к справочнику (index.html).

Источники — опубликованные в интернете CSV листов (Файл → Поделиться → Опубликовать в интернете → лист → CSV):
    SHEET_PRODUCTS_CSV, SHEET_LINES_CSV, SHEET_GLOSSARY_CSV, SHEET_COMPLEXES_CSV, SHEET_ABOUT_CSV — URL или путь к файлу.
Пустая переменная — этот лист не трогаем.

    python3 tools/sheet_sync.py [index.html]
Выход: 0 — изменений нет или применены (пишет changed=true/false в $GITHUB_OUTPUT), 1 — ошибка в таблице.
"""
import csv, io, json, os, sys, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from sheet_common import SHEETS, from_cell, inci_key, load_index, save_index, about_from_rows

path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
lines, idx, D = load_index(path)
before = json.dumps(D, ensure_ascii=False, sort_keys=True)
errors, warns = [], []

def fetch(src):
    if src.startswith('http'):
        req = urllib.request.Request(src, headers={'User-Agent': 'mesoestetic-guide-sync'})
        with urllib.request.urlopen(req, timeout=60) as r: return r.read().decode('utf-8-sig')
    return open(src, encoding='utf-8-sig').read()

def read_sheet(key, env):
    src = os.environ.get(env, '').strip()
    if not src: return None
    title, cols = SHEETS[key]
    rows = list(csv.reader(io.StringIO(fetch(src))))
    if not rows: errors.append(f'«{title}»: лист пустой'); return None
    hdr = [h.strip() for h in rows[0]]
    pos = {}
    for f, h, t in cols:
        if h not in hdr:
            if f == '_delete': continue
            errors.append(f'«{title}»: нет колонки «{h}»'); continue
        pos[f] = hdr.index(h)
    out = []
    for n, r in enumerate(rows[1:], 2):
        if not any(c.strip() for c in r): continue
        it = {f: from_cell(r[p] if p < len(r) else '', t) for (f, h, t) in cols for p in [pos.get(f)] if p is not None}
        it['_row'] = n; out.append(it)
    return out

lines_rows = read_sheet('lines', 'SHEET_LINES_CSV')
gl_rows = read_sheet('glossary', 'SHEET_GLOSSARY_CSV')
pr_rows = read_sheet('products', 'SHEET_PRODUCTS_CSV')
cx_rows = read_sheet('complexes', 'SHEET_COMPLEXES_CSV')
ab_rows = read_sheet('about', 'SHEET_ABOUT_CSV')
if errors: print('\n'.join('::error::' + e for e in errors)); sys.exit(1)

# ── линии
if lines_rows is not None:
    old = {l['id']: l for l in D['lines']}; new = []
    for it in lines_rows:
        if not it.get('id') or not it.get('name') or not it.get('sym'): errors.append(f'Линии, строка {it["_row"]}: нужны id, Название и Символ'); continue
        l = dict(old.get(it['id'], {}))
        for k, v in it.items():
            if k.startswith('_'): continue
            if k == 'accent':
                if v: l['accent'] = True
                else: l.pop('accent', None)
            else: l[k] = v
        new.append(l)
    if len(set(l['id'] for l in new)) != len(new): errors.append('Линии: повторяется id')
    if len(new) < len(D['lines']) / 2: errors.append(f'Линии: в таблице {len(new)} строк, было {len(D["lines"])} — похоже на ошибку')
    D['lines'] = new
LINES = {l['id'] for l in D['lines']}

# ── глоссарий
if gl_rows is not None:
    old = {g['id']: g for g in D['glossary']}; new = []
    for it in gl_rows:
        if not it.get('id') or not it.get('ru'): errors.append(f'Глоссарий, строка {it["_row"]}: нужны id и Название'); continue
        g = dict(old.get(it['id'], {'used': []}))
        for k, v in it.items():
            if k.startswith('_'): continue
            if k == 'tech':
                if v: g['tech'] = True
                else: g.pop('tech', None)
            else: g[k] = v
        new.append(g)
    if len(set(g['id'] for g in new)) != len(new): errors.append('Глоссарий: повторяется id')
    if len(new) < len(D['glossary']) / 2: errors.append(f'Глоссарий: в таблице {len(new)} строк, было {len(D["glossary"])} — похоже на ошибку')
    D['glossary'] = new
GL = {g['id']: g for g in D['glossary']}

# ── препараты
if pr_rows is not None:
    old = {p['code']: p for p in D['products']}; new = []; deleted = []
    for it in pr_rows:
        if it.get('_delete'): deleted.append(it.get('code')); continue
        miss = [h for f, h in [('code', 'Артикул'), ('line', 'Линия'), ('kind', 'Формат'), ('en', 'Название EN'), ('ru', 'Название RU')] if not it.get(f)]
        if miss: errors.append(f'Препараты, строка {it["_row"]}: не заполнено — {", ".join(miss)}'); continue
        if it['line'] not in LINES: errors.append(f'Препараты, строка {it["_row"]} ({it["code"]}): нет линии «{it["line"]}»'); continue
        if it['kind'] not in ('home', 'prof', 'med'): errors.append(f'Препараты, строка {it["_row"]} ({it["code"]}): Формат должен быть home, prof или med'); continue
        p = dict(old.get(it['code'], {}))
        for k, v in it.items():
            if not k.startswith('_'): p[k] = v
        for k, d in [('eff', []), ('act', []), ('skin', []), ('inci', []), ('usage', ''), ('desc', ''), ('ideal', ''), ('size', ''), ('group', ''), ('groupRu', '')]: p.setdefault(k, d)
        bad = [a for a in p['act'] if a not in GL]
        if bad: warns.append(f'{p["code"]}: нет в глоссарии активов {", ".join(bad)} — пропущены'); p['act'] = [a for a in p['act'] if a in GL]
        new.append(p)
    codes = [p['code'] for p in new]
    dup = sorted({c for c in codes if codes.count(c) > 1})
    if dup: errors.append('Препараты: повторяются артикулы ' + ', '.join(dup))
    if len(new) < len(D['products']) / 2 and not os.environ.get('SHEET_FORCE'): errors.append(f'Препараты: в таблице {len(new)} строк, было {len(D["products"])} — похоже на ошибку (SHEET_FORCE=1, если это намеренно)')
    gone = [c for c in old if c not in codes]
    code_only = '\n'.join(l for n, l in enumerate(lines) if n != idx)   # всё, кроме строки с данными
    for c in gone:
        if c in code_only: warns.append(f'{c} удалён, но упоминается в коде справочника (диагностика, путь пациента) — проверьте')
    if gone: warns.append('Удалены: ' + ', '.join(gone))
    D['products'] = new

# ── фирменные комплексы
if cx_rows is not None:
    PC = {p['code'] for p in D['products']}; new = []
    for it in cx_rows:
        if it.get('_delete'): continue
        if not it.get('id') or not it.get('name'): errors.append(f'Комплексы, строка {it["_row"]}: нужны id и Название'); continue
        if it.get('line') and it['line'] not in LINES: errors.append(f'Комплексы, строка {it["_row"]} ({it["id"]}): нет линии «{it["line"]}»'); continue
        c = {k: v for k, v in it.items() if not k.startswith('_')}
        for k, d in [('parts', []), ('g', []), ('used', []), ('purpose', ''), ('text', ''), ('line', ''), ('patent', False)]: c.setdefault(k, d)
        bad = [x for x in c['g'] if x not in GL]
        if bad: warns.append(f'Комплекс {c["id"]}: нет в глоссарии {", ".join(bad)} — пропущены'); c['g'] = [x for x in c['g'] if x in GL]
        bad = [x for x in c['used'] if x not in PC]
        if bad: warns.append(f'Комплекс {c["id"]}: нет препаратов {", ".join(bad)} — пропущены'); c['used'] = [x for x in c['used'] if x in PC]
        new.append(c)
    if len(set(c['id'] for c in new)) != len(new): errors.append('Комплексы: повторяется id')
    D['complexes'] = new
    for g in D['glossary']:          # обратные ссылки «входит в комплекс»
        cx = [c['id'] for c in new if g['id'] in c['g']]
        if cx: g['cx'] = cx
        else: g.pop('cx', None)

# ── «О компании»
if ab_rows is not None:
    A = about_from_rows(ab_rows, errors)
    if not A.get('title'): errors.append('«О компании»: нет строки «Заголовок»')
    D['about'] = A

if errors: print('\n'.join('::error::' + e for e in errors)); sys.exit(1)

# ── привязка INCI к глоссарию и «где встречается»
alias = {}
for g in D['glossary']:
    for n in g.get('inci', []): alias.setdefault(inci_key(n), g['id'])
for p in json.loads(before).get('products', []):        # прежние привязки сохраняются
    for s in p.get('inci', []):
        for i in s['items']:
            if i.get('g') in GL: alias.setdefault(inci_key(i['t']), i['g'])
unlinked = set()
for g in D['glossary']: g['used'] = []
for p in D['products']:
    for s in p['inci']:
        for i in s['items']:
            gid = i.get('g') if i.get('g') in GL else alias.get(inci_key(i['t']))
            if gid: i['g'] = gid
            else: i.pop('g', None); unlinked.add(i['t'])
    for gid in dict.fromkeys([i['g'] for s in p['inci'] for i in s['items'] if i.get('g')] + p['act']):
        if gid in GL and p['code'] not in GL[gid]['used']: GL[gid]['used'].append(p['code'])
if unlinked: warns.append('Ингредиенты без статьи в глоссарии: ' + ', '.join(sorted(unlinked)))
for c in D.get('complexes', []): c['used'] = [x for x in c['used'] if any(p['code'] == x for p in D['products'])]

for w in warns: print('::warning::' + w)
changed = json.dumps(D, ensure_ascii=False, sort_keys=True) != before
if changed: save_index(path, lines, idx, D)
print('changed' if changed else 'no changes', '| products', len(D['products']), '| lines', len(D['lines']), '| glossary', len(D['glossary']), '| complexes', len(D.get('complexes', [])))
if os.environ.get('GITHUB_OUTPUT'):
    open(os.environ['GITHUB_OUTPUT'], 'a').write(f'changed={"true" if changed else "false"}\n')
