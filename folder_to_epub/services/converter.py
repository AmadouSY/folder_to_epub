"""High-level conversion orchestration service."""

from pathlib import Path
from typing import List, Optional, Callable
from folder_to_epub.core.models import Book, ConversionConfig, ProgressEvent
from folder_to_epub.services.builder import EpubBuilder


class ConversionService:
    """Coordinates single and batch book conversions."""

    @staticmethod
    def convert_book(
        book: Book,
        config: ConversionConfig,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ) -> Path:
        """Converts a single Book model into an EPUB file."""
        builder = EpubBuilder(book=book, config=config, progress_callback=progress_callback)
        return builder.build()

    @staticmethod
    def convert_batch(
        books: List[Book],
        output_dir: Path,
        base_config: ConversionConfig,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ) -> List[Path]:
        """Converts a collection of books into individual EPUB files inside output_dir."""
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

            builder = EpubBuilder(book=book, config=book_config, progress_callback=forward_progress)
            created_epubs.append(builder.build())

        return created_epubs
