"""Directory scanning and structure inspection service."""

from pathlib import Path
from typing import List, Optional, Tuple
from natsort import natsorted

from folder_to_epub.core.constants import SUPPORTED_EXTENSIONS
from folder_to_epub.core.exceptions import InvalidSourceError
from folder_to_epub.core.models import Book, Chapter, ImagePage


class ScannerService:
    """Discovers books, chapters, and image files using natural alphanumeric sorting."""

    @staticmethod
    def is_hidden_or_system_file(path: Path) -> bool:
        """Determines if a path is hidden or an operating system metadata file."""
        name = path.name
        if name.startswith('.') or name.startswith('~$'):
            return True
        if name.lower() in ('thumbs.db', 'desktop.ini', 'ehthumbs.db'):
            return True
        return False

    @classmethod
    def scan_chapters(cls, source_dir: Path) -> List[Chapter]:
        """
        Scans source_dir and returns naturally sorted chapters and their images.
        Supports both:
        1. Multi-chapter structure (subdirectories = chapters)
        2. Flat single-chapter structure (images directly at root)
        """
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise InvalidSourceError(f"Source directory '{source_dir}' does not exist.")
        if not source_dir.is_dir():
            raise InvalidSourceError(f"Source path '{source_dir}' is not a directory.")

        chapters: List[Chapter] = []
        children = [p for p in source_dir.iterdir() if not cls.is_hidden_or_system_file(p)]
        subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
        direct_images = natsorted(
            [p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS],
            key=lambda p: p.name
        )

        if subdirs:
            for subdir in subdirs:
                chapter = Chapter(title=subdir.name, folder_path=subdir)
                image_files = natsorted(
                    [
                        p for p in subdir.iterdir()
                        if p.is_file() and not cls.is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS
                    ],
                    key=lambda p: p.name
                )
                for idx, img_path in enumerate(image_files, start=1):
                    page = ImagePage.from_file(img_path, chapter_title=subdir.name, page_index=idx)
                    if page:
                        chapter.pages.append(page)

                if chapter.pages:
                    chapters.append(chapter)

        elif direct_images:
            chapter = Chapter(title=source_dir.name, folder_path=source_dir)
            for idx, img_path in enumerate(direct_images, start=1):
                page = ImagePage.from_file(img_path, chapter_title=source_dir.name, page_index=idx)
                if page:
                    chapter.pages.append(page)
            if chapter.pages:
                chapters.append(chapter)

        return chapters

    @classmethod
    def find_cover(cls, source_dir: Path) -> Optional[Path]:
        """
        Locates an image file in the root of source_dir containing 'cover' or 'couverture'.
        Returns the naturally first candidate path, or None.
        """
        if not source_dir:
            return None
        source_dir = Path(source_dir)
        if not source_dir.exists() or not source_dir.is_dir():
            return None

        candidates = []
        for p in source_dir.iterdir():
            if p.is_file() and not cls.is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                stem_lower = p.stem.lower()
                if 'cover' in stem_lower or 'couverture' in stem_lower:
                    candidates.append(p)

        if candidates:
            return natsorted(candidates, key=lambda p: p.name)[0]
        return None

    @classmethod
    def scan_book(cls, book_dir: Path) -> Optional[Book]:
        """Constructs a Book domain model from a directory, or returns None if empty."""
        book_dir = Path(book_dir)
        try:
            chapters = cls.scan_chapters(book_dir)
            if not chapters or sum(c.page_count for c in chapters) == 0:
                return None
            cover = cls.find_cover(book_dir)
            return Book(title=book_dir.name, folder_path=book_dir, chapters=chapters, cover_path=cover)
        except Exception:
            return None

    @classmethod
    def detect_books(cls, source_dir: Path, force_batch: Optional[bool] = None) -> Tuple[bool, List[Book]]:
        """
        Analyzes a directory to determine if it represents a single book or a batch collection.
        Returns:
            Tuple of (is_batch_mode: bool, list_of_Book).
        """
        if not source_dir:
            return False, []
        source_dir = Path(source_dir)
        if not source_dir.exists() or not source_dir.is_dir():
            return False, []

        children = [p for p in source_dir.iterdir() if not cls.is_hidden_or_system_file(p)]
        subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
        direct_images = [p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]

        is_batch = False
        if force_batch is True:
            is_batch = True
        elif force_batch is False:
            is_batch = False
        else:
            # Auto-detect batch mode if subdirectories have nested folders or their own covers
            if subdirs and not direct_images:
                has_nested_subdirs = False
                covers_count = 0
                for sd in subdirs:
                    sd_children = [p for p in sd.iterdir() if not cls.is_hidden_or_system_file(p)]
                    if any(p.is_dir() for p in sd_children):
                        has_nested_subdirs = True
                    if cls.find_cover(sd):
                        covers_count += 1
                if has_nested_subdirs or covers_count >= 2:
                    is_batch = True

        if is_batch and subdirs:
            books: List[Book] = []
            for sd in subdirs:
                b = cls.scan_book(sd)
                if b:
                    books.append(b)
            if books:
                return True, books

        # Fallback to single book
        single = cls.scan_book(source_dir)
        return False, [single] if single else []
