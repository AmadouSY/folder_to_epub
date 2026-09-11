#!/usr/bin/env python3
"""
Folder to EPUB Converter (CLI & Engine)
=======================================
A Python tool to convert a directory of images or chapter subdirectories
into clean, structured, and responsive EPUB eBooks optimized for e-readers
(Kindle, Kobo, Apple Books, etc.).

Supports both single-book and batch collection modes.

Expected directory structure (Single Book):
------------------------------------------
source_folder/
├── Chapter 01/
│   ├── 01.jpg
│   ├── 02.jpg
│   └── 03.jpg
└── Chapter 02/
    ├── 01.jpg
    └── 02.jpg

Expected directory structure (Batch Multi-Books):
------------------------------------------------
collection_folder/
├── Book 01/
│   ├── cover.jpg (optional)
│   ├── Chapter 01/
│   │   └── 01.jpg
│   └── Chapter 02/
│       └── 01.jpg
└── Book 02/
    ├── 01.jpg
    └── 02.jpg

Usage Examples:
---------------
$ python folder_to_epub.py ./my_book -o ./my_book.epub --title "My Manga" --author "Author" --lang en
$ python folder_to_epub.py ./my_manga --manga --rtl
$ python folder_to_epub.py ./my_collection --batch -o ./output_epubs/
"""

import argparse
import sys
import uuid
import mimetypes
from pathlib import Path
from typing import List, Tuple, Optional, Dict

try:
    from PIL import Image
except ImportError:
    sys.exit("Error: 'Pillow' is required. Install it using 'pip install Pillow'.")

try:
    from natsort import natsorted
except ImportError:
    sys.exit("Error: 'natsort' is required. Install it using 'pip install natsort'.")

try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    sys.exit("Error: 'EbookLib' is required. Install it using 'pip install EbookLib'.")

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Supported image formats
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

# Default clean, responsive CSS stylesheet
DEFAULT_CSS = """@page {
    margin: 0;
    padding: 0;
}
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    text-align: center;
    background-color: #ffffff;
}
div.page-container {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
img.page-image {
    max-width: 100%;
    max-height: 100%;
    height: auto;
    width: auto;
    object-fit: contain;
    display: block;
    margin: 0 auto;
}
"""


class ImagePage:
    """Represents an image page with its metadata and dimensions."""
    def __init__(self, file_path: Path, chapter_title: str, page_index: int):
        self.file_path = file_path
        self.chapter_title = chapter_title
        self.page_index = page_index
        self.width: int = 0
        self.height: int = 0
        self.mime_type: str = "image/jpeg"
        self.is_valid: bool = False
        self._inspect_image()

    def _inspect_image(self):
        """Validates the image with Pillow and extracts dimensions and MIME type."""
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


class ChapterData:
    """Represents a chapter containing its sorted image pages."""
    def __init__(self, title: str, folder_path: Optional[Path] = None):
        self.title = title
        self.folder_path = folder_path
        self.pages: List[ImagePage] = []


class BookData:
    """Represents a full book with its title, folder, chapters, cover and page counts."""
    def __init__(self, title: str, folder_path: Path, chapters: List[ChapterData], cover_path: Optional[Path] = None):
        self.title = title
        self.folder_path = folder_path
        self.chapters = chapters
        self.cover_path = cover_path
        self.total_images = sum(len(c.pages) for c in chapters)


def is_hidden_or_system_file(path: Path) -> bool:
    """Checks if a file or directory is hidden or a system file (e.g. .DS_Store, Thumbs.db)."""
    name = path.name
    if name.startswith('.') or name.startswith('~$'):
        return True
    if name.lower() in ('thumbs.db', 'desktop.ini', 'ehthumbs.db'):
        return True
    return False


def collect_chapters_and_images(source_dir: Path) -> List[ChapterData]:
    """
    Scans the source directory and extracts naturally sorted chapters and their images.
    Supports:
    1. Multi-chapter structure (subdirectories = chapters)
    2. Flat directory (images directly at root = 1 single chapter)
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory '{source_dir}' does not exist.")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path '{source_dir}' is not a directory.")

    chapters: List[ChapterData] = []

    children = [p for p in source_dir.iterdir() if not is_hidden_or_system_file(p)]
    subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
    direct_images = natsorted([p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS], key=lambda p: p.name)

    if subdirs:
        # Multi-chapter structure
        for subdir in subdirs:
            chapter = ChapterData(title=subdir.name, folder_path=subdir)
            image_files = natsorted(
                [p for p in subdir.iterdir() if p.is_file() and not is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS],
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


def find_root_cover(source_dir: Path) -> Optional[Path]:
    """
    Searches the root of source_dir for an image containing 'cover' (case-insensitive).
    Returns the Path of the first naturally sorted candidate, or None.
    """
    if not source_dir or not source_dir.exists() or not source_dir.is_dir():
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


def detect_books(source_dir: Path, force_batch: Optional[bool] = None) -> Tuple[bool, List[BookData]]:
    """
    Analyzes a directory to determine if it is a single book or a collection (multi-book batch).
    - If force_batch is True: treats every valid subdirectory as an independent book.
    - If force_batch is False: treats the entire folder as a single book.
    - If force_batch is None (auto):
        Checks if subdirectories contain nested subdirectories with images,
        or if multiple subdirectories contain their own cover image. If so, enables batch mode.
    Returns (is_batch, list_of_BookData).
    """
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
        # Auto-detection
        if subdirs and not direct_images:
            has_nested_subdirs = False
            covers_count = 0
            for sd in subdirs:
                sd_children = [p for p in sd.iterdir() if not is_hidden_or_system_file(p)]
                if any(p.is_dir() for p in sd_children):
                    has_nested_subdirs = True
                if find_root_cover(sd):
                    covers_count += 1
            if has_nested_subdirs or covers_count >= 2:
                is_batch = True

    if is_batch and subdirs:
        books: List[BookData] = []
        for sd in subdirs:
            try:
                chaps = collect_chapters_and_images(sd)
                if chaps and sum(len(c.pages) for c in chaps) > 0:
                    cov = find_root_cover(sd)
                    books.append(BookData(title=sd.name, folder_path=sd, chapters=chaps, cover_path=cov))
            except Exception:
                continue
        if books:
            return True, books

    # Single book fallback
    try:
        chaps = collect_chapters_and_images(source_dir)
        cov = find_root_cover(source_dir)
        single = BookData(title=source_dir.name, folder_path=source_dir, chapters=chaps, cover_path=cov)
        return False, [single] if (chaps and single.total_images > 0) else []
    except Exception:
        return False, []


def create_epub(
    chapters: List[ChapterData],
    output_file: Path,
    title: str,
    author: str,
    language: str = "en",
    custom_cover_path: Optional[Path] = None,
    source_dir: Optional[Path] = None,
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback=None
) -> Path:
    """Generates an EPUB file from chapters and their image pages."""

    book = epub.EpubBook()
    book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # Reading direction & Manga / Fixed-Layout metadata
    if is_manga or is_rtl:
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
    cover_page: Optional[ImagePage] = None
    if custom_cover_path and custom_cover_path.exists():
        cover_page = ImagePage(custom_cover_path, "Cover", 0)
    else:
        # Default: image at root containing 'cover' in its name
        root_cover = None
        if source_dir:
            root_cover = find_root_cover(source_dir)
        elif chapters and chapters[0].folder_path:
            parent_dir = chapters[0].folder_path.parent
            root_cover = find_root_cover(parent_dir) or find_root_cover(chapters[0].folder_path)

        if root_cover and root_cover.exists():
            cover_page = ImagePage(root_cover, "Cover", 0)
        elif chapters and chapters[0].pages:
            cover_page = chapters[0].pages[0]

    if cover_page and cover_page.is_valid:
        with open(cover_page.file_path, 'rb') as f:
            cover_data = f.read()
        book.set_cover(f"cover_{cover_page.file_path.name}", cover_data)

    spine_items = ['nav']
    toc_items = []
    total_pages_count = sum(len(c.pages) for c in chapters)
    processed_pages = 0

    img_counter = 1
    page_counter = 1

    for chap_idx, chapter in enumerate(chapters, start=1):
        chapter_xhtml_pages = []

        for page in chapter.pages:
            img_ext = page.file_path.suffix.lower()
            img_filename = f"images/img_{img_counter:04d}{img_ext}"
            
            # 1. Add image resource
            with open(page.file_path, 'rb') as f:
                img_data = f.read()

            img_item = epub.EpubItem(
                uid=f"img_{img_counter:04d}",
                file_name=img_filename,
                media_type=page.mime_type,
                content=img_data
            )
            book.add_item(img_item)

            # 2. Add XHTML page
            page_filename = f"pages/page_{page_counter:04d}.xhtml"
            page_title = f"{chapter.title} - Page {page.page_index}"

            rel_img_path = f"../{img_filename}"
            rel_css_path = "../style/style.css"

            viewport_meta = f'<meta name="viewport" content="width={page.width}, height={page.height}" />' if page.width and page.height else ''

            xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{language}">
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
                lang=language,
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

            if progress_callback:
                progress_callback(processed_pages, total_pages_count, chapter.title)

        # Add chapter to Table of Contents
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

    # Write output EPUB file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_file), book, {})
    return output_file


def create_epub_batch(
    books: List[BookData],
    output_dir: Path,
    author: str = "Unknown",
    language: str = "en",
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback=None
) -> List[Path]:
    """
    Generates an EPUB file for each book in batch mode.
    progress_callback(book_idx, total_books, book, current_page, total_pages_in_book)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_epubs: List[Path] = []
    total_books = len(books)

    for b_idx, book in enumerate(books, start=1):
        out_epub = output_dir / f"{book.title}.epub"

        def on_book_page_progress(curr, tot, chap_title):
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


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image folder or chapter subdirectories into a clean, structured EPUB eBook.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Usage Examples:
  python folder_to_epub.py ./my_book
  python folder_to_epub.py ./manga_folder -o ./manga.epub --title "One Piece Vol 1" --author "Oda" --manga --rtl
  python folder_to_epub.py ./my_collection --batch -o ./output_epubs/
"""
    )
    parser.add_argument("source_dir", nargs="?", type=Path, default=None, help="Path to the source folder containing images, chapters, or multiple books.")
    parser.add_argument("-g", "--gui", action="store_true", help="Launch the graphical user interface (GUI).")
    parser.add_argument("-b", "--batch", action="store_true", help="Enable multi-book batch mode (creates an EPUB file for each book subdirectory).")
    parser.add_argument("-o", "--output", type=Path, help="Output EPUB file path (or destination directory in batch mode).")
    parser.add_argument("-t", "--title", type=str, help="eBook title (defaults to source folder name; ignored in batch mode).")
    parser.add_argument("-a", "--author", type=str, default="Unknown", help="Author of the book (default: 'Unknown').")
    parser.add_argument("-l", "--lang", type=str, default="en", help="Language code (default: 'en').")
    parser.add_argument("-c", "--cover", type=Path, help="Optional custom cover image path.")
    parser.add_argument("--manga", action="store_true", help="Enable Fixed-Layout formatting optimized for Manga and Comics.")
    parser.add_argument("--rtl", action="store_true", help="Set reading progression from Right-To-Left (RTL).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output.")

    args = parser.parse_args()

    # Launch GUI if requested or if no argument is provided
    if args.gui or args.source_dir is None:
        try:
            from gui import main as launch_gui
            launch_gui()
            return
        except ImportError as e:
            print(f"Error: Unable to load GUI ({e}). Install 'customtkinter'.", file=sys.stderr)
            if args.source_dir is None:
                parser.print_help()
                sys.exit(1)

    console = Console() if RICH_AVAILABLE else None

    source_path = args.source_dir.resolve()
    if not source_path.exists() or not source_path.is_dir():
        msg = f"Error: Source folder '{source_path}' does not exist or is not a directory."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    # 1. Detection: Batch Multi-Books vs Single Book
    is_batch, detected_books = detect_books(source_path, force_batch=True if args.batch else None)

    if is_batch and len(detected_books) > 1:
        # BATCH MULTI-BOOKS MODE
        out_dir = args.output.resolve() if args.output else source_path.parent / f"{source_path.name}_epubs"
        if out_dir.suffix.lower() == ".epub":
            out_dir = out_dir.parent

        if console:
            console.print(Panel.fit(
                f"[bold cyan]Batch Processing Mode (Multi-Books)[/bold cyan]\n"
                f"[yellow]Collection Source :[/yellow] {source_path}\n"
                f"[yellow]Output Directory  :[/yellow] {out_dir}\n"
                f"[yellow]Books Detected    :[/yellow] {len(detected_books)}\n"
                f"[yellow]Manga/Comic Mode  :[/yellow] {'Yes' if args.manga else 'No'} | [yellow]RTL Direction :[/yellow] {'Yes' if args.rtl else 'No'}",
                title="Batch Configuration"
            ))

            table = Table(title="Books to Convert")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("Book Title", style="magenta")
            table.add_column("Chapters", justify="right", style="blue")
            table.add_column("Pages", justify="right", style="green")
            table.add_column("Cover Image", style="yellow")

            for idx, b in enumerate(detected_books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1st page"
                table.add_row(str(idx), b.title, str(len(b.chapters)), str(b.total_images), cov_str)
            console.print(table)
            console.print("")

        if RICH_AVAILABLE and console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                overall_task = progress.add_task("[bold cyan]Overall books progress...", total=len(detected_books))
                current_book_task = progress.add_task("[bold magenta]Current page...", total=1)

                def update_batch_progress(b_idx, total_b, book, curr_p, total_p):
                    progress.update(overall_task, completed=b_idx - 1, description=f"[bold cyan]Book {b_idx}/{total_b}: {book.title}")
                    progress.update(current_book_task, total=total_p, completed=curr_p, description=f"[bold magenta]{book.title} (p. {curr_p}/{total_p})")

                created_files = create_epub_batch(
                    books=detected_books,
                    output_dir=out_dir,
                    author=args.author,
                    language=args.lang,
                    is_manga=args.manga,
                    is_rtl=args.rtl,
                    progress_callback=update_batch_progress
                )
                progress.update(overall_task, completed=len(detected_books))
        else:
            print(f"Generating {len(detected_books)} EPUB books...")
            created_files = create_epub_batch(
                books=detected_books,
                output_dir=out_dir,
                author=args.author,
                language=args.lang,
                is_manga=args.manga,
                is_rtl=args.rtl
            )

        if console:
            console.print(f"\n[bold green]Success! {len(created_files)} EPUB books generated in:[/bold green]\n[cyan]{out_dir}[/cyan]")
        else:
            print(f"Success! {len(created_files)} EPUB files created in: {out_dir}")
        return

    # SINGLE BOOK MODE
    book_title = args.title or source_path.name
    output_file = args.output or source_path.with_suffix('.epub')

    if console:
        console.print(Panel.fit(
            f"[bold cyan]EPUB Generator (Single Book)[/bold cyan]\n"
            f"[yellow]Source :[/yellow] {source_path}\n"
            f"[yellow]Output :[/yellow] {output_file}\n"
            f"[yellow]Title  :[/yellow] {book_title} | [yellow]Author :[/yellow] {args.author} | [yellow]Language :[/yellow] {args.lang}\n"
            f"[yellow]Manga/Comic Mode :[/yellow] {'Yes' if args.manga else 'No'} | [yellow]RTL Direction :[/yellow] {'Yes' if args.rtl else 'No'}",
            title="Configuration"
        ))

    chapters = collect_chapters_and_images(source_path)
    if not chapters:
        msg = "Error: No valid images found in the source folder or its subdirectories."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    total_images = sum(len(c.pages) for c in chapters)

    if console:
        table = Table(title="Detected Chapters")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Chapter Name", style="magenta")
        table.add_column("Pages", justify="right", style="green")

        for idx, chap in enumerate(chapters, start=1):
            table.add_row(str(idx), chap.title, str(len(chap.pages)))
        
        console.print(table)
        console.print(f"[bold green]Total: {len(chapters)} chapter(s), {total_images} image page(s).[/bold green]\n")

    # Automatic root cover detection
    cover_to_use = args.cover
    if not cover_to_use:
        auto_cover = find_root_cover(source_path)
        if auto_cover:
            cover_to_use = auto_cover
            if console:
                console.print(f"[bold cyan]ℹ Root cover detected:[/bold cyan] [yellow]{auto_cover.name}[/yellow]")
            else:
                print(f"ℹ Root cover detected: {auto_cover.name}")

    if RICH_AVAILABLE and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[bold cyan]Generating EPUB...", total=total_images)

            def update_progress(current, total, current_chap):
                progress.update(task, completed=current, description=f"[bold cyan]Processing: {current_chap}")

            final_epub = create_epub(
                chapters=chapters,
                output_file=output_file,
                title=book_title,
                author=args.author,
                language=args.lang,
                custom_cover_path=cover_to_use,
                source_dir=source_path,
                is_manga=args.manga,
                is_rtl=args.rtl,
                progress_callback=update_progress
            )
    else:
        print(f"Generating EPUB for {total_images} pages...")
        final_epub = create_epub(
            chapters=chapters,
            output_file=output_file,
            title=book_title,
            author=args.author,
            language=args.lang,
            custom_cover_path=cover_to_use,
            source_dir=source_path,
            is_manga=args.manga,
            is_rtl=args.rtl
        )

    if console:
        console.print(f"\n[bold green]Success! EPUB file generated successfully:[/bold green]\n[cyan]{final_epub.resolve()}[/cyan]")
    else:
        print(f"Success! EPUB file created: {final_epub.resolve()}")


if __name__ == "__main__":
    main()
