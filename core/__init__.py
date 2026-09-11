"""Core domain module for folder_to_epub."""
from core.constants import SUPPORTED_EXTENSIONS, DEFAULT_CSS, APP_TITLE, APP_VERSION
from core.exceptions import (
    FolderToEpubError,
    InvalidSourceError,
    NoImagesFoundError,
    InvalidImageError,
    EpubGenerationError,
)
from core.models import ImagePage, ChapterData, BookData, ConversionConfig

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
]
