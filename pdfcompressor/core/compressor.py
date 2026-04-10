"""
PDF Compressor - Core compression logic with AsyncIO support
Clean Architecture: Application Service Layer
"""

import asyncio
import subprocess
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Self, Protocol
from enum import StrEnum

from pdfcompressor.core.config import (
    QualityLevel,
    CompressionMode,
    AppSettings,
    QUALITY_INFO,
    ESTIMATED_SIZE_RATIOS,
)
from pdfcompressor.core.validator import PDFValidator, ValidationResult


class CompressionStatus(StrEnum):
    """Status of compression operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True, frozen=True)
class CompressionResult:
    """Result of a compression operation"""
    success: bool
    input_path: Path
    output_path: Path
    original_size: int
    compressed_size: int
    compression_ratio: float
    status: CompressionStatus
    error_message: str = ""
    duration_ms: int = 0
    mode_used: CompressionMode = CompressionMode.AUTO
    quality_level: QualityLevel = QualityLevel.PRINTER
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def original_size_mb(self) -> float:
        return self.original_size / (1024 * 1024)
    
    @property
    def compressed_size_mb(self) -> float:
        return self.compressed_size / (1024 * 1024)
    
    @property
    def savings_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        return round((1 - self.compressed_size / self.original_size) * 100, 2)
    
    def __bool__(self) -> bool:
        return self.success


class ProgressCallback(Protocol):
    """Protocol for progress callbacks"""
    def __call__(self, current: int, total: int, message: str) -> None: ...


class PDFCompressor:
    """
    PDF Compressor service with Ghostscript and PyPDF fallback
    
    Clean Architecture: Application Service
    Supports async operations for non-blocking UI
    """
    
    def __init__(
        self,
        settings: AppSettings | None = None,
        progress_callback: ProgressCallback | None = None,
    ):
        self.settings = settings or AppSettings()
        self.progress_callback = progress_callback
        self.validator = PDFValidator(settings)
        self._ghostscript_available: bool | None = None
        self._gs_path: str | None = None
    
    def _find_ghostscript(self) -> tuple[bool, str | None]:
        """Find Ghostscript installation"""
        if self._ghostscript_available is not None:
            return self._ghostscript_available, self._gs_path
        
        # Check common paths based on platform
        import platform
        system = platform.system().lower()
        
        paths_to_check = [
            shutil.which("gs"),
            shutil.which("gswin64c"),
            shutil.which("gswin32c"),
        ]
        
        # Add configured paths
        if system in self.settings.ghostscript_paths:
            gs_pattern = self.settings.ghostscript_paths[system]
            if "*" not in gs_pattern:
                paths_to_check.append(gs_pattern)
        
        # Filter None values and check each path
        for path in filter(None, paths_to_check):
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._ghostscript_available = True
                    self._gs_path = path
                    return True, path
            except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
                continue
        
        self._ghostscript_available = False
        self._gs_path = None
        return False, None
    
    @property
    def ghostscript_available(self) -> bool:
        """Check if Ghostscript is available"""
        available, _ = self._find_ghostscript()
        return available
    
    @property
    def ghostscript_version(self) -> str | None:
        """Get Ghostscript version string"""
        available, gs_path = self._find_ghostscript()
        if not available or not gs_path:
            return None
        
        try:
            result = subprocess.run(
                [gs_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.SubprocessError, TimeoutError):
            return None
    
    def _get_mode(self, mode: CompressionMode) -> CompressionMode:
        """Determine actual compression mode to use"""
        if mode == CompressionMode.AUTO:
            return CompressionMode.GHOSTSCRIPT if self.ghostscript_available else CompressionMode.PYPDF
        return mode
    
    async def compress_async(
        self,
        input_path: Path | str,
        output_path: Path | str | None = None,
        quality: QualityLevel = QualityLevel.PRINTER,
        mode: CompressionMode = CompressionMode.AUTO,
    ) -> CompressionResult:
        """
        Compress PDF asynchronously
        
        Uses asyncio.to_thread for blocking I/O operations
        """
        input_path = Path(input_path)
        
        # Validate input
        validation = self.validator.validate_full(input_path, output_path)
        if not validation:
            return CompressionResult(
                success=False,
                input_path=input_path,
                output_path=output_path or Path(),
                original_size=0,
                compressed_size=0,
                compression_ratio=0.0,
                status=CompressionStatus.FAILED,
                error_message=validation.error_message,
            )
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}{self.settings.output_suffix}.pdf"
        output_path = Path(output_path)
        
        # Determine mode
        actual_mode = self._get_mode(mode)
        
        start_time = datetime.now()
        
        try:
            if self.progress_callback:
                self.progress_callback(0, 100, "Starting compression...")
            
            # Run compression in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._compress_sync(input_path, output_path, quality, actual_mode),
            )
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if self.progress_callback:
                self.progress_callback(100, 100, "Compression completed!")
            
            return CompressionResult(
                success=result.success,
                input_path=input_path,
                output_path=output_path,
                original_size=result.original_size,
                compressed_size=result.compressed_size,
                compression_ratio=result.compression_ratio,
                status=CompressionStatus.COMPLETED if result.success else CompressionStatus.FAILED,
                error_message=result.error_message,
                duration_ms=duration_ms,
                mode_used=actual_mode,
                quality_level=quality,
            )
            
        except asyncio.CancelledError:
            return CompressionResult(
                success=False,
                input_path=input_path,
                output_path=output_path,
                original_size=input_path.stat().st_size,
                compressed_size=0,
                compression_ratio=0.0,
                status=CompressionStatus.CANCELLED,
                error_message="Compression was cancelled",
            )
        except Exception as e:
            return CompressionResult(
                success=False,
                input_path=input_path,
                output_path=output_path,
                original_size=input_path.stat().st_size,
                compressed_size=0,
                compression_ratio=0.0,
                status=CompressionStatus.FAILED,
                error_message=f"Unexpected error: {e}",
            )
    
    def _compress_sync(
        self,
        input_path: Path,
        output_path: Path,
        quality: QualityLevel,
        mode: CompressionMode,
    ) -> CompressionResult:
        """Synchronous compression implementation"""
        original_size = input_path.stat().st_size
        
        try:
            if mode == CompressionMode.GHOSTSCRIPT:
                return self._compress_with_ghostscript(input_path, output_path, quality, original_size)
            else:
                return self._compress_with_pypdf(input_path, output_path, quality, original_size)
        except Exception as e:
            return CompressionResult(
                success=False,
                input_path=input_path,
                output_path=output_path,
                original_size=original_size,
                compressed_size=0,
                compression_ratio=0.0,
                status=CompressionStatus.FAILED,
                error_message=str(e),
                quality_level=quality,
                mode_used=mode,
            )
    
    def _compress_with_ghostscript(
        self,
        input_path: Path,
        output_path: Path,
        quality: QualityLevel,
        original_size: int,
    ) -> CompressionResult:
        """Compress using Ghostscript"""
        available, gs_path = self._find_ghostscript()
        if not available or not gs_path:
            raise RuntimeError("Ghostscript not found")
        
        cmd = [
            gs_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{quality.value}",
            "-dNOPAUSE",
            "-dBATCH",
            "-dSAFER",
            f"-sOutputFile={output_path}",
            str(input_path),
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Ghostscript failed: {result.stderr}")
        
        compressed_size = output_path.stat().st_size
        
        return CompressionResult(
            success=True,
            input_path=input_path,
            output_path=output_path,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compressed_size / original_size if original_size > 0 else 0,
            status=CompressionStatus.COMPLETED,
            quality_level=quality,
            mode_used=CompressionMode.GHOSTSCRIPT,
        )
    
    def _compress_with_pypdf(
        self,
        input_path: Path,
        output_path: Path,
        quality: QualityLevel,
        original_size: int,
    ) -> CompressionResult:
        """Compress using PyPDF (fallback method)"""
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            raise RuntimeError("PyPDF2/pypdf not installed")
        
        reader = PdfReader(str(input_path))
        writer = PdfWriter()
        
        # Copy pages with compression
        for page in reader.pages:
            writer.add_page(page)
        
        # Apply compression settings based on quality
        compression_map = {
            QualityLevel.PREPRESS: {"stream_data": True, "images": True},
            QualityLevel.PRINTER: {"stream_data": True, "images": True},
            QualityLevel.EBOOK: {"stream_data": True, "images": True},
            QualityLevel.SCREEN: {"stream_data": True, "images": True},
        }
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        compressed_size = output_path.stat().st_size
        
        return CompressionResult(
            success=True,
            input_path=input_path,
            output_path=output_path,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compressed_size / original_size if original_size > 0 else 0,
            status=CompressionStatus.COMPLETED,
            quality_level=quality,
            mode_used=CompressionMode.PYPDF,
        )
    
    def compress(
        self,
        input_path: Path | str,
        output_path: Path | str | None = None,
        quality: QualityLevel = QualityLevel.PRINTER,
        mode: CompressionMode = CompressionMode.AUTO,
    ) -> CompressionResult:
        """Synchronous compression wrapper"""
        return asyncio.run(self.compress_async(input_path, output_path, quality, mode))
    
    async def compress_batch_async(
        self,
        files: list[Path | str],
        output_dir: Path | str | None = None,
        quality: QualityLevel = QualityLevel.PRINTER,
        mode: CompressionMode = CompressionMode.AUTO,
        max_concurrent: int = 3,
    ) -> list[CompressionResult]:
        """Compress multiple files concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def compress_with_semaphore(file: Path) -> CompressionResult:
            async with semaphore:
                return await self.compress_async(file, quality=quality, mode=mode)
        
        tasks = [compress_with_semaphore(Path(f)) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results: list[CompressionResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(CompressionResult(
                    success=False,
                    input_path=Path(files[i]),
                    output_path=Path(),
                    original_size=0,
                    compressed_size=0,
                    compression_ratio=0.0,
                    status=CompressionStatus.FAILED,
                    error_message=str(result),
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_quality_info(self, quality: QualityLevel) -> dict[str, str | float]:
        """Get detailed information about a quality level"""
        info = QUALITY_INFO.get(quality)
        if not info:
            return {}
        
        return {
            "level": info.level.value,
            "description": info.description,
            "estimated_ratio": info.estimated_ratio,
            "recommended_for": info.recommended_for,
        }
