#!/usr/bin/env python3
"""
Folder to EPUB Converter (CLI & Public Engine API)
=================================================
A Clean Architecture tool to convert image directories or chapter subfolders
into clean, responsive EPUB eBooks optimized for e-readers.

Provides full backward compatibility for CLI commands and external imports.
"""

from core.constants import SUPPORTED_EXTENSIONS, DEFAULT_CSS, APP_TITLE, APP_VERSION
from core.exceptions import (
    FolderToEpubError,
    InvalidSourceError,
    NoImagesFoundError,
    InvalidImageError,
    EpubGenerationError
)
from core.models import ImagePage, ChapterData, BookData, ConversionConfig
from services.scanner import (
    ScannerService,
    collect_chapters_and_images,
    find_root_cover,
    detect_books,
    is_hidden_or_system_file
)
from services.builder import EpubBuilder, create_epub
from services.converter import ConversionService, create_epub_batch
from cli.main import main

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "DEFAULT_CSS",
    "APP_TITLE",
    "APP_VERSION",
    "FolderToEpubError",
    "InvalidSourceError",
    "NoImagesFoundError",
    "InvalidImageError",
    "EpubGenerationError",
    "ImagePage",
    "ChapterData",
    "BookData",
    "ConversionConfig",
    "ScannerService",
    "collect_chapters_and_images",
    "find_root_cover",
    "detect_books",
    "is_hidden_or_system_file",
    "EpubBuilder",
    "create_epub",
    "ConversionService",
    "create_epub_batch",
    "main",
]

if __name__ == "__main__":
    main()
