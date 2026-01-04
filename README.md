# PDF Compressor M1 Optimized

Это приложение на Python с графическим интерфейсом, предназначенное для сжатия PDF-файлов. Особенность — оптимизация под Apple Silicon (M1/M2), хотя работает и на других системах.

## Особенности

*   **Графический интерфейс:** Построен на `tkinter` и `ttkbootstrap`.
*   **Два режима сжатия:**
    *   **Ghostscript:** Более эффективное сжатие изображений и оптимизация PDF.
    *   **PyPDF:** Резервный режим, работает при отсутствии Ghostscript.
*   **Предварительный просмотр:** Возможность оценить потенциальный размер сжатого файла.
*   **Контроль качества:** Выбор из 4-х уровней сжатия (от "пресс" до "экран").
*   **Многопоточность:** Основные операции выполняются в фоновом потоке, интерфейс не зависает.

## Требования

*   Python 3.8+
*   [Ghostscript](https://www.ghostscript.com/) (рекомендуется для эффективного сжатия)
    *   Установка на macOS (с помощью Homebrew): `brew install ghostscript`

## Установка и запуск

1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/AlexOzr174/PDF_Compressed.git
    ```
2.  Перейдите в папку проекта:
    ```bash
    cd PDF_Compressed
    ```
3.  (Рекомендуется) Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv venv
    source venv/bin/activate  # На Windows: venv\Scripts\activate
    ```
4.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```
5.  Запустите приложение:
    ```bash
    python main.py
    ```

## Использованные библиотеки

*   `ttkbootstrap`
*   `pypdf` (или `PyPDF2`)
*   `tkinter`

(См. `requirements.txt` для полного списка)

## Автор

AlexOzr174