"""Archive processing service for .cbz and .zip files."""

import os
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List
from natsort import natsorted

from folder_to_epub.core.constants import SUPPORTED_EXTENSIONS, SUPPORTED_ARCHIVE_EXTENSIONS


class ArchiveService:
    """Provides safe reading, fast cover extraction, and unpacking for comic/manga archives."""

    @staticmethod
    def is_archive(path: Path) -> bool:
        """Returns True if the path is a file with a supported archive extension (.cbz, .zip)."""
        if not path:
            return False
        path = Path(path)
        return path.is_file() and path.suffix.lower() in SUPPORTED_ARCHIVE_EXTENSIONS

    @classmethod
    def get_archive_image_namelist(cls, archive_path: Path) -> List[str]:
        """Returns a naturally sorted list of all valid image entries inside the archive."""
        archive_path = Path(archive_path)
        valid_images = []
        try:
            with zipfile.ZipFile(archive_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('/') or name.endswith('\\'):
                        continue
                    clean_name = name.replace('\\', '/')
                    filename = clean_name.split('/')[-1]
                    if filename.startswith('.') or filename.lower() in ('thumbs.db', 'desktop.ini'):
                        continue
                    ext = Path(filename).suffix.lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        valid_images.append(name)
        except Exception:
            return []

        return natsorted(valid_images)

    @classmethod
    def get_cover_bytes(cls, archive_path: Path) -> Optional[Tuple[str, bytes]]:
        """
        Fast in-memory extraction of the cover image without unzipping the entire archive.
        Searches for entries with 'cover' in their name first, or falls back to the first image.
        Returns:
            Tuple of (filename: str, image_bytes: bytes) or None.
        """
        image_names = cls.get_archive_image_namelist(archive_path)
        if not image_names:
            return None

        # Prefer an image named 'cover' or 'couverture'
        cover_candidate = None
        for name in image_names:
            stem_lower = Path(name).stem.lower()
            if 'cover' in stem_lower or 'couverture' in stem_lower:
                cover_candidate = name
                break

        if not cover_candidate:
            cover_candidate = image_names[0]

        try:
            with zipfile.ZipFile(archive_path, 'r') as z:
                data = z.read(cover_candidate)
                filename = Path(cover_candidate).name
                return filename, data
        except Exception:
            return None

    @classmethod
    def inspect_archive(cls, archive_path: Path) -> Tuple[int, List[str]]:
        """
        Inspects the archive structure without full extraction.
        Returns:
            Tuple of (total_images_count, list_of_detected_chapter_names).
        """
        image_names = cls.get_archive_image_namelist(archive_path)
        if not image_names:
            return 0, []

        chapters = set()
        for name in image_names:
            clean_name = name.replace('\\', '/')
            parts = clean_name.split('/')
            if len(parts) > 1:
                chapters.add(parts[0])

        chapter_list = natsorted(list(chapters)) if chapters else [Path(archive_path).stem]
        return len(image_names), chapter_list

    @classmethod
    def extract_archive(cls, archive_path: Path, dest_dir: Path) -> Path:
        """
        Safely extracts an archive to dest_dir, preventing directory traversal attacks.
        Returns dest_dir.
        """
        archive_path = Path(archive_path)
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path, 'r') as z:
            for member in z.infolist():
                # Sanitize target path against path traversal (Zip Slip vulnerability prevention)
                member_path = member.filename.replace('\\', '/')
                target_path = (dest_dir / member_path).resolve()
                if not str(target_path).startswith(str(dest_dir.resolve())):
                    continue

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

        return dest_dir
