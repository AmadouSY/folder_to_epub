"""Services layer providing scanning, EPUB building, and batch conversion."""
from services.scanner import (
    ScannerService,
    collect_chapters_and_images,
    find_root_cover,
    detect_books,
    is_hidden_or_system_file,
)
from services.builder import EpubBuilder, create_epub
from services.converter import ConversionService, create_epub_batch

__all__ = [
    "ScannerService",
    "collect_chapters_and_images",
    "find_root_cover",
    "detect_books",
    "is_hidden_or_system_file",
    "EpubBuilder",
    "create_epub",
    "ConversionService",
    "create_epub_batch",
]
