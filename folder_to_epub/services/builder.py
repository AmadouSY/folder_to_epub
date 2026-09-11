"""EPUB 3 generation service using EbookLib."""

import uuid
from pathlib import Path
from typing import Optional, Callable
from ebooklib import epub

from folder_to_epub.core.constants import DEFAULT_CSS
from folder_to_epub.core.exceptions import EpubGenerationError
from folder_to_epub.core.models import Book, ConversionConfig, ProgressEvent, ImagePage


class EpubBuilder:
    """Assembles a compliant EPUB 3 document from a Book domain model and configuration."""

    def __init__(
        self,
        book: Book,
        config: ConversionConfig,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ):
        self.book = book
        self.config = config
        self.progress_callback = progress_callback
        self.output_path = Path(config.output_path or book.folder_path.with_suffix('.epub'))

    def build(self) -> Path:
        """Executes the EPUB assembly and writes the file to disk."""
        try:
            epub_book = epub.EpubBook()
            epub_book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
            epub_book.set_title(self.config.title or self.book.title)
            epub_book.set_language(self.config.language)
            epub_book.add_author(self.config.author)

            # Manga / Fixed-Layout and RTL Progression
            if self.config.is_manga or self.config.is_rtl:
                epub_book.set_direction('rtl')
                epub_book.add_metadata(None, 'meta', 'pre-paginated', {'property': 'rendition:layout'})
                epub_book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:orientation'})
                epub_book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:spread'})
                epub_book.add_metadata(None, 'meta', 'comic', {'property': 'book-type'})
                epub_book.add_metadata(None, 'meta', 'true', {'property': 'zero-gutter'})
                epub_book.add_metadata(None, 'meta', 'true', {'property': 'zero-margin'})

            # Stylesheet
            style_item = epub.EpubItem(
                uid="style_css",
                file_name="style/style.css",
                media_type="text/css",
                content=DEFAULT_CSS.encode('utf-8')
            )
            epub_book.add_item(style_item)

            # Apply Cover
            self._apply_cover(epub_book)

            # Pages, TOC, and Spine
            spine_items = ['nav']
            toc_items = []
            total_pages = self.book.total_images
            processed_pages = 0

            img_counter = 1
            page_counter = 1

            for chap_idx, chapter in enumerate(self.book.chapters, start=1):
                chapter_xhtml_pages = []

                for page in chapter.pages:
                    img_ext = page.file_path.suffix.lower()
                    img_filename = f"images/img_{img_counter:04d}{img_ext}"

                    with open(page.file_path, 'rb') as f:
                        img_data = f.read()

                    img_item = epub.EpubItem(
                        uid=f"img_{img_counter:04d}",
                        file_name=img_filename,
                        media_type=page.mime_type,
                        content=img_data
                    )
                    epub_book.add_item(img_item)

                    page_filename = f"pages/page_{page_counter:04d}.xhtml"
                    page_title = f"{chapter.title} - Page {page.page_index}"
                    rel_img_path = f"../{img_filename}"
                    rel_css_path = "../style/style.css"

                    viewport_meta = (
                        f'<meta name="viewport" content="width={page.width}, height={page.height}" />'
                        if page.width and page.height else ''
                    )

                    xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{self.config.language}">
<head>
    <meta charset="utf-8" />
    <title>{page_title}</title>
    {viewport_meta}
    <link rel="stylesheet" type="text/css" href="{rel_css_path}" />
</head>
<body>
    <div class="page-container">
        <img class="page-image" src="{rel_img_path}" alt="{page_title}" />
    </div>
</body>
</html>
"""
                    xhtml_item = epub.EpubHtml(
                        title=page_title,
                        file_name=page_filename,
                        lang=self.config.language,
                        uid=f"page_{page_counter:04d}"
                    )
                    xhtml_item.set_content(xhtml_content.encode('utf-8'))
                    xhtml_item.add_item(style_item)
                    epub_book.add_item(xhtml_item)

                    chapter_xhtml_pages.append(xhtml_item)
                    spine_items.append(xhtml_item)

                    img_counter += 1
                    page_counter += 1
                    processed_pages += 1

                    if self.progress_callback:
                        self.progress_callback(ProgressEvent(
                            current_step=processed_pages,
                            total_steps=total_pages,
                            current_label=chapter.title,
                            book_title=self.book.title
                        ))

                if chapter_xhtml_pages:
                    toc_link = epub.Link(
                        href=chapter_xhtml_pages[0].file_name,
                        title=chapter.title,
                        uid=f"toc_chap_{chap_idx:03d}"
                    )
                    toc_items.append(toc_link)

            epub_book.toc = toc_items
            epub_book.add_item(epub.EpubNcx())
            epub_book.add_item(epub.EpubNav())
            epub_book.spine = spine_items

            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            epub.write_epub(str(self.output_path), epub_book, {})
            return self.output_path

        except Exception as e:
            raise EpubGenerationError(f"Failed to assemble EPUB '{self.output_path}': {e}") from e

    def _apply_cover(self, epub_book: epub.EpubBook) -> None:
        """Applies cover image from custom config, book cover, or first page."""
        cover_page: Optional[ImagePage] = None
        target_cover = self.config.custom_cover_path or self.book.cover_path

        if target_cover and target_cover.exists():
            cover_page = ImagePage.from_file(target_cover, "Cover", 0)
        elif self.book.chapters and self.book.chapters[0].pages:
            cover_page = self.book.chapters[0].pages[0]

        if cover_page:
            with open(cover_page.file_path, 'rb') as f:
                cover_data = f.read()
            epub_book.set_cover(f"cover_{cover_page.file_path.name}", cover_data)
