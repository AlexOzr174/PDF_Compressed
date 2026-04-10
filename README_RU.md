# PDF Compressor Pro v2.0

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Современный инструмент для сжатия PDF с использованием возможностей Python 3.14+, архитектуры Clean Architecture и поддержкой AsyncIO.

## ✨ Возможности

### Основные возможности
- **Два движка**: Ghostscript (основной) с резервным PyPDF
- **Несколько уровней качества**: Prepress, Printer, Ebook, Screen
- **Асинхронная обработка**: Неблокирующий интерфейс на asyncio
- **Пакетная обработка**: Параллельное сжатие нескольких файлов

### Пользовательский интерфейс
- **Современный GUI**: Красивые темы на базе ttkbootstrap
- **Drag & Drop**: Простой выбор файлов перетаскиванием
- **Поддержка тем**: Тёмная, светлая и синяя темы
- **Прогресс в реальном времени**: Отображение статуса сжатия

### Командная строка
- **Гибкий CLI**: Полноценный интерфейс командной строки
- **Конфигурация**: Поддержка JSON/YAML конфигов
- **Dry-run режим**: Проверка без реального выполнения
- **Цветной вывод**: Наглядные статусы операций

## 📦 Установка

### Требования
- Python 3.12 или выше
- Ghostscript (рекомендуется для лучшего качества)

### Быстрая установка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Или установка пакета в режиме разработки
pip install -e .
```

### Установка Ghostscript

**Windows:**
1. Скачайте с [официального сайта](https://ghostscript.com/releases/gsdnld.html)
2. Установите в `C:\Program Files\gs\`
3. Добавьте в PATH: `C:\Program Files\gs\gs_version\bin`

**macOS:**
```bash
brew install ghostscript
```

**Linux:**
```bash
sudo apt-get install ghostscript  # Debian/Ubuntu
sudo dnf install ghostscript      # Fedora/RHEL
sudo pacman -S ghostscript        # Arch Linux
```

## 🚀 Использование

### Графический интерфейс

```bash
# Запуск GUI
python -m pdfcompressor.ui.main_window

# Или через скрипт
pdfcompressor-gui
```

**Как использовать:**
1. Перетащите PDF файлы в окно или нажмите "Выбрать файлы"
2. Выберите уровень качества (Prepress/Printer/Ebook/Screen)
3. При необходимости укажите папку для сохранения
4. Нажмите "Сжать" и следите за прогрессом

### Командная строка

```bash
# Базовое сжатие
pdfcompressor input.pdf -q printer

# Сжатие с указанием выходного файла
pdfcompressor input.pdf -o output.pdf -q ebook

# Пакетная обработка папки
pdfcompressor ./documents/ --recursive -q screen

# Dry-run (проверка без выполнения)
pdfcompressor large.pdf --dry-run -v

# С использованием конфига
pdfcompressor input.pdf --config config.json
```

### Конфигурация

**Пример config.json:**
```json
{
  "quality": "ebook",
  "mode": "balanced",
  "output_dir": "./compressed",
  "use_ghostscript": true,
  "log_level": "INFO",
  "theme": "dark"
}
```

**Пример config.yaml:**
```yaml
quality: printer
mode: quality
output_dir: ~/pdf_output
use_ghostscript: true
log_level: DEBUG
theme: light
```

## 🏗️ Архитектура

Проект использует **Clean Architecture** и **MVVM** для GUI:

```
pdfcompressor/
├── core/              # Бизнес-логика
│   ├── config.py      # Настройки и конфигурация
│   ├── validator.py   # Валидация файлов
│   └── compressor.py  # Движки сжатия
│
├── ui/                # Пользовательский интерфейс
│   ├── main_window.py # Главное окно
│   └── components.py  # Компоненты UI
│
├── utils/             # Утилиты
│   └── logger.py      # Логирование
│
├── cli.py             # CLI интерфейс
└── tests/             # Тесты
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pdfcompressor.tests.test_all
```

Покрытие тестами:
- ✅ Валидация файлов и путей
- ✅ Движки сжатия (Ghostscript/PyPDF)
- ✅ Конфигурация и сериализация
- ✅ UI компоненты
- ✅ Интеграционные тесты

## 📊 Уровни качества

| Уровень | Сжатие | Качество | Назначение |
|---------|--------|----------|------------|
| **prepress** | ~80-90% | Максимальное | Полиграфия |
| **printer** | ~50-70% | Высокое | Печать в офисе |
| **ebook** | ~30-50% | Среднее | Чтение с экрана |
| **screen** | ~10-25% | Минимальное | Веб, email |

## 🔧 Расширение

### Добавление темы

В файле `ui/components.py`:

```python
self.themes["my_theme"] = {
    "bg": "#1a1a2e",
    "fg": "#eaeaea",
    "primary": "#0f3460",
    "secondary": "#16213e"
}
```

### Новый движок сжатия

В файле `core/compressor.py`:

```python
class MyCompressor:
    async def compress(
        self, 
        input_path: Path, 
        output_path: Path, 
        quality: str
    ) -> CompressionResult:
        # Ваша реализация
        pass
```

## 🤝 Вклад в проект

Приветствуются:
- Отчёты об ошибках
- Предложения по улучшению
- Pull Request'ы
- Улучшение документации

## 📄 Лицензия

MIT License. См. файл [LICENSE](LICENSE).

## 🙏 Благодарности

- [Ghostscript](https://ghostscript.com/) — основной движок
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) — UI фреймворк
- [PyPDF](https://pypdf.readthedocs.io/) — резервный движок

---

**Создано с ❤️ на Python 3.14+**
