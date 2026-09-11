"""High-level conversion orchestration service supporting folders and archives."""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable
from folder_to_epub.core.models import Book, ConversionConfig, ProgressEvent
from folder_to_epub.services.builder import EpubBuilder
from folder_to_epub.services.archive import ArchiveService
from folder_to_epub.services.scanner import ScannerService


class ConversionService:
    """Coordinates single and batch book conversions from folders and archives."""

    @classmethod
    def convert_book(
        cls,
        book: Book,
        config: ConversionConfig,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ) -> Path:
        """
        Converts a single Book model into an EPUB file.
        If the book originates from an archive (.cbz, .zip), it is extracted to a
        temporary directory for conversion and automatically purged afterwards.
        """
        if book.is_archive and book.archive_path:
            with tempfile.TemporaryDirectory() as temp_dir:
                extracted_path = Path(temp_dir)
                ArchiveService.extract_archive(book.archive_path, extracted_path)

                chapters = ScannerService.scan_chapters(extracted_path)
                cover = config.custom_cover_path or ScannerService.find_cover(extracted_path)

                temp_book = Book(
                    title=config.title or book.title,
                    folder_path=extracted_path,
                    chapters=chapters,
                    cover_path=cover
                )
                temp_config = ConversionConfig(
                    title=config.title or book.title,
                    author=config.author,
                    language=config.language,
                    output_path=config.output_path or book.archive_path.with_suffix('.epub'),
                    custom_cover_path=cover,
                    source_dir=extracted_path,
                    is_manga=config.is_manga,
                    is_rtl=config.is_rtl
                )
                builder = EpubBuilder(book=temp_book, config=temp_config, progress_callback=progress_callback)
                return builder.build()

        builder = EpubBuilder(book=book, config=config, progress_callback=progress_callback)
        return builder.build()

    @classmethod
    def convert_batch(
        cls,
        books: List[Book],
        output_dir: Path,
        base_config: ConversionConfig,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ) -> List[Path]:
        """Converts a collection of books (folders or archives) into individual EPUB files inside output_dir."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        created_epubs: List[Path] = []
        total_books = len(books)

        for b_idx, book in enumerate(books, start=1):
            out_file = output_dir / f"{book.title}.epub"
            book_config = ConversionConfig(
                title=book.title,
                author=base_config.author,
                language=base_config.language,
                output_path=out_file,
                custom_cover_path=book.cover_path,
                source_dir=book.folder_path,
                is_manga=base_config.is_manga,
                is_rtl=base_config.is_rtl
            )

            def forward_progress(event: ProgressEvent):
                if progress_callback:
                    event.current_book_index = b_idx
                    event.total_books = total_books
                    event.book_title = book.title
                    progress_callback(event)

            created_epubs.append(cls.convert_book(book=book, config=book_config, progress_callback=forward_progress))

        return created_epubs
