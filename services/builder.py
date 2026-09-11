"""EPUB Builder service responsible for assembling EPUB 3 eBooks using EbookLib."""

import uuid
from pathlib import Path
from typing import List, Optional, Callable
from ebooklib import epub

from core.constants import DEFAULT_CSS
from core.models import ChapterData, ImagePage
from core.exceptions import EpubGenerationError
from services.scanner import find_root_cover


class EpubBuilder:
    """Constructs a compliant EPUB 3 document from chapters and image pages."""

    def __init__(
        self,
        chapters: List[ChapterData],
        output_file: Path,
        title: str,
        author: str = "Unknown",
        language: str = "en",
        custom_cover_path: Optional[Path] = None,
        source_dir: Optional[Path] = None,
        is_manga: bool = False,
        is_rtl: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        self.chapters = chapters
        self.output_file = Path(output_file)
        self.title = title
        self.author = author
        self.language = language
        self.custom_cover_path = Path(custom_cover_path) if custom_cover_path else None
        self.source_dir = Path(source_dir) if source_dir else None
        self.is_manga = is_manga
        self.is_rtl = is_rtl
        self.progress_callback = progress_callback

    def build(self) -> Path:
        """Executes the EPUB construction and writes the file to disk."""
        try:
            book = epub.EpubBook()
            book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
            book.set_title(self.title)
            book.set_language(self.language)
            book.add_author(self.author)

            # Reading direction & Manga / Fixed-Layout metadata
            if self.is_manga or self.is_rtl:
                book.set_direction('rtl')
                book.add_metadata(None, 'meta', 'pre-paginated', {'property': 'rendition:layout'})
                book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:orientation'})
                book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:spread'})
                book.add_metadata(None, 'meta', 'comic', {'property': 'book-type'})
                book.add_metadata(None, 'meta', 'true', {'property': 'zero-gutter'})
                book.add_metadata(None, 'meta', 'true', {'property': 'zero-margin'})

            # CSS Stylesheet
            style_item = epub.EpubItem(
                uid="style_css",
                file_name="style/style.css",
                media_type="text/css",
                content=DEFAULT_CSS.encode('utf-8')
            )
            book.add_item(style_item)

            # Cover image handling
            self._apply_cover(book)

            # Pages, Spine, and TOC
            spine_items = ['nav']
            toc_items = []
            total_pages_count = sum(len(c.pages) for c in self.chapters)
            processed_pages = 0

            img_counter = 1
            page_counter = 1

            for chap_idx, chapter in enumerate(self.chapters, start=1):
                chapter_xhtml_pages = []

                for page in chapter.pages:
                    img_ext = page.file_path.suffix.lower()
                    img_filename = f"images/img_{img_counter:04d}{img_ext}"

                    # 1. Add image binary resource
                    with open(page.file_path, 'rb') as f:
                        img_data = f.read()

                    img_item = epub.EpubItem(
                        uid=f"img_{img_counter:04d}",
                        file_name=img_filename,
                        media_type=page.mime_type,
                        content=img_data
                    )
                    book.add_item(img_item)

                    # 2. Add XHTML page wrapper
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
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{self.language}">
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
                        lang=self.language,
                        uid=f"page_{page_counter:04d}"
                    )
                    xhtml_item.set_content(xhtml_content.encode('utf-8'))
                    xhtml_item.add_item(style_item)
                    book.add_item(xhtml_item)

                    chapter_xhtml_pages.append(xhtml_item)
                    spine_items.append(xhtml_item)

                    img_counter += 1
                    page_counter += 1
                    processed_pages += 1

                    if self.progress_callback:
                        self.progress_callback(processed_pages, total_pages_count, chapter.title)

                # Add chapter header to Table of Contents
                if chapter_xhtml_pages:
                    toc_link = epub.Link(
                        href=chapter_xhtml_pages[0].file_name,
                        title=chapter.title,
                        uid=f"toc_chap_{chap_idx:03d}"
                    )
                    toc_items.append(toc_link)

            book.toc = toc_items
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = spine_items

            # Write EPUB to disk
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            epub.write_epub(str(self.output_file), book, {})
            return self.output_file

        except Exception as e:
            raise EpubGenerationError(f"Failed to generate EPUB '{self.output_file}': {e}") from e

    def _apply_cover(self, book: epub.EpubBook) -> None:
        """Determines and sets the EPUB cover image."""
        cover_page: Optional[ImagePage] = None
        if self.custom_cover_path and self.custom_cover_path.exists():
            cover_page = ImagePage(self.custom_cover_path, "Cover", 0)
        else:
            root_cover = None
            if self.source_dir:
                root_cover = find_root_cover(self.source_dir)
            elif self.chapters and self.chapters[0].folder_path:
                parent_dir = self.chapters[0].folder_path.parent
                root_cover = find_root_cover(parent_dir) or find_root_cover(self.chapters[0].folder_path)

            if root_cover and root_cover.exists():
                cover_page = ImagePage(root_cover, "Cover", 0)
            elif self.chapters and self.chapters[0].pages:
                cover_page = self.chapters[0].pages[0]

        if cover_page and cover_page.is_valid:
            with open(cover_page.file_path, 'rb') as f:
                cover_data = f.read()
            book.set_cover(f"cover_{cover_page.file_path.name}", cover_data)


def create_epub(
    chapters: List[ChapterData],
    output_file: Path,
    title: str,
    author: str = "Unknown",
    language: str = "en",
    custom_cover_path: Optional[Path] = None,
    source_dir: Optional[Path] = None,
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Path:
    """Convenience function to generate an EPUB file."""
    builder = EpubBuilder(
        chapters=chapters,
        output_file=output_file,
        title=title,
        author=author,
        language=language,
        custom_cover_path=custom_cover_path,
        source_dir=source_dir,
        is_manga=is_manga,
        is_rtl=is_rtl,
        progress_callback=progress_callback
    )
    return builder.build()
