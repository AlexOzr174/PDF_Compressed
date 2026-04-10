"""
Comprehensive test suite for PDF Compressor
Tests all modules with Python 3.14+ features
"""

import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test results tracking
test_results: list[tuple[str, bool, str]] = []


def test(name: str):
    """Decorator to track test results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                test_results.append((name, True, "PASS"))
                print(f"✓ {name}")
                return True
            except AssertionError as e:
                test_results.append((name, False, f"FAIL: {e}"))
                print(f"✗ {name}: {e}")
                return False
            except Exception as e:
                test_results.append((name, False, f"ERROR: {e}"))
                print(f"✗ {name}: {e}")
                return False
        return wrapper
    return decorator


def create_test_pdf(path: Path, pages: int = 1) -> None:
    """Create a minimal valid PDF file for testing"""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n193\n%%EOF"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(pdf_content)


# ============================================
# CONFIG TESTS
# ============================================

@test("Config: QualityLevel enum values")
def test_quality_level_enum():
    from pdfcompressor.core.config import QualityLevel
    
    assert QualityLevel.PREPRESS.value == "prepress"
    assert QualityLevel.PRINTER.value == "printer"
    assert QualityLevel.EBOOK.value == "ebook"
    assert QualityLevel.SCREEN.value == "screen"


@test("Config: CompressionMode enum values")
def test_compression_mode_enum():
    from pdfcompressor.core.config import CompressionMode
    
    assert CompressionMode.GHOSTSCRIPT.value == "ghostscript"
    assert CompressionMode.PYPDF.value == "pypdf"
    assert CompressionMode.AUTO.value == "auto"


@test("Config: AppSettings default values")
def test_app_settings_defaults():
    from pdfcompressor.core.config import AppSettings, QualityLevel, CompressionMode
    
    settings = AppSettings()
    assert settings.default_quality == QualityLevel.PRINTER
    assert settings.default_mode == CompressionMode.AUTO
    assert settings.output_suffix == "_compressed"
    assert settings.create_backup is True
    assert settings.max_file_size_mb == 100


@test("Config: AppSettings serialization to dict")
def test_app_settings_to_dict():
    from pdfcompressor.core.config import AppSettings
    
    settings = AppSettings(theme="dark", language="en")
    data = settings.to_dict()
    
    assert data["theme"] == "dark"
    assert data["language"] == "en"
    assert "default_quality" in data


@test("Config: AppSettings JSON round-trip")
def test_app_settings_json_roundtrip():
    from pdfcompressor.core.config import AppSettings, QualityLevel
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "settings.json"
        
        # Save
        original = AppSettings(theme="light", max_file_size_mb=50)
        original.save_json(config_path)
        
        # Load
        loaded = AppSettings.load_json(config_path)
        
        assert loaded.theme == "light"
        assert loaded.max_file_size_mb == 50


# ============================================
# VALIDATOR TESTS
# ============================================

@test("Validator: Empty path detection")
def test_validator_empty_path():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    validator = PDFValidator()
    result = validator.validate_path("")
    
    assert result.is_valid is False
    assert result.error_code == ValidationErrorCode.EMPTY_PATH


@test("Validator: File not found detection")
def test_validator_file_not_found():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    validator = PDFValidator()
    result = validator.validate_file_exists("/nonexistent/file.pdf")
    
    assert result.is_valid is False
    assert result.error_code == ValidationErrorCode.FILE_NOT_FOUND


@test("Validator: Wrong extension detection")
def test_validator_wrong_extension():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        tmpfile = f.name
    
    try:
        validator = PDFValidator()
        result = validator.validate_extension(tmpfile)
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.WRONG_EXTENSION
    finally:
        os.unlink(tmpfile)


@test("Validator: Empty file detection")
def test_validator_empty_file():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmpfile = f.name
    
    try:
        validator = PDFValidator()
        result = validator.validate_file_size(tmpfile)
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.EMPTY_FILE
    finally:
        os.unlink(tmpfile)


@test("Validator: Valid PDF passes all checks")
def test_validator_valid_pdf():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        output_path = Path(tmpdir) / "output.pdf"
        create_test_pdf(pdf_path)
        
        validator = PDFValidator()
        result = validator.validate_full(str(pdf_path), str(output_path))
        
        assert result.is_valid is True
        assert result.error_code == ValidationErrorCode.SUCCESS


@test("Validator: Same input/output paths rejected")
def test_validator_same_paths():
    from pdfcompressor.core.validator import PDFValidator, ValidationErrorCode
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        create_test_pdf(pdf_path)
        
        validator = PDFValidator()
        result = validator.validate_output_path(str(pdf_path), str(pdf_path))
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.SAME_PATHS


# ============================================
# COMPRESSOR TESTS
# ============================================

@test("Compressor: Initialization")
def test_compressor_init():
    from pdfcompressor.core.compressor import PDFCompressor
    from pdfcompressor.core.config import AppSettings
    
    settings = AppSettings()
    compressor = PDFCompressor(settings)
    
    assert compressor.settings == settings
    assert compressor.validator is not None


@test("Compressor: Ghostscript availability check")
def test_compressor_ghostscript_check():
    from pdfcompressor.core.compressor import PDFCompressor
    
    compressor = PDFCompressor()
    # Just check the property exists and returns a boolean
    result = compressor.ghostscript_available
    assert isinstance(result, bool)


@test("Compressor: Quality info retrieval")
def test_compressor_quality_info():
    from pdfcompressor.core.compressor import PDFCompressor
    from pdfcompressor.core.config import QualityLevel
    
    compressor = PDFCompressor()
    info = compressor.get_quality_info(QualityLevel.PRINTER)
    
    assert "level" in info
    assert "description" in info
    assert info["level"] == "printer"


@test("Compressor: Async compression with invalid file")
def test_compressor_async_invalid_file():
    from pdfcompressor.core.compressor import PDFCompressor, CompressionStatus
    
    async def run_test():
        compressor = PDFCompressor()
        result = await compressor.compress_async(
            input_path="/nonexistent/file.pdf",
        )
        return result
    
    result = asyncio.run(run_test())
    
    # Should fail gracefully with validation error, not exception
    assert result.success is False
    assert result.status in [CompressionStatus.FAILED, CompressionStatus.PENDING]


@test("Compressor: Sync compression wrapper")
def test_compressor_sync_wrapper():
    from pdfcompressor.core.compressor import PDFCompressor, CompressionStatus
    
    compressor = PDFCompressor()
    result = compressor.compress(input_path="/nonexistent/file.pdf")
    
    # Should fail gracefully with validation error, not exception
    assert result.success is False
    assert result.status in [CompressionStatus.FAILED, CompressionStatus.PENDING]


# ============================================
# LOGGER TESTS
# ============================================

@test("Logger: Setup creates logger")
def test_logger_setup():
    from pdfcompressor.utils.logger import setup_logger
    import logging
    
    logger = setup_logger("test_logger", console_output=False, file_output=False)
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


@test("Logger: Get existing logger")
def test_logger_get():
    from pdfcompressor.utils.logger import get_logger, setup_logger
    import logging
    
    # Create first
    setup_logger("test_get", console_output=False, file_output=False)
    
    # Get existing
    logger = get_logger("test_get")
    assert isinstance(logger, logging.Logger)


# ============================================
# UI COMPONENT TESTS (without display)
# ============================================

@test("UI Components: ThemeManager initialization")
def test_theme_manager_init():
    from pdfcompressor.ui.components import ThemeManager
    
    tm = ThemeManager("dark")
    assert tm.current_theme == "dark"
    assert "dark" in tm.available_themes


@test("UI Components: ThemeManager theme switching")
def test_theme_manager_switch():
    from pdfcompressor.ui.components import ThemeManager
    
    tm = ThemeManager("dark")
    tm.set_theme("light")
    
    assert tm.current_theme == "light"
    assert tm.current_config["name"] == "Light"


@test("UI Components: ViewModel reset")
def test_viewmodel_reset():
    from pdfcompressor.ui.main_window import ViewModel
    from pdfcompressor.core.config import QualityLevel, CompressionMode
    
    vm = ViewModel(
        input_path="/test.pdf",
        is_processing=True,
        progress_value=50,
    )
    vm.reset()
    
    assert vm.input_path == ""
    assert vm.is_processing is False
    assert vm.progress_value == 0


# ============================================
# INTEGRATION TESTS
# ============================================

@test("Integration: Full validation flow")
def test_integration_validation():
    from pdfcompressor.core.config import AppSettings
    from pdfcompressor.core.validator import PDFValidator
    from pdfcompressor.core.compressor import PDFCompressor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        output_path = Path(tmpdir) / "output.pdf"
        create_test_pdf(pdf_path)
        
        settings = AppSettings()
        validator = PDFValidator(settings)
        compressor = PDFCompressor(settings)
        
        # Validate
        validation = validator.validate_full(str(pdf_path), str(output_path))
        assert validation.is_valid
        
        # Check compressor can access the file
        assert compressor.validator is not None


# ============================================
# MAIN TEST RUNNER
# ============================================

def run_all_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("PDF Compressor - Test Suite")
    print("=" * 60)
    print()
    
    # Run all test functions
    test_functions = [
        # Config tests
        test_quality_level_enum,
        test_compression_mode_enum,
        test_app_settings_defaults,
        test_app_settings_to_dict,
        test_app_settings_json_roundtrip,
        
        # Validator tests
        test_validator_empty_path,
        test_validator_file_not_found,
        test_validator_wrong_extension,
        test_validator_empty_file,
        test_validator_valid_pdf,
        test_validator_same_paths,
        
        # Compressor tests
        test_compressor_init,
        test_compressor_ghostscript_check,
        test_compressor_quality_info,
        test_compressor_async_invalid_file,
        test_compressor_sync_wrapper,
        
        # Logger tests
        test_logger_setup,
        test_logger_get,
        
        # UI tests
        test_theme_manager_init,
        test_theme_manager_switch,
        test_viewmodel_reset,
        
        # Integration tests
        test_integration_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_functions)} tests")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
