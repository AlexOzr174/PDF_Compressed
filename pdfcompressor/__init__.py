"""
PDF Compressor - Modern PDF Compression Tool
Built with Python 3.14+ features, Clean Architecture, and AsyncIO
"""

__version__ = "2.0.0"
__author__ = "PDF Compressor Team"
__license__ = "MIT"

from pdfcompressor.core.compressor import PDFCompressor
from pdfcompressor.ui.main_window import PDFCompressorApp
from pdfcompressor.utils.logger import setup_logger

__all__ = [
    "PDFCompressor",
    "PDFCompressorApp", 
    "setup_logger",
]
