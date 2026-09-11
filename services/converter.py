"""Conversion service for orchestrating single and batch EPUB generation."""

from pathlib import Path
from typing import List, Optional, Callable
from core.models import BookData, ConversionConfig
from services.builder import create_epub


class ConversionService:
    """Orchestrates single-book and batch eBook conversions."""

    @staticmethod
    def convert_single_book(
        book: BookData,
        config: ConversionConfig,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Path:
        """Converts a single BookData into an EPUB file."""
        out_path = config.output_path or book.folder_path.with_suffix('.epub')
        cover_path = config.custom_cover_path or book.cover_path

        return create_epub(
            chapters=book.chapters,
            output_file=out_path,
            title=config.title or book.title,
            author=config.author,
            language=config.language,
            custom_cover_path=cover_path,
            source_dir=config.source_dir or book.folder_path,
            is_manga=config.is_manga,
            is_rtl=config.is_rtl,
            progress_callback=progress_callback
        )

    @staticmethod
    def convert_batch(
        books: List[BookData],
        output_dir: Path,
        author: str = "Unknown",
        language: str = "en",
        is_manga: bool = False,
        is_rtl: bool = False,
        progress_callback: Optional[Callable[[int, int, BookData, int, int], None]] = None
    ) -> List[Path]:
        """
        Converts multiple books in batch mode.
        progress_callback signature:
            (book_idx, total_books, book, current_page_in_book, total_pages_in_book)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_epubs: List[Path] = []
        total_books = len(books)

        for b_idx, book in enumerate(books, start=1):
            out_epub = output_dir / f"{book.title}.epub"

            def on_book_page_progress(curr: int, tot: int, chap_title: str):
                if progress_callback:
                    progress_callback(b_idx, total_books, book, curr, tot)

            create_epub(
                chapters=book.chapters,
                output_file=out_epub,
                title=book.title,
                author=author,
                language=language,
                custom_cover_path=book.cover_path,
                source_dir=book.folder_path,
                is_manga=is_manga,
                is_rtl=is_rtl,
                progress_callback=on_book_page_progress
            )
            generated_epubs.append(out_epub)

        return generated_epubs


def create_epub_batch(
    books: List[BookData],
    output_dir: Path,
    author: str = "Unknown",
    language: str = "en",
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback: Optional[Callable[[int, int, BookData, int, int], None]] = None
) -> List[Path]:
    """Convenience function for batch conversion."""
    return ConversionService.convert_batch(
        books=books,
        output_dir=output_dir,
        author=author,
        language=language,
        is_manga=is_manga,
        is_rtl=is_rtl,
        progress_callback=progress_callback
    )
