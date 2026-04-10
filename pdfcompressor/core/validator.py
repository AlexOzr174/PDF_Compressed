"""
PDF Validator - Validates PDF files and paths
Uses Python 3.14+ type hints and pattern matching
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Self
from enum import StrEnum, auto

from pdfcompressor.core.config import AppSettings


class ValidationErrorCode(StrEnum):
    """Error codes for validation failures"""
    EMPTY_PATH = "empty_path"
    FILE_NOT_FOUND = "file_not_found"
    NOT_A_FILE = "not_a_file"
    WRONG_EXTENSION = "wrong_extension"
    FILE_TOO_LARGE = "file_too_large"
    EMPTY_FILE = "empty_file"
    INVALID_PDF = "invalid_pdf"
    SAME_PATHS = "same_paths"
    OUTPUT_DIR_NOT_WRITABLE = "output_dir_not_writable"
    SUCCESS = "success"


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Result of PDF validation"""
    is_valid: bool
    error_code: ValidationErrorCode | None = None
    error_message: str = ""
    file_size: int = 0
    file_size_mb: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def raise_if_invalid(self) -> Self:
        """Raise ValueError if validation failed"""
        if not self.is_valid:
            raise ValueError(f"Validation failed: {self.error_message}")
        return self


class PDFValidator:
    """
    PDF file validator with comprehensive checks
    
    Clean Architecture: Domain Logic Layer
    """
    
    def __init__(self, settings: AppSettings | None = None):
        self.settings = settings or AppSettings()
    
    def validate_path(self, path: Path | str) -> ValidationResult:
        """Validate a file path without checking if it exists"""
        path_str = str(path).strip()
        
        if not path_str:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.EMPTY_PATH,
                error_message="Path cannot be empty",
                suggestions=["Please select a PDF file"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_file_exists(self, path: Path | str) -> ValidationResult:
        """Validate that file exists"""
        path = Path(path)
        
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.FILE_NOT_FOUND,
                error_message=f"File not found: {path}",
                suggestions=[
                    "Check if the file path is correct",
                    "Ensure the file hasn't been moved or deleted"
                ]
            )
        
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.NOT_A_FILE,
                error_message=f"Path is not a file: {path}",
                suggestions=["Please select a valid file, not a directory"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_extension(self, path: Path | str) -> ValidationResult:
        """Validate file extension"""
        path = Path(path)
        ext = path.suffix.lower()
        
        if ext not in self.settings.supported_extensions:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.WRONG_EXTENSION,
                error_message=f"Unsupported file type: {ext}",
                suggestions=[
                    f"Supported formats: {', '.join(self.settings.supported_extensions)}",
                    "Please select a PDF file"
                ]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_file_size(self, path: Path | str) -> ValidationResult:
        """Validate file size is within limits"""
        path = Path(path)
        
        try:
            size_bytes = path.stat().st_size
        except (FileNotFoundError, OSError):
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.FILE_NOT_FOUND,
                error_message=f"Cannot access file: {path}",
                suggestions=["Check if the file exists and is accessible"]
            )
        
        size_mb = size_bytes / (1024 * 1024)
        
        if size_bytes == 0:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.EMPTY_FILE,
                error_message="File is empty",
                suggestions=["The PDF file appears to be corrupted or empty"]
            )
        
        if size_mb > self.settings.max_file_size_mb:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.FILE_TOO_LARGE,
                error_message=f"File too large: {size_mb:.2f} MB (max: {self.settings.max_file_size_mb} MB)",
                suggestions=[
                    "Try splitting the PDF into smaller files",
                    "Increase max_file_size_mb in settings"
                ]
            )
        
        return ValidationResult(
            is_valid=True,
            file_size=size_bytes,
            file_size_mb=size_mb
        )
    
    def validate_output_path(self, output_path: Path | str, input_path: Path | str) -> ValidationResult:
        """Validate output path is writable and different from input"""
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Check if output path is same as input
        if input_path.resolve() == output_path.resolve():
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.SAME_PATHS,
                error_message="Output path cannot be the same as input path",
                suggestions=["Choose a different output filename or location"]
            )
        
        # Check if output directory is writable
        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                return ValidationResult(
                    is_valid=False,
                    error_code=ValidationErrorCode.OUTPUT_DIR_NOT_WRITABLE,
                    error_message=f"Cannot create output directory: {e}",
                    suggestions=["Check directory permissions"]
                )
        elif not os.access(output_dir, os.W_OK):
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.OUTPUT_DIR_NOT_WRITABLE,
                error_message=f"Output directory is not writable: {output_dir}",
                suggestions=["Check directory permissions"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_pdf_content(self, path: Path | str) -> ValidationResult:
        """Basic PDF content validation"""
        path = Path(path)
        
        try:
            with open(path, "rb") as f:
                header = f.read(8)
                if not header.startswith(b"%PDF"):
                    return ValidationResult(
                        is_valid=False,
                        error_code=ValidationErrorCode.INVALID_PDF,
                        error_message="File does not appear to be a valid PDF",
                        suggestions=["Ensure the file is a valid PDF document"]
                    )
        except (IOError, PermissionError) as e:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.FILE_NOT_FOUND,
                error_message=f"Cannot read file: {e}",
                suggestions=["Check file permissions"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_full(self, input_path: Path | str, output_path: Path | str | None = None) -> ValidationResult:
        """
        Perform complete validation
        
        Uses structural pattern matching (Python 3.10+)
        """
        input_path = Path(input_path)
        
        # Sequential validation with early exit
        validations = [
            self.validate_path(input_path),
            self.validate_file_exists(input_path),
            self.validate_extension(input_path),
            self.validate_file_size(input_path),
            self.validate_pdf_content(input_path),
        ]
        
        for result in validations:
            if not result.is_valid:
                return result
        
        # Validate output path if provided
        if output_path:
            output_result = self.validate_output_path(output_path, input_path)
            if not output_result.is_valid:
                return output_result
        
        # All validations passed
        file_size = input_path.stat().st_size
        return ValidationResult(
            is_valid=True,
            error_code=ValidationErrorCode.SUCCESS,
            error_message="Validation successful",
            file_size=file_size,
            file_size_mb=file_size / (1024 * 1024)
        )
    
    @staticmethod
    def estimate_output_size(input_size_mb: float, quality_ratio: float) -> float:
        """Estimate output file size based on quality ratio"""
        return round(input_size_mb * quality_ratio, 2)


# Import os at module level for validate_output_path
import os
