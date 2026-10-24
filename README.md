# mesoestetic — справочник препаратов (Android)

## Файлы

- `index.html` — сам справочник (работает и в браузере)
- `package.json`, `capacitor.config.json` — настройки сборки
- `android-res.zip` — иконка и заставка (не распаковывать!)
- `build-apk.yml` — текст сценария сборки
- `README.md` — эта инструкция

## Как получить APK

1. На github.com: «+» → **New repository** → название `mesoestetic-guide`, **Private** → **Create repository**.
2. Нажмите **uploading an existing file**, выделите и перетащите **все файлы из архива разом**. Нажмите **Commit changes**.
3. Нажмите **Add file → Create new file**. В поле имени файла впишите ровно:
   `.github/workflows/build-apk.yml`
   (слеши сами превратят строку в папки). Откройте `build-apk.yml` из архива Блокнотом, скопируйте весь текст и вставьте в большое поле. Нажмите **Commit changes**.
4. Откройте вкладку **Actions** — сборка уже идёт (5–8 минут). После зелёной галочки откройте её и внизу в **Artifacts** скачайте `mesoestetic-guide-apk`. Внутри — `mesoestetic-guide.apk`.
5. Перешлите APK на Android-телефон, откройте и разрешите установку из неизвестных источников.

## Как обновить справочник

**Add file → Upload files** → перетащите новый `index.html` → **Commit changes**. APK пересоберётся сама.

## Если сборка красная

Откройте её → слева **build** → разверните шаг с красным крестиком и пришлите скриншот последних строк.
