"""Общие описания колонок Google-таблицы справочника и помощники для обоих скриптов."""
import json, re

# (ключ в данных, заголовок колонки в таблице, тип)
# типы: s — строка, lines — по одному значению на строку ячейки, list — через «;», bool — да/нет, inci — состав
PRODUCT_COLS = [
    ('code', 'Артикул', 's'), ('line', 'Линия (id)', 's'), ('kind', 'Формат: home / prof / med', 's'),
    ('group', 'Группа (id)', 's'), ('groupRu', 'Название группы', 's'),
    ('en', 'Название EN', 's'), ('ru', 'Название RU', 's'), ('size', 'Фасовка', 's'),
    ('desc', 'Кратко (описание)', 's'), ('usage', 'Применение', 's'),
    ('eff', 'Эффекты (каждый с новой строки)', 'lines'), ('act', 'Главные активы (id глоссария через ;)', 'list'),
    ('ideal', 'Идеальный клиент', 's'), ('skin', 'Тип кожи / задачи (через ;)', 'list'),
    ('hit', 'Хит (да/нет)', 'bool'), ('disc', 'Выводится (да/нет)', 'bool'), ('form', 'Для подбора формулы (да/нет)', 'bool'),
    ('inci', 'INCI (секции: «Название: a, b, c», секции разделять ||)', 'inci'),
    ('_delete', 'Удалить (да)', 'bool'),
]
LINE_COLS = [
    ('id', 'id', 's'), ('sym', 'Символ', 's'), ('name', 'Название', 's'), ('ru', 'Описание RU', 's'),
    ('short', 'Кратко (для плитки)', 's'), ('color', 'Цвет рамки (#RRGGBB)', 's'), ('ink', 'Цвет текста (#RRGGBB)', 's'),
    ('accent', 'Акцентная плитка (да/нет)', 'bool'), ('intro', 'Вступление', 's'), ('who', 'Для кого (каждый с новой строки)', 'lines'),
]
GLOSS_COLS = [
    ('id', 'id', 's'), ('ru', 'Название RU', 's'), ('cat', 'Категория', 's'), ('tech', 'Вспомогательный (да/нет)', 'bool'),
    ('text', 'Кратко', 's'), ('more', 'Подробнее', 's'), ('inci', 'INCI-названия (через ;)', 'list'),
]
SHEETS = {'products': ('Препараты', PRODUCT_COLS), 'lines': ('Линии', LINE_COLS), 'glossary': ('Глоссарий', GLOSS_COLS)}

YES = {'да', 'yes', 'y', 'true', '1', '+', 'x', 'х'}

def to_cell(v, t):
    if t == 'bool': return 'да' if v else ''
    if t == 'lines': return '\n'.join(v or [])
    if t == 'list': return '; '.join(v or [])
    if t == 'inci': return ' || '.join(((s['title'] + ': ') if s.get('title') else '') + ', '.join(i['t'] for i in s['items']) for s in (v or []))
    return '' if v is None else str(v)

def split_inci_items(s):
    """Разбить список INCI по запятым, не трогая «1,2-Hexanediol» и запятые внутри скобок."""
    out, cur, depth = [], '', 0
    for i, ch in enumerate(s):
        if ch in '([': depth += 1
        elif ch in ')]': depth = max(0, depth - 1)
        if ch == ',' and depth == 0 and (i + 1 >= len(s) or s[i + 1] == ' '):
            out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return [x for x in out if x]

def from_cell(v, t):
    v = '' if v is None else str(v).replace('\r\n', '\n').strip()
    if t == 'bool': return v.lower() in YES
    if t == 'lines': return [x.strip() for x in v.split('\n') if x.strip()]
    if t == 'list':
        out, cur, depth = [], '', 0
        for ch in v:
            if ch in '([': depth += 1
            elif ch in ')]': depth = max(0, depth - 1)
            if ch in ';\n' and depth == 0: out.append(cur.strip()); cur = ''
            else: cur += ch
        out.append(cur.strip())
        return [x for x in out if x]
    if t == 'inci':
        secs = []
        for part in [p.strip() for p in v.split('||') if p.strip()]:
            m = re.match(r'^([^,:()]{2,60}):\s+(.*)$', part, re.S)
            title, body = (m.group(1).strip(), m.group(2)) if m else ('', part)
            secs.append({'title': title, 'items': [{'t': x} for x in split_inci_items(body)]})
        return secs
    return v

def inci_key(s):
    s = s.lower().replace('lso', 'iso').replace('cl 1', 'ci 1').replace('potasium', 'potassium').replace('hydroxythyl', 'hydroxyethyl').replace('isoropyl', 'isopropyl').replace('propylen ', 'propylene ').replace('acrlamide', 'acrylamide')
    return re.sub(r'[^a-z0-9]+', '', s)

def load_index(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    i = next(n for n, l in enumerate(lines) if l.startswith('const DATA = '))
    return lines, i, json.loads(lines[i][len('const DATA = '):].rstrip()[:-1])

def save_index(path, lines, i, data):
    lines[i] = 'const DATA = ' + json.dumps(data, ensure_ascii=False) + ';'
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
