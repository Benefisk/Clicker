# Clicker Club (Vibe)

Игра-кликер для Windows с отдельным стилизованным окном на Pygame: магазин скинов, улучшение силы клика, настройки, сброс прогресса и сохранение.

## Запуск игры

Самостоятельный файл находится в `dist/ClickerClub.exe`. Python для запуска не нужен.
Архив с установкой и ярлыками находится в `release/ClickerClub-Installer.zip`.

Прогресс сохраняется в `clicker_save.json` рядом с запущенным файлом.

## Запуск из исходников

```powershell
python -m pip install -r requirements.txt
python clicker.py
```

Сборка Windows-файла: `pyinstaller --noconfirm ClickerClub.spec`.
