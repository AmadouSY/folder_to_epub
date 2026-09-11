"""Scanner service for inspecting directories, chapters, covers, and books."""

from pathlib import Path
from typing import List, Optional, Tuple
from natsort import natsorted

from core.constants import SUPPORTED_EXTENSIONS
from core.models import ChapterData, ImagePage, BookData
from core.exceptions import InvalidSourceError


def is_hidden_or_system_file(path: Path) -> bool:
    """Checks whether a file or directory is hidden or an OS system artifact."""
    name = path.name
    if name.startswith('.') or name.startswith('~$'):
        return True
    if name.lower() in ('thumbs.db', 'desktop.ini', 'ehthumbs.db'):
        return True
    return False


class ScannerService:
    """Encapsulates directory discovery, natural sorting, and structure analysis."""

    @staticmethod
    def collect_chapters_and_images(source_dir: Path) -> List[ChapterData]:
        """
        Scans source_dir and extracts naturally sorted chapters and their images.
        Supports:
        1. Multi-chapter structure (subdirectories = chapters)
        2. Flat directory (images directly at root = 1 single chapter)
        """
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise InvalidSourceError(f"Source directory '{source_dir}' does not exist.")
        if not source_dir.is_dir():
            raise InvalidSourceError(f"Source path '{source_dir}' is not a directory.")

        chapters: List[ChapterData] = []
        children = [p for p in source_dir.iterdir() if not is_hidden_or_system_file(p)]
        subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
        direct_images = natsorted(
            [p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS],
            key=lambda p: p.name
        )

        if subdirs:
            # Multi-chapter structure
            for subdir in subdirs:
                chapter = ChapterData(title=subdir.name, folder_path=subdir)
                image_files = natsorted(
                    [
                        p for p in subdir.iterdir()
                        if p.is_file() and not is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS
                    ],
                    key=lambda p: p.name
                )
                for idx, img_path in enumerate(image_files, start=1):
                    page = ImagePage(img_path, chapter_title=subdir.name, page_index=idx)
                    if page.is_valid:
                        chapter.pages.append(page)

                if chapter.pages:
                    chapters.append(chapter)

        elif direct_images:
            # Flat single-chapter structure
            chapter = ChapterData(title=source_dir.name, folder_path=source_dir)
            for idx, img_path in enumerate(direct_images, start=1):
                page = ImagePage(img_path, chapter_title=source_dir.name, page_index=idx)
                if page.is_valid:
                    chapter.pages.append(page)
            if chapter.pages:
                chapters.append(chapter)

        return chapters

    @staticmethod
    def find_root_cover(source_dir: Path) -> Optional[Path]:
        """
        Searches the root of source_dir for an image containing 'cover' or 'couverture'.
        Returns the Path of the first naturally sorted candidate, or None.
        """
        if not source_dir:
            return None
        source_dir = Path(source_dir)
        if not source_dir.exists() or not source_dir.is_dir():
            return None

        candidates = []
        for p in source_dir.iterdir():
            if p.is_file() and not is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                stem_lower = p.stem.lower()
                if 'cover' in stem_lower or 'couverture' in stem_lower:
                    candidates.append(p)

        if candidates:
            return natsorted(candidates, key=lambda p: p.name)[0]
        return None

    @classmethod
    def detect_books(cls, source_dir: Path, force_batch: Optional[bool] = None) -> Tuple[bool, List[BookData]]:
        """
        Analyzes a directory to determine if it is a single book or a batch collection.
        - If force_batch is True: treats every valid subdirectory as an independent book.
        - If force_batch is False: treats the entire folder as a single book.
        - If force_batch is None (auto-detection):
            Inspects whether subdirectories contain nested chapters or their own cover image.
        Returns:
            Tuple of (is_batch_mode: bool, list_of_BookData).
        """
        if not source_dir:
            return False, []
        source_dir = Path(source_dir)
        if not source_dir.exists() or not source_dir.is_dir():
            return False, []

        children = [p for p in source_dir.iterdir() if not is_hidden_or_system_file(p)]
        subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
        direct_images = [p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]

        is_batch = False
        if force_batch is True:
            is_batch = True
        elif force_batch is False:
            is_batch = False
        else:
            # Auto-detection heuristic
            if subdirs and not direct_images:
                has_nested_subdirs = False
                covers_count = 0
                for sd in subdirs:
                    sd_children = [p for p in sd.iterdir() if not is_hidden_or_system_file(p)]
                    if any(p.is_dir() for p in sd_children):
                        has_nested_subdirs = True
                    if cls.find_root_cover(sd):
                        covers_count += 1
                if has_nested_subdirs or covers_count >= 2:
                    is_batch = True

        if is_batch and subdirs:
            books: List[BookData] = []
            for sd in subdirs:
                try:
                    chaps = cls.collect_chapters_and_images(sd)
                    if chaps and sum(len(c.pages) for c in chaps) > 0:
                        cov = cls.find_root_cover(sd)
                        books.append(BookData(title=sd.name, folder_path=sd, chapters=chaps, cover_path=cov))
                except Exception:
                    continue
            if books:
                return True, books

        # Single book fallback
        try:
            chaps = cls.collect_chapters_and_images(source_dir)
            cov = cls.find_root_cover(source_dir)
            single = BookData(title=source_dir.name, folder_path=source_dir, chapters=chaps, cover_path=cov)
            return False, [single] if (chaps and single.total_images > 0) else []
        except Exception:
            return False, []


# Backward-compatible function aliases
collect_chapters_and_images = ScannerService.collect_chapters_and_images
find_root_cover = ScannerService.find_root_cover
detect_books = ScannerService.detect_books
