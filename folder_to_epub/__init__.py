"""
Folder to EPUB Converter
========================
A clean, modular Python tool for converting directories of images and comic archives into EPUB 3 eBooks.
"""

from folder_to_epub.core.constants import (
    APP_NAME,
    APP_TITLE,
    APP_VERSION,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_ARCHIVE_EXTENSIONS,
    DEFAULT_CSS,
)
from folder_to_epub.core.exceptions import (
    FolderToEpubError,
    InvalidSourceError,
    NoImagesFoundError,
    InvalidImageError,
    EpubGenerationError,
)
from folder_to_epub.core.models import Book, Chapter, ImagePage, ConversionConfig, ProgressEvent
from folder_to_epub.services.archive import ArchiveService
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.builder import EpubBuilder
from folder_to_epub.services.converter import ConversionService

__all__ = [
    "APP_NAME",
    "APP_TITLE",
    "APP_VERSION",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_ARCHIVE_EXTENSIONS",
    "DEFAULT_CSS",
    "FolderToEpubError",
    "InvalidSourceError",
    "NoImagesFoundError",
    "InvalidImageError",
    "EpubGenerationError",
    "Book",
    "Chapter",
    "ImagePage",
    "ConversionConfig",
    "ProgressEvent",
    "ArchiveService",
    "ScannerService",
    "EpubBuilder",
    "ConversionService",
]
