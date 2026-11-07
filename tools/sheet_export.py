#!/usr/bin/env python3
"""Выгрузить данные справочника в шаблон таблицы (.xlsx) для импорта в Google Таблицы.

    python3 tools/sheet_export.py [index.html] [mesoestetic-guide-data.xlsx]
"""
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from sheet_common import SHEETS, load_index, to_cell

src = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
dst = sys.argv[2] if len(sys.argv) > 2 else 'mesoestetic-guide-data.xlsx'
_, _, D = load_index(src)

F = 'Arial'
head = Font(name=F, bold=True, color='FFFFFF'); body = Font(name=F, size=10)
fill = PatternFill('solid', fgColor='000000'); key = PatternFill('solid', fgColor='FFF2CC')
wb = Workbook()
info = wb.active; info.title = 'Как пользоваться'
rows = [
    ('Справочник mesoestetic — данные для редактирования', True),
    ('', False),
    ('Листы «Препараты», «Линии» и «Глоссарий» — источник данных приложения. После правок приложение обновится само (синхронизация раз в 6 часов или вручную в GitHub → Actions → «Синхронизация с Google-таблицей» → Run workflow).', False),
    ('', False),
    ('Как править', True),
    ('• Меняйте текст прямо в ячейках. Названия колонок и порядок листов не меняйте.', False),
    ('• Новый препарат — новая строка внизу листа «Препараты». Обязательно: Артикул, Линия (id из листа «Линии»), Формат, Название EN и RU.', False),
    ('• Удалить препарат — напишите «да» в колонке «Удалить» (строку можно и просто удалить).', False),
    ('• Списки: «Эффекты» и «Для кого» — каждый пункт с новой строки (Ctrl+Enter / Alt+Enter в ячейке). «Тип кожи», «Главные активы», «INCI-названия» — через точку с запятой.', False),
    ('• INCI: компоненты через запятую с пробелом. Если у набора несколько составов, разделите их «||» и подпишите: «COSMELAN 1: Aqua, ... || COSMELAN 2: Aqua, ...».', False),
    ('• Новые ингредиенты из INCI сами привяжутся к статьям глоссария, если в глоссарии есть такое INCI-название. Иначе добавьте строку в «Глоссарий».', False),
    ('• Да/нет: «да» — включено, пусто — выключено.', False),
    ('', False),
    ('Защита от ошибок', True),
    ('Синхронизация не применит таблицу, если пропала колонка, повторился артикул, указана несуществующая линия или препаратов стало меньше половины от прежнего. Причина будет видна в GitHub → Actions.', False),
    ('', False),
    ('Пример строки — первая строка листа «Препараты» (age element). Жёлтым отмечены ключевые колонки.', False),
]
for r, (t, b) in enumerate(rows, 1):
    c = info.cell(r, 1, t); c.font = Font(name=F, bold=b, size=13 if r == 1 else 11); c.alignment = Alignment(wrap_text=True, vertical='top')
info.column_dimensions['A'].width = 120

for k, (title, cols) in SHEETS.items():
    ws = wb.create_sheet(title)
    for j, (_, h, _) in enumerate(cols, 1):
        c = ws.cell(1, j, h); c.font = head; c.fill = fill; c.alignment = Alignment(wrap_text=True, vertical='center')
    items = D['glossary'] if k == 'glossary' else D[k]
    for r, it in enumerate(items, 2):
        for j, (f, _, t) in enumerate(cols, 1):
            c = ws.cell(r, j, to_cell(it.get(f), t)); c.font = body; c.alignment = Alignment(wrap_text=True, vertical='top')
    for j, (f, h, t) in enumerate(cols, 1):
        L = ws.cell(1, j).column_letter
        ws.column_dimensions[L].width = {'s': 28, 'lines': 34, 'list': 26, 'bool': 12, 'inci': 60}[t] if f not in ('desc', 'usage', 'more', 'intro', 'text', 'ideal') else 48
        if f in ('code', 'line', 'id', 'en', 'ru', 'kind'):
            ws.cell(1, j).fill = PatternFill('solid', fgColor='7F6000')
    ws.freeze_panes = 'B2'; ws.row_dimensions[1].height = 42
    if k == 'products':
        dv = DataValidation(type='list', formula1='"home,prof,med"', allow_blank=False); ws.add_data_validation(dv); dv.add('C2:C1000')
        ids = ','.join(l['id'] for l in D['lines'])
        dl = DataValidation(type='list', formula1=f'"{ids}"', allow_blank=False); ws.add_data_validation(dl); dl.add('B2:B1000')
wb.save(dst)
print('saved', dst, {k: len(D['glossary'] if k == 'glossary' else D[k]) for k in SHEETS})
