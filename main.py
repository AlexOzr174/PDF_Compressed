import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttkb
import os
import subprocess
import threading
import logging
import time
import shutil
import sys
from pathlib import Path
from enum import Enum

# Оптимизированные импорты для M1
try:
    import pypdf
    from pypdf import PdfReader, PdfWriter

    PDF_LIB = "pypdf"
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter

    PDF_LIB = "PyPDF2"

# Константы
WINDOW_SIZE = "900x700"
WINDOW_TITLE = "PDF Compressor M1 Optimized"
ENTRY_WIDTH = 70
LOG_TEXT_HEIGHT = 15
LOG_TEXT_WIDTH = 80
INITIAL_DIR = str(Path.home() / "Documents")

# Уровни качества
QUALITY_LEVELS = {
    "Высокое (пресс)": "/prepress",
    "Хорошее (принтер)": "/printer",
    "Среднее (книга)": "/ebook",
    "Низкое (экран)": "/screen"
}


class CompressionMode(Enum):
    GHOSTSCRIPT = "ghostscript"
    PYPDF = "pypdf"


# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip:
            return
        x, y = self.widget.winfo_rootx(), self.widget.winfo_rooty()
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        # Исправление позиционирования тултипа
        self.tooltip.wm_geometry(f"+{x + 25}+{y + 20}")
        label = tk.Label(
            self.tooltip, text=self.text,
            background="#ffffe0", relief="solid",
            borderwidth=1, font=("Helvetica", 9)
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class PDFCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)

        # Переменные
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.quality_level = tk.StringVar(value=list(QUALITY_LEVELS.keys())[1])
        self.progress = tk.DoubleVar(value=0)
        self.preview_result = tk.StringVar(value="Ожидаемый размер: не рассчитан")
        self.is_compressing = False
        self.is_previewing = False

        # Проверка Ghostscript
        self.ghostscript_available = self._check_ghostscript()
        self.compression_mode = CompressionMode.GHOSTSCRIPT if self.ghostscript_available else CompressionMode.PYPDF

        # Логгер для GUI
        self.log_handler = TextHandler(self)
        logger.addHandler(self.log_handler)

        # Создание интерфейса
        self.setup_ui()
        logger.info(f"Запуск на {sys.platform}")
        logger.info(f"Используется библиотека PDF: {PDF_LIB}")
        logger.info(f"Режим сжатия: {self.compression_mode.value}")
        logger.info(f"Ghostscript доступен: {self.ghostscript_available}")

    def _check_ghostscript(self) -> bool:
        """Проверка Ghostscript"""
        gs_paths = [
            "/usr/local/bin/gs",
            "/opt/homebrew/bin/gs",  # Путь для Homebrew на M1
            "/usr/bin/gs",
            shutil.which("gs")
        ]

        for path in gs_paths:
            if path and os.path.exists(path):
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5  # Увеличил таймаут для надежности
                    )
                    if result.returncode == 0:
                        logger.info(f"Ghostscript найден: {path}")
                        return True
                except Exception as e:
                    logger.warning(f"Не удалось проверить Ghostscript по пути {path}: {e}")
                    continue
        logger.warning("Ghostscript не найден. Будет использован резервный режим.")
        return False

    def setup_ui(self):
        """Настройка интерфейса"""
        # Основной фрейм с padding
        main_frame = ttkb.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_frame = ttkb.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        ttkb.Label(
            title_frame,
            text=WINDOW_TITLE,
            font=("Helvetica", 16, "bold")
        ).pack(side=tk.LEFT)

        if sys.platform == "darwin":
            ttkb.Label(
                title_frame,
                text="✓ Оптимизировано для Apple Silicon",
                font=("Helvetica", 10),
                bootstyle="success"
            ).pack(side=tk.RIGHT)

        # Выбор входного файла
        input_frame = ttkb.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 15))

        ttkb.Label(input_frame, text="Исходный PDF:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)

        input_subframe = ttkb.Frame(input_frame)
        input_subframe.pack(fill=tk.X, pady=5)

        input_entry = ttkb.Entry(input_subframe, textvariable=self.input_path, width=ENTRY_WIDTH)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        input_btn = ttkb.Button(
            input_subframe,
            text="Выбрать файл",
            command=self.select_input_file,
            width=15
        )
        input_btn.pack(side=tk.RIGHT)

        # Выбор пути сохранения
        output_frame = ttkb.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=(0, 15))

        ttkb.Label(output_frame, text="Выходной файл:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)

        output_subframe = ttkb.Frame(output_frame)
        output_subframe.pack(fill=tk.X, pady=5)

        output_entry = ttkb.Entry(output_subframe, textvariable=self.output_path, width=ENTRY_WIDTH)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        output_btn = ttkb.Button(
            output_subframe,
            text="Выбрать путь",
            command=self.select_output_path,
            width=15
        )
        output_btn.pack(side=tk.RIGHT)

        # Настройки сжатия
        settings_frame = ttkb.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        ttkb.Label(settings_frame, text="Настройки сжатия:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)

        settings_subframe = ttkb.Frame(settings_frame)
        settings_subframe.pack(fill=tk.X, pady=5)

        ttkb.Label(settings_subframe, text="Качество:").pack(side=tk.LEFT, padx=(0, 10))

        quality_combo = ttkb.Combobox(
            settings_subframe,
            textvariable=self.quality_level,
            values=list(QUALITY_LEVELS.keys()),
            state="readonly",
            width=40
        )
        quality_combo.pack(side=tk.LEFT, padx=(0, 20))

        # Информация о режиме
        self.mode_label = ttkb.Label(
            settings_subframe,
            text=f"Режим: {self.compression_mode.value.upper()}",
            font=("Helvetica", 9)
        )
        self.mode_label.pack(side=tk.LEFT)

        # Прогресс-бар
        progress_frame = ttkb.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_label = ttkb.Label(progress_frame, text="Готов к работе")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        self.progressbar = ttkb.Progressbar(
            progress_frame,
            variable=self.progress,
            maximum=100,
            mode="determinate",
            bootstyle="success-striped"
        )
        self.progressbar.pack(fill=tk.X, pady=5)

        # Результат предпросмотра
        preview_frame = ttkb.Frame(main_frame)
        preview_frame.pack(fill=tk.X, pady=(0, 15))

        self.preview_label = ttkb.Label(
            preview_frame,
            textvariable=self.preview_result,
            font=("Helvetica", 10, "bold")
        )
        self.preview_label.pack(anchor=tk.W)

        # Кнопки управления
        button_frame = ttkb.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))

        self.preview_btn = ttkb.Button(
            button_frame,
            text="Предпросмотр",
            command=self.start_preview,
            bootstyle="info",
            width=20
        )
        self.preview_btn.pack(side=tk.LEFT, padx=5)

        self.compress_btn = ttkb.Button(
            button_frame,
            text="Сжать PDF",
            command=self.start_compression,
            bootstyle="success",
            width=20
        )
        self.compress_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttkb.Button(
            button_frame,
            text="Отмена",
            command=self.cancel_operation,
            bootstyle="danger",
            width=15
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Логи
        log_frame = ttkb.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        ttkb.Label(log_frame, text="Логи операций:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)

        self.log_text = tk.Text(
            log_frame,
            height=LOG_TEXT_HEIGHT,
            width=LOG_TEXT_WIDTH,
            state="disabled",
            font=("Monaco", 9) if sys.platform == "darwin" else ("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        log_scrollbar = ttkb.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def select_input_file(self):
        """Выбор входного PDF-файла"""
        try:
            file_path = filedialog.askopenfilename(
                initialdir=INITIAL_DIR,
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ],
                title="Выберите PDF-файл"
            )
            if file_path:
                self.input_path.set(file_path)
                output_path = Path(file_path).parent / f"{Path(file_path).stem}_compressed.pdf"
                self.output_path.set(str(output_path))
                self.preview_result.set("Ожидаемый размер: не рассчитан")
                self.update_status(f"Выбран файл: {Path(file_path).name}")
                logger.info(f"Выбран входной файл: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при выборе файла: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось выбрать файл: {str(e)}")

    def select_output_path(self):
        """Выбор пути сохранения"""
        try:
            initial_file = self.output_path.get() or str(Path(INITIAL_DIR) / "compressed.pdf")
            file_path = filedialog.asksaveasfilename(
                initialdir=Path(initial_file).parent,
                initialfile=Path(initial_file).name,
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Сохранить как"
            )
            if file_path:
                self.output_path.set(file_path)
                self.update_status(f"Выходной файл: {Path(file_path).name}")
                logger.info(f"Выбран путь сохранения: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при выборе пути: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось выбрать путь: {str(e)}")

    def update_status(self, message: str):
        """Обновление статуса"""
        self.progress_label.config(text=message)
        self.root.update_idletasks()

    def update_progress(self, value: int, message: str = ""):
        """Обновление прогресса"""
        self.progress.set(value)
        if message:
            self.update_status(message)

    def start_preview(self):
        """Запуск предпросмотра"""
        if self.is_previewing or self.is_compressing:
            messagebox.showwarning("Внимание", "Операция уже выполняется!")
            return

        input_path = self.input_path.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Ошибка", "Выберите существующий PDF-файл!")
            return

        self.is_previewing = True
        self.set_buttons_state(False)
        self.update_progress(0, "Начало предпросмотра...")

        threading.Thread(
            target=self.preview_compression,
            args=(input_path,),
            daemon=True
        ).start()

    def preview_compression(self, input_path: str):
        """Оценка размера сжатого файла"""
        try:
            start_time = time.time()
            logger.info("Начало предпросмотра...")

            original_size = os.path.getsize(input_path)
            # Улучшенная логика оценки сжатия
            estimated_size_ratio = {
                "Высокое (пресс)": 0.9,  # Меньшее сжатие
                "Хорошее (принтер)": 0.7,
                "Среднее (книга)": 0.5,
                "Низкое (экран)": 0.3  # Большее сжатие
            }
            quality_key = self.quality_level.get()
            estimated_size = original_size * estimated_size_ratio.get(quality_key, 0.7)

            # Расчет результатов
            original_size_mb = original_size / (1024 * 1024)
            estimated_size_mb = estimated_size / (1024 * 1024)
            reduction_pct = max(0, (1 - estimated_size / original_size) * 100)

            result_text = (
                f"Исходно: {original_size_mb:.2f} MB → "
                f"Оценка: {estimated_size_mb:.2f} MB "
                f"(↓{reduction_pct:.1f}%)"
            )

            self.root.after(0, lambda: self.preview_result.set(result_text))  # Потокобезопасное обновление
            self.update_progress(100, "Предпросмотр завершен")
            logger.info(f"Предпросмотр завершен за {time.time() - start_time:.2f} сек")

        except Exception as e:
            logger.error(f"Ошибка предпросмотра: {str(e)}")
            self.root.after(0, lambda: self.preview_result.set("Ошибка оценки"))  # Потокобезопасное обновление
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", f"Не удалось выполнить предпросмотр: {str(e)}"
            ))
        finally:
            self.is_previewing = False
            self.set_buttons_state(True)

    def start_compression(self):
        """Запуск сжатия"""
        if self.is_compressing or self.is_previewing:
            messagebox.showwarning("Внимание", "Операция уже выполняется!")
            return

        input_path = self.input_path.get()
        output_path = self.output_path.get()

        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Ошибка", "Выберите существующий PDF-файл!")
            return
        if not output_path:
            messagebox.showerror("Ошибка", "Укажите путь для сохранения!")
            return

        # Проверка, чтобы не перезаписать исходный файл
        if os.path.abspath(input_path) == os.path.abspath(output_path):
            messagebox.showerror("Ошибка", "Выходной файл не может совпадать с исходным!")
            return

        self.is_compressing = True
        self.set_buttons_state(False)
        self.update_progress(0, "Подготовка к сжатию...")

        threading.Thread(
            target=self.compress_pdf,
            args=(input_path, output_path),
            daemon=True
        ).start()

    def compress_pdf(self, input_path: str, output_path: str):
        """Основная функция сжатия"""
        try:
            start_time = time.time()
            logger.info(f"Начало сжатия: {input_path}")

            original_size = os.path.getsize(input_path)

            if self.compression_mode == CompressionMode.GHOSTSCRIPT:
                self._compress_with_ghostscript(input_path, output_path)
            else:
                self._compress_with_pypdf(input_path, output_path)

            # Проверка результата
            if not os.path.exists(output_path):
                raise FileNotFoundError("Выходной файл не создан")

            compressed_size = os.path.getsize(output_path)
            reduction = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0

            result_msg = (
                f"Сжатие завершено за {time.time() - start_time:.1f} сек\n"
                f"Размер: {original_size / 1024 / 1024:.2f} MB → {compressed_size / 1024 / 1024:.2f} MB\n"
                f"Экономия: {reduction:.1f}%"
            )

            self.root.after(0, lambda: messagebox.showinfo(
                "Успех",
                result_msg
            ))

            logger.info(f"Сжатие завершено: {reduction:.1f}% экономии")
            self.update_progress(100, "Сжатие завершено")

        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка Ghostscript: {e.stderr}")
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", f"Ошибка Ghostscript: {e.stderr[:200] if e.stderr else 'Неизвестная ошибка'}"
            ))
        except Exception as e:
            logger.error(f"Ошибка сжатия: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", f"Не удалось сжать PDF: {str(e)}"
            ))
        finally:
            self.is_compressing = False
            self.set_buttons_state(True)

    def _compress_with_ghostscript(self, input_path: str, output_path: str):
        """Сжатие с использованием Ghostscript"""
        quality = QUALITY_LEVELS[self.quality_level.get()]

        cmd = [
            "gs",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            "-sDEVICE=pdfwrite",
            f"-dPDFSETTINGS={quality}",
            "-dCompatibilityLevel=1.4",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=true",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=true",
            "-dColorImageResolution=150",
            "-dGrayImageResolution=150",
            "-dMonoImageResolution=150",
            f"-sOutputFile={output_path}",
            input_path
        ]

        self.update_progress(25, "Запуск Ghostscript...")

        process = subprocess.run(cmd, capture_output=True, text=True, timeout=120) # Увеличил таймаут

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=process.stderr)

        self.update_progress(75, "Завершение обработки...")

    def _compress_with_pypdf(self, input_path: str, output_path: str):
        """Сжатие с использованием PyPDF (ограниченное)"""
        logger.warning("PyPDF не поддерживает сжатие изображений. Используется простое копирование страниц.")
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            writer = PdfWriter()

            self.update_progress(10, f"Обработка {total_pages} страниц...")

            for i, page in enumerate(reader.pages):
                writer.add_page(page)

                progress = 10 + int((i + 1) / total_pages * 80)
                self.update_progress(progress, f"Страница {i + 1}/{total_pages}")

            self.update_progress(95, "Сохранение файла...")

            with open(output_path, "wb") as f:
                writer.write(f)

        except Exception as e:
            logger.error(f"Ошибка PyPDF: {str(e)}")
            raise

    def set_buttons_state(self, enabled: bool):
        """Управление состоянием кнопок"""
        state = "normal" if enabled else "disabled"
        # Потокобезопасное обновление состояния кнопок
        self.root.after(0, lambda: self.compress_btn.config(state=state))
        self.root.after(0, lambda: self.preview_btn.config(state=state))

    def cancel_operation(self):
        """Отмена текущей операции (ограниченно)"""
        # Реальная отмена процесса subprocess невозможна без усложнения логики
        # Показываем предупреждение, что отмена не мгновенная
        if self.is_compressing or self.is_previewing:
            messagebox.showwarning("Отмена", "Операция запущена. Для остановки закройте приложение.")
            logger.info("Пользователь запросил отмену, но операция уже запущена.")


class TextHandler(logging.Handler):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def emit(self, record):
        try:
            msg = self.format(record)
            # Потокобезопасное добавление лога
            self.app.root.after(0, self._append_log, msg)
        except Exception as e:
            print(f"Ошибка в TextHandler: {e}") # Лог в консоль при ошибке

    def _append_log(self, msg):
        if hasattr(self.app, 'log_text') and self.app.log_text:
            # Потокобезопасное обновление текстового поля
            self.app.log_text.config(state="normal")
            self.app.log_text.insert(tk.END, msg + "\n")
            self.app.log_text.see(tk.END)
            self.app.log_text.config(state="disabled")


def main():
    try:
        theme = "flatly" if sys.platform == "darwin" else "cosmo"
        root = ttkb.Window(themename=theme)
        app = PDFCompressorApp(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
        messagebox.showerror(
            "Фатальная ошибка",
            f"Приложение завершилось с ошибкой:\n{str(e)}"
        )


if __name__ == "__main__":
    main()