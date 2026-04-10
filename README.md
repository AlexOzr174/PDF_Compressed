# 📄 PDF Compressor Pro v2.0

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern PDF compression tool built with Python 3.14+ features, Clean Architecture, and AsyncIO support.

## ✨ Features

### Core Features
- **Dual Engine Support**: Ghostscript (primary) with PyPDF fallback
- **Multiple Quality Levels**: Prepress, Printer, Ebook, Screen
- **Async Processing**: Non-blocking UI with asyncio
- **Batch Processing**: Compress multiple files concurrently

### User Interface
- **Modern GUI**: Built with ttkbootstrap for beautiful themes
- **Drag & Drop**: Easy file selection
- **Theme Support**: Dark, Light, and Blue themes
- **Real-time Progress**: Live compression status updates
- **Detailed Logging**: Color-coded log output

### Command Line
- **Full CLI Support**: All features available from command line
- **Batch Mode**: Process multiple files at once
- **Dry Run**: Preview operations without executing
- **Configurable**: JSON/YAML configuration support

### Architecture
- **Clean Architecture**: Separation of concerns (UI, Core, Services)
- **MVVM Pattern**: Model-View-ViewModel for the GUI
- **Type Safety**: Full type hints with Python 3.12+ syntax
- **Testable**: Comprehensive test suite included

## 🚀 Installation

### From Source
```bash
git clone https://github.com/pdfcompressor/pdfcompressor.git
cd pdfcompressor
pip install -e .
```

### With Development Dependencies
```bash
pip install -e ".[dev]"
```

### Requirements
- Python 3.12 or higher
- Ghostscript (optional, recommended for best results)
- ttkbootstrap, PyYAML, pypdf (installed automatically)

## 💻 Usage

### GUI Application
```bash
# Launch GUI
pdfcompressor-gui

# Or run directly
python -m pdfcompressor.ui.main_window
```

### Command Line
```bash
# Basic compression
pdfcompressor input.pdf

# Specify output file
pdfcompressor input.pdf -o output.pdf

# Maximum compression
pdfcompressor input.pdf -q screen

# Batch processing
pdfcompressor *.pdf -q ebook

# Use PyPDF engine
pdfcompressor input.pdf --mode pypdf

# Verbose output
pdfcompressor input.pdf -v

# Dry run (preview only)
pdfcompressor input.pdf --dry-run

# With config file
pdfcompressor input.pdf --config settings.json
```

### CLI Options
| Option | Description |
|--------|-------------|
| `input` | Input PDF file(s) |
| `-o, --output` | Output file path |
| `-d, --output-dir` | Output directory for batch |
| `-q, --quality` | Quality level (prepress/printer/ebook/screen) |
| `-m, --mode` | Engine (ghostscript/pypdf/auto) |
| `-v, --verbose` | Verbose output |
| `--dry-run` | Preview without compressing |
| `--config` | Configuration file path |

## 📁 Project Structure

```
pdfcompressor/
├── core/                   # Business logic
│   ├── config.py          # Configuration & settings
│   ├── validator.py       # File validation
│   └── compressor.py      # Compression logic
├── ui/                     # User interface
│   ├── main_window.py     # Main application window
│   └── components.py      # Reusable components
├── utils/                  # Utilities
│   └── logger.py          # Logging setup
├── services/               # External services (future)
├── tests/                  # Test suite
│   └── test_all.py        # Comprehensive tests
├── cli.py                  # Command-line interface
└── __init__.py             # Package initialization
```

## ⚙️ Configuration

### JSON Configuration
```json
{
  "default_quality": "printer",
  "default_mode": "auto",
  "output_suffix": "_compressed",
  "create_backup": true,
  "max_file_size_mb": 100,
  "theme": "dark",
  "language": "en"
}
```

### YAML Configuration
```yaml
default_quality: printer
default_mode: auto
output_suffix: _compressed
create_backup: true
max_file_size_mb: 100
theme: dark
language: en
```

Save as `~/.pdfcompressor/settings.json` or use `--config` flag.

## 🧪 Testing

```bash
# Run all tests
python -m pdfcompressor.tests.test_all

# With pytest
pytest pdfcompressor/tests/

# With coverage
pytest --cov=pdfcompressor pdfcompressor/tests/
```

## 🎯 Quality Levels

| Level | Description | Est. Reduction | Best For |
|-------|-------------|----------------|----------|
| prepress | Highest quality | ~30% | Professional printing |
| printer | High quality | ~50% | Office documents |
| ebook | Medium quality | ~70% | E-books, web |
| screen | Maximum compression | ~85% | Email attachments |

## 🛠️ Development

### Code Quality
```bash
# Format code
black pdfcompressor/

# Lint code
ruff check pdfcompressor/

# Type checking
mypy pdfcompressor/
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest pdfcompressor/tests/test_all.py -v

# With coverage
pytest --cov=pdfcompressor --cov-report=html
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [Ghostscript](https://ghostscript.com/) - PDF processing engine
- [PyPDF](https://pypdf.readthedocs.io/) - Python PDF library
- [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) - Modern tkinter themes

---

Built with ❤️ using Python 3.14+ features
