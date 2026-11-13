#!/usr/bin/env python3
"""Поднять версию справочника перед выпуском обновления.

    python3 bump-version.py                 # версия = сегодняшняя дата, .1 / .2 / …
    python3 bump-version.py "что нового"    # то же + текст для уведомления в приложении

Меняет номер сразу в трёх местах: version.json, <meta name="app-version"> и BUNDLED в index.html.
"""
import datetime, json, re, sys

# дата по Москве: сервер GitHub живёт по UTC, и ночью там ещё «вчера»
today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).strftime('%Y.%m.%d')
meta = json.load(open('version.json', encoding='utf-8'))
old = meta['version']
key = lambda v: tuple(int(x) for x in v.split('.'))
base, n = old.rsplit('.', 1)
# номер версии никогда не идёт назад: иначе телефоны сочтут обновление старым и пропустят его
if key(today + '.0') > key(base + '.0'):
    new = f'{today}.1'
else:
    new = f'{base}.{int(n) + 1}'

html = open('index.html', encoding='utf-8').read()
html2 = html.replace(f'<meta name="app-version" content="{old}">', f'<meta name="app-version" content="{new}">')
html2 = html2.replace(f"var BUNDLED = '{old}';", f"var BUNDLED = '{new}';")
if html2.count(new) < 2:
    sys.exit(f'В index.html не найдена текущая версия {old} — проверьте вручную.')
open('index.html', 'w', encoding='utf-8').write(html2)

meta['version'] = new
if len(sys.argv) > 1:
    meta['notes'] = sys.argv[1]
open('version.json', 'w', encoding='utf-8').write(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
print(f'{old} → {new}')
