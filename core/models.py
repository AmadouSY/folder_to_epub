"""Domain entities and value objects for folder_to_epub."""

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from PIL import Image


class ImagePage:
    """Represents a single image page with its dimensions, MIME type, and validity."""

    def __init__(self, file_path: Path, chapter_title: str, page_index: int):
        self.file_path: Path = Path(file_path)
        self.chapter_title: str = chapter_title
        self.page_index: int = page_index
        self.width: int = 0
        self.height: int = 0
        self.mime_type: str = "image/jpeg"
        self.is_valid: bool = False
        self._inspect_image()

    def _inspect_image(self) -> None:
        """Validates the image file with Pillow and extracts dimensions and MIME type."""
        ext = self.file_path.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            self.mime_type = 'image/jpeg'
        elif ext == '.png':
            self.mime_type = 'image/png'
        elif ext == '.webp':
            self.mime_type = 'image/webp'
        elif ext == '.gif':
            self.mime_type = 'image/gif'
        elif ext == '.bmp':
            self.mime_type = 'image/bmp'
        else:
            self.mime_type = mimetypes.guess_type(self.file_path)[0] or 'image/jpeg'

        try:
            with Image.open(self.file_path) as img:
                img.verify()
            with Image.open(self.file_path) as img:
                self.width, self.height = img.size
                self.is_valid = True
        except Exception:
            self.is_valid = False

    def __repr__(self) -> str:
        return f"<ImagePage {self.file_path.name} ({self.width}x{self.height}, valid={self.is_valid})>"


class ChapterData:
    """Represents a book chapter containing an ordered list of image pages."""

    def __init__(self, title: str, folder_path: Optional[Path] = None):
        self.title: str = title
        self.folder_path: Optional[Path] = Path(folder_path) if folder_path else None
        self.pages: List[ImagePage] = []

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def __repr__(self) -> str:
        return f"<ChapterData '{self.title}' ({self.page_count} pages)>"


class BookData:
    """Represents a complete book with its chapters, cover, and page statistics."""

    def __init__(
        self,
        title: str,
        folder_path: Path,
        chapters: List[ChapterData],
        cover_path: Optional[Path] = None
    ):
        self.title: str = title
        self.folder_path: Path = Path(folder_path)
        self.chapters: List[ChapterData] = chapters
        self.cover_path: Optional[Path] = Path(cover_path) if cover_path else None
        self.total_images: int = sum(len(c.pages) for c in chapters)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    def __repr__(self) -> str:
        return f"<BookData '{self.title}' ({self.chapter_count} chapters, {self.total_images} pages)>"


@dataclass
class ConversionConfig:
    """Configuration options for building an EPUB eBook."""
    title: str
    author: str = "Unknown"
    language: str = "en"
    output_path: Optional[Path] = None
    custom_cover_path: Optional[Path] = None
    source_dir: Optional[Path] = None
    is_manga: bool = False
    is_rtl: bool = False
