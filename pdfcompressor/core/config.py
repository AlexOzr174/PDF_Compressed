"""
Configuration module with Python 3.14+ type hints and PEP 695 generics
"""

from enum import StrEnum, auto
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict, TypeAlias
import json
import yaml


# PEP 695: New type alias syntax (Python 3.12+)
QualityMap: TypeAlias = dict[str, float]


class QualityLevel(StrEnum):
    """PDF compression quality levels matching Ghostscript presets"""
    PREPRESS = "prepress"
    PRINTER = "printer"
    EBOOK = "ebook"
    SCREEN = "screen"
    DEFAULT = "default"


class CompressionMode(StrEnum):
    """Compression engine modes"""
    GHOSTSCRIPT = "ghostscript"
    PYPDF = "pypdf"
    AUTO = "auto"


# Estimated size reduction ratios by quality level
ESTIMATED_SIZE_RATIOS: QualityMap = {
    QualityLevel.PREPRESS: 0.7,
    QualityLevel.PRINTER: 0.5,
    QualityLevel.EBOOK: 0.3,
    QualityLevel.SCREEN: 0.15,
    QualityLevel.DEFAULT: 0.5,
}

QUALITY_LEVELS: list[QualityLevel] = [
    QualityLevel.PREPRESS,
    QualityLevel.PRINTER,
    QualityLevel.EBOOK,
    QualityLevel.SCREEN,
]


@dataclass(slots=True, frozen=True)
class QualityInfo:
    """Information about a quality level"""
    level: QualityLevel
    description: str
    estimated_ratio: float
    recommended_for: str


QUALITY_INFO: dict[QualityLevel, QualityInfo] = {
    QualityLevel.PREPRESS: QualityInfo(
        level=QualityLevel.PREPRESS,
        description="Highest quality, minimal compression",
        estimated_ratio=0.7,
        recommended_for="Professional printing, archives"
    ),
    QualityLevel.PRINTER: QualityInfo(
        level=QualityLevel.PRINTER,
        description="High quality for office printers",
        estimated_ratio=0.5,
        recommended_for="Office documents, presentations"
    ),
    QualityLevel.EBOOK: QualityInfo(
        level=QualityLevel.EBOOK,
        description="Medium quality for screens",
        estimated_ratio=0.3,
        recommended_for="E-books, web distribution"
    ),
    QualityLevel.SCREEN: QualityInfo(
        level=QualityLevel.SCREEN,
        description="Lowest quality, maximum compression",
        estimated_ratio=0.15,
        recommended_for="Email attachments, quick sharing"
    ),
}


class SettingsDict(TypedDict, total=False):
    """Typed dictionary for settings serialization"""
    default_quality: str
    default_mode: str
    output_suffix: str
    create_backup: bool
    max_file_size_mb: int
    supported_extensions: list[str]
    ghostscript_paths: dict[str, str]
    theme: str
    language: str


@dataclass(slots=True)
class AppSettings:
    """Application configuration with support for JSON/YAML"""
    default_quality: QualityLevel = QualityLevel.PRINTER
    default_mode: CompressionMode = CompressionMode.AUTO
    output_suffix: str = "_compressed"
    create_backup: bool = True
    max_file_size_mb: int = 100
    supported_extensions: list[str] = field(default_factory=lambda: [".pdf"])
    ghostscript_paths: dict[str, str] = field(default_factory=lambda: {
        "linux": "/usr/bin/gs",
        "darwin": "/usr/local/bin/gs",
        "win32": r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
    })
    theme: str = "dark"
    language: str = "en"
    
    # PEP 695: Generic methods will use new syntax when available
    def to_dict(self) -> SettingsDict:
        """Convert settings to dictionary for serialization"""
        return SettingsDict(
            default_quality=self.default_quality.value,
            default_mode=self.default_mode.value,
            output_suffix=self.output_suffix,
            create_backup=self.create_backup,
            max_file_size_mb=self.max_file_size_mb,
            supported_extensions=self.supported_extensions,
            ghostscript_paths=self.ghostscript_paths,
            theme=self.theme,
            language=self.language,
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """Create settings from dictionary"""
        return cls(
            default_quality=QualityLevel(data.get("default_quality", "printer")),
            default_mode=CompressionMode(data.get("default_mode", "auto")),
            output_suffix=data.get("output_suffix", "_compressed"),
            create_backup=data.get("create_backup", True),
            max_file_size_mb=data.get("max_file_size_mb", 100),
            supported_extensions=data.get("supported_extensions", [".pdf"]),
            ghostscript_paths=data.get("ghostscript_paths", cls.__dataclass_fields__["ghostscript_paths"].default_factory()),
            theme=data.get("theme", "dark"),
            language=data.get("language", "en"),
        )
    
    def save_json(self, path: Path | str) -> None:
        """Save settings to JSON file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_json(cls, path: Path | str) -> "AppSettings":
        """Load settings from JSON file"""
        path = Path(path)
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save_yaml(self, path: Path | str) -> None:
        """Save settings to YAML file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def load_yaml(cls, path: Path | str) -> "AppSettings":
        """Load settings from YAML file"""
        path = Path(path)
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data or {})
