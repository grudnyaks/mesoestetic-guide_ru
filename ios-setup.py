#!/usr/bin/env python3
"""Настройка iOS-проекта после `npx cap add ios` (запускается в сборке на GitHub, macOS).

- иконка приложения 1024×1024 из icons/icon-1024.png;
- чёрный экран запуска (дальше — анимированная заставка справочника);
- версия: CFBundleShortVersionString = ГГГГ.М.Д (Apple допускает максимум три числа), номер сборки = номер запуска;
- название под иконкой, отказ от экспортного шифрования (нужно для TestFlight).
"""
import glob, json, os, plistlib, re
from PIL import Image

APP = 'ios/App/App'
ver = json.load(open('version.json', encoding='utf-8'))['version']          # 2026.11.07.2
y, m, d = ver.split('.')[:3]
short = f'{int(y)}.{int(m)}.{int(d)}'
build = os.environ.get('GITHUB_RUN_NUMBER', '1')

# иконка
for f in glob.glob(f'{APP}/Assets.xcassets/AppIcon.appiconset/*.png'):
    Image.open('icons/icon-1024.png').convert('RGB').resize(Image.open(f).size, Image.LANCZOS).save(f)
    print('icon', f)
# экран запуска — чёрный
for f in glob.glob(f'{APP}/Assets.xcassets/Splash.imageset/*.png'):
    Image.new('RGB', Image.open(f).size, (0, 0, 0)).save(f); print('splash', f)

# Info.plist
p = f'{APP}/Info.plist'
info = plistlib.load(open(p, 'rb'))
info['CFBundleDisplayName'] = 'mesoestetic'
info['CFBundleShortVersionString'] = short
info['CFBundleVersion'] = build
info['ITSAppUsesNonExemptEncryption'] = False
info['UIViewControllerBasedStatusBarAppearance'] = True
info['LSApplicationQueriesSchemes'] = info.get('LSApplicationQueriesSchemes', [])
plistlib.dump(info, open(p, 'wb'))

# версия и в проекте Xcode (MARKETING_VERSION / CURRENT_PROJECT_VERSION)
pbx = 'ios/App/App.xcodeproj/project.pbxproj'
s = open(pbx, encoding='utf-8').read()
s = re.sub(r'MARKETING_VERSION = [^;]+;', f'MARKETING_VERSION = {short};', s)
s = re.sub(r'CURRENT_PROJECT_VERSION = [^;]+;', f'CURRENT_PROJECT_VERSION = {build};', s)
open(pbx, 'w', encoding='utf-8').write(s)
print('iOS', short, '(' + build + ')')
