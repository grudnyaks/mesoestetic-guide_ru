#!/usr/bin/env python3
"""Настройка Android-проекта после `npx cap add android` (запускается в сборке на GitHub).

- тема DayNight: WebView узнаёт системную тёмную тему (с Light-темой справочник всегда был бы светлым);
- старт приложения — чёрный экран без значка Capacitor, дальше анимированная заставка справочника;
- цвет панели навигации под светлую/тёмную тему системы;
- масштаб текста WebView фиксирован (крупный системный шрифт ломал вёрстку);
- номер версии APK = версия справочника из version.json;
- только портретная ориентация (автоповорот выключен).
"""
import json, os, re, sys, glob

RES = 'android/app/src/main/res'
ver = json.load(open('version.json', encoding='utf-8'))['version']
build_no = os.environ.get('GITHUB_RUN_NUMBER', '1')

# 1) убрать стандартные картинки заставки Capacitor (drawable-port-*/land-* перекрывали нашу)
for f in glob.glob(f'{RES}/drawable*/splash.png'):
    os.remove(f); print('removed', f)

def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text); print('wrote', path)

w(f'{RES}/drawable/splash.xml', '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#000000"/>
</shape>
''')
w(f'{RES}/drawable/splash_blank.xml', '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#00000000"/>
    <size android:width="1dp" android:height="1dp"/>
</shape>
''')

# 2) цвета панели навигации: до Android 8.1 светлых иконок нет — оставляем чёрную
def res_vals(nav, light):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="meso_nav">{nav}</color>
    <bool name="meso_light_nav">{light}</bool>
</resources>
'''
w(f'{RES}/values/meso_bars.xml', res_vals('#000000', 'false'))
w(f'{RES}/values-v27/meso_bars.xml', res_vals('#FFFFFF', 'true'))
w(f'{RES}/values-night-v27/meso_bars.xml', res_vals('#000000', 'false'))

# 3) темы
styles_path = f'{RES}/values/styles.xml'
orig = open(styles_path, encoding='utf-8').read() if os.path.exists(styles_path) else ''
has_splash_api = 'Theme.SplashScreen' in orig
launch = ('''    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="android:background">@drawable/splash</item>
        <item name="windowSplashScreenBackground">#000000</item>
        <item name="windowSplashScreenAnimatedIcon">@drawable/splash_blank</item>
        <item name="postSplashScreenTheme">@style/AppTheme.NoActionBar</item>
        <item name="android:statusBarColor">#000000</item>
        <item name="android:navigationBarColor">#000000</item>
    </style>''' if has_splash_api else '''    <style name="AppTheme.NoActionBarLaunch" parent="AppTheme.NoActionBar">
        <item name="android:background">@drawable/splash</item>
        <item name="android:windowBackground">@drawable/splash</item>
        <item name="android:navigationBarColor">#000000</item>
    </style>''')
w(styles_path, f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="Theme.AppCompat.DayNight.DarkActionBar">
        <item name="colorPrimary">#000000</item>
        <item name="colorPrimaryDark">#000000</item>
        <item name="colorAccent">#000000</item>
    </style>
    <style name="AppTheme.NoActionBar" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="windowActionBar">false</item>
        <item name="windowNoTitle">true</item>
        <item name="android:background">@null</item>
        <item name="android:windowBackground">#000000</item>
        <item name="android:statusBarColor">#000000</item>
        <item name="android:navigationBarColor">@color/meso_nav</item>
        <item name="android:windowLightNavigationBar">@bool/meso_light_nav</item>
    </style>
{launch}
</resources>
''')

# 4) масштаб текста WebView = 100%: системный «крупный шрифт» иначе раздувает текст и ломает вёрстку
act = 'android/app/src/main/java/ru/mesoestetic/guide/MainActivity.java'
w(act, """package ru.mesoestetic.guide;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getBridge() != null && getBridge().getWebView() != null) {
            getBridge().getWebView().getSettings().setTextZoom(100);
        }
    }
}
""")

# 5) версия APK
g = 'android/app/build.gradle'
s = open(g, encoding='utf-8').read()
s2 = re.sub(r'versionCode\s+\d+', f'versionCode {build_no}', s)
s2 = re.sub(r'versionName\s+"[^"]*"', f'versionName "{ver}"', s2)
if s2 == s: sys.exit('не нашёл versionCode/versionName в build.gradle')
open(g, 'w', encoding='utf-8').write(s2)
print(f'version {ver} ({build_no}), splash api: {has_splash_api}')

# только портретная ориентация: экран не поворачивается вместе с телефоном
man = 'android/app/src/main/AndroidManifest.xml'
m = open(man, encoding='utf-8').read()
m = re.sub(r'\s*android:screenOrientation="[^"]*"', '', m)
m = re.sub(r'(<activity\b)', r'\1\n            android:screenOrientation="portrait"', m, count=1)
open(man, 'w', encoding='utf-8').write(m); print('portrait', man)
