"""Domain models and value objects."""

from dataclasses import dataclass, field
import mimetypes
from pathlib import Path
from typing import List, Optional
from PIL import Image


@dataclass
class ImagePage:
    """Represents a single image page with its dimensions, MIME type, and metadata."""
    file_path: Path
    chapter_title: str
    page_index: int
    width: int
    height: int
    mime_type: str = "image/jpeg"
    is_valid: bool = True

    @classmethod
    def from_file(cls, file_path: Path, chapter_title: str, page_index: int) -> Optional['ImagePage']:
        """
        Factory method validating the image file with Pillow and extracting dimensions.
        Returns an ImagePage if valid, or None if corrupted/unsupported.
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            mime = 'image/jpeg'
        elif ext == '.png':
            mime = 'image/png'
        elif ext == '.webp':
            mime = 'image/webp'
        elif ext == '.gif':
            mime = 'image/gif'
        elif ext == '.bmp':
            mime = 'image/bmp'
        else:
            mime = mimetypes.guess_type(file_path)[0] or 'image/jpeg'

        try:
            with Image.open(file_path) as img:
                img.verify()
            with Image.open(file_path) as img:
                width, height = img.size
            return cls(
                file_path=file_path,
                chapter_title=chapter_title,
                page_index=page_index,
                width=width,
                height=height,
                mime_type=mime,
                is_valid=True
            )
        except Exception:
            return None


@dataclass
class Chapter:
    """Represents an ordered chapter containing image pages."""
    title: str
    folder_path: Optional[Path] = None
    pages: List[ImagePage] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)


@dataclass
class Book:
    """Represents an entire book composed of chapters and an optional cover image."""
    title: str
    folder_path: Path
    chapters: List[Chapter] = field(default_factory=list)
    cover_path: Optional[Path] = None
    archive_path: Optional[Path] = None
    archive_page_count: int = 0

    @property
    def is_archive(self) -> bool:
        return self.archive_path is not None

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def total_images(self) -> int:
        if self.chapters and any(c.page_count > 0 for c in self.chapters):
            return sum(c.page_count for c in self.chapters)
        return self.archive_page_count


@dataclass
class ConversionConfig:
    """Configuration options for EPUB generation."""
    title: str
    author: str = "Unknown"
    language: str = "en"
    output_path: Optional[Path] = None
    custom_cover_path: Optional[Path] = None
    source_dir: Optional[Path] = None
    is_manga: bool = False
    is_rtl: bool = False


@dataclass
class ProgressEvent:
    """Event data emitted during conversion steps."""
    current_step: int
    total_steps: int
    current_label: str
    current_book_index: int = 1
    total_books: int = 1
    book_title: str = ""
