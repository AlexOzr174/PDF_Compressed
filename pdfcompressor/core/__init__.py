"""Core module - Business logic and domain models"""

from pdfcompressor.core.config import (
    QualityLevel,
    CompressionMode,
    AppSettings,
    QUALITY_LEVELS,
    ESTIMATED_SIZE_RATIOS,
)
from pdfcompressor.core.validator import PDFValidator, ValidationResult
from pdfcompressor.core.compressor import PDFCompressor, CompressionResult

__all__ = [
    "QualityLevel",
    "CompressionMode", 
    "AppSettings",
    "QUALITY_LEVELS",
    "ESTIMATED_SIZE_RATIOS",
    "PDFValidator",
    "ValidationResult",
    "PDFCompressor",
    "CompressionResult",
]
