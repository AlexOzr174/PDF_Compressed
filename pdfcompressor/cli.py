"""
PDF Compressor CLI - Command Line Interface
Modern Python 3.14+ with argparse and async support
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Self

from pdfcompressor.core.config import (
    QualityLevel,
    CompressionMode,
    AppSettings,
    QUALITY_LEVELS,
)
from pdfcompressor.core.compressor import PDFCompressor, CompressionResult, CompressionStatus
from pdfcompressor.core.validator import PDFValidator, ValidationResult
from pdfcompressor.utils.logger import setup_logger, get_logger


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all CLI options"""
    parser = argparse.ArgumentParser(
        prog="pdfcompressor",
        description="📄 PDF Compressor Pro - Compress PDF files with Ghostscript or PyPDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pdf                          # Compress with default settings
  %(prog)s input.pdf -o output.pdf            # Specify output file
  %(prog)s input.pdf -q screen                # Maximum compression
  %(prog)s *.pdf -q ebook                     # Batch compress multiple files
  %(prog)s input.pdf --mode pypdf             # Use PyPDF instead of Ghostscript

Quality Levels:
  prepress  - Highest quality, minimal compression (~30%% reduction)
  printer   - High quality for office printers (~50%% reduction)
  ebook     - Medium quality for screens (~70%% reduction)
  screen    - Lowest quality, maximum compression (~85%% reduction)
""",
    )
    
    # Positional arguments
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input PDF file(s) to compress",
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path (for single file mode)",
    )
    
    parser.add_argument(
        "-d", "--output-dir",
        type=Path,
        help="Output directory for batch processing",
    )
    
    # Compression settings
    parser.add_argument(
        "-q", "--quality",
        type=str,
        choices=[q.value for q in QUALITY_LEVELS],
        default="printer",
        help="Compression quality level (default: printer)",
    )
    
    parser.add_argument(
        "-m", "--mode",
        type=str,
        choices=[m.value for m in CompressionMode],
        default="auto",
        help="Compression engine (default: auto)",
    )
    
    # General options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually compressing",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (JSON/YAML)",
    )
    
    return parser


async def compress_file_async(
    compressor: PDFCompressor,
    input_path: Path,
    output_path: Path | None,
    quality: QualityLevel,
    mode: CompressionMode,
    dry_run: bool = False,
) -> CompressionResult:
    """Compress a single file asynchronously"""
    if dry_run:
        print(f"  [DRY RUN] Would compress: {input_path}")
        if output_path:
            print(f"            Output: {output_path}")
        print(f"            Quality: {quality.value}, Mode: {mode.value}")
        
        # Return a fake success result for dry run
        return CompressionResult(
            success=True,
            input_path=input_path,
            output_path=output_path or Path(),
            original_size=input_path.stat().st_size if input_path.exists() else 0,
            compressed_size=0,
            compression_ratio=0.0,
            status=CompressionStatus.COMPLETED,
        )
    
    return await compressor.compress_async(
        input_path=input_path,
        output_path=output_path,
        quality=quality,
        mode=mode,
    )


async def run_batch_async(
    compressor: PDFCompressor,
    files: list[Path],
    output_dir: Path | None,
    quality: QualityLevel,
    mode: CompressionMode,
    dry_run: bool = False,
) -> list[CompressionResult]:
    """Compress multiple files concurrently"""
    results = []
    
    for input_path in files:
        if output_dir and output_dir.exists():
            output_path = output_dir / f"{input_path.stem}_compressed.pdf"
        else:
            output_path = None
        
        result = await compress_file_async(
            compressor,
            input_path,
            output_path,
            quality,
            mode,
            dry_run,
        )
        results.append(result)
    
    return results


def print_result(result: CompressionResult, verbose: bool = False) -> None:
    """Print compression result"""
    if result.success:
        savings = result.savings_percent
        print(f"✓ {result.input_path.name}")
        if verbose:
            print(f"  Original:   {result.original_size_mb:.2f} MB")
            print(f"  Compressed: {result.compressed_size_mb:.2f} MB")
            print(f"  Saved:      {savings:.1f}%")
            print(f"  Mode:       {result.mode_used.value}")
            print(f"  Duration:   {result.duration_ms}ms")
    else:
        print(f"✗ {result.input_path.name}: {result.error_message}")


def load_config(config_path: Path | None) -> AppSettings:
    """Load configuration from file or use defaults"""
    if config_path and config_path.exists():
        if config_path.suffix in [".yaml", ".yml"]:
            return AppSettings.load_yaml(config_path)
        else:
            return AppSettings.load_json(config_path)
    return AppSettings()


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Setup logger
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger("pdfcompressor.cli", level=getattr(__import__("logging"), log_level))
    
    # Load configuration
    settings = load_config(args.config)
    
    # Initialize components
    validator = PDFValidator(settings)
    compressor = PDFCompressor(settings)
    
    # Parse quality and mode
    quality = QualityLevel(args.quality)
    mode = CompressionMode(args.mode)
    
    # Validate inputs
    print(f"PDF Compressor Pro v2.0")
    print(f"Ghostscript: {'✓ ' + (compressor.ghostscript_version or 'available') if compressor.ghostscript_available else '⚠ not found (using PyPDF)'}")
    print()
    
    # Dry run info
    if args.dry_run:
        print("[DRY RUN MODE - No files will be modified]")
        print()
    
    # Process files
    async def process():
        if len(args.input) == 1 and args.output:
            # Single file mode
            input_path = args.input[0]
            
            # Validate
            validation = validator.validate_full(str(input_path), str(args.output))
            if not validation:
                print(f"Error: {validation.error_message}")
                return 1
            
            result = await compress_file_async(
                compressor,
                input_path,
                args.output,
                quality,
                mode,
                args.dry_run,
            )
            print_result(result, args.verbose)
            return 0 if result.success else 1
        
        else:
            # Batch mode
            print(f"Processing {len(args.input)} file(s)...\n")
            
            # Validate all files first
            valid_files = []
            for input_path in args.input:
                validation = validator.validate_full(str(input_path))
                if validation:
                    valid_files.append(input_path)
                else:
                    print(f"⚠ Skipping {input_path.name}: {validation.error_message}")
            
            if not valid_files:
                print("\nNo valid files to process")
                return 1
            
            results = await run_batch_async(
                compressor,
                valid_files,
                args.output_dir,
                quality,
                mode,
                args.dry_run,
            )
            
            # Print results
            print("\nResults:")
            print("-" * 50)
            for result in results:
                print_result(result, args.verbose)
            
            # Summary
            successful = sum(1 for r in results if r.success)
            total = len(results)
            print("-" * 50)
            print(f"Total: {successful}/{total} successful")
            
            if successful > 0 and not args.dry_run:
                total_original = sum(r.original_size_mb for r in results if r.success)
                total_compressed = sum(r.compressed_size_mb for r in results if r.success)
                total_savings = (1 - total_compressed / total_original) * 100 if total_original > 0 else 0
                print(f"\nSpace saved: {total_original - total_compressed:.2f} MB ({total_savings:.1f}%)")
            
            return 0 if successful == total else 1
    
    return asyncio.run(process())


if __name__ == "__main__":
    sys.exit(main())
