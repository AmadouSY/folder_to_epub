"""Main CLI command implementation."""

import sys
from pathlib import Path
from folder_to_epub.cli.parser import build_arg_parser
from folder_to_epub.cli.renderer import CliRenderer, RICH_AVAILABLE
from folder_to_epub.core.models import Book, ConversionConfig, ProgressEvent
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.converter import ConversionService

if RICH_AVAILABLE:
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn
    )


def main() -> None:
    """CLI execution entrypoint."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # GUI requested or no directory provided
    if args.gui or args.source_dir is None:
        try:
            from folder_to_epub.ui.app import main as launch_gui
            launch_gui()
            return
        except ImportError as e:
            print(f"Error: Unable to start GUI ({e}). Ensure 'customtkinter' is installed.", file=sys.stderr)
            if args.source_dir is None:
                parser.print_help()
                sys.exit(1)

    renderer = CliRenderer()
    source_path = args.source_dir.resolve()

    if not source_path.exists() or not source_path.is_dir():
        renderer.print_error(f"Source folder '{source_path}' does not exist or is not a directory.")
        sys.exit(1)

    # 1. Inspect source directory for Batch Multi-Books vs Single Book
    is_batch, detected_books = ScannerService.detect_books(
        source_path,
        force_batch=True if args.batch else None
    )

    base_config = ConversionConfig(
        title=args.title or source_path.name,
        author=args.author,
        language=args.lang,
        custom_cover_path=args.cover,
        is_manga=args.manga,
        is_rtl=args.rtl
    )

    if is_batch and len(detected_books) > 1:
        # BATCH MULTI-BOOKS CONVERSION
        out_dir = args.output.resolve() if args.output else source_path.parent / f"{source_path.name}_epubs"
        if out_dir.suffix.lower() == ".epub":
            out_dir = out_dir.parent

        renderer.render_batch_header(
            source=source_path,
            output_dir=out_dir,
            count=len(detected_books),
            is_manga=args.manga,
            is_rtl=args.rtl
        )
        renderer.render_books_table(detected_books)

        if renderer.is_rich:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=renderer.console
            ) as progress:
                overall_task = progress.add_task(
                    "[bold cyan]Overall books...",
                    total=len(detected_books)
                )
                current_book_task = progress.add_task(
                    "[bold magenta]Current page...",
                    total=1
                )

                def update_batch(event: ProgressEvent):
                    progress.update(
                        overall_task,
                        completed=event.current_book_index - 1,
                        description=f"[bold cyan]Book {event.current_book_index}/{event.total_books}: {event.book_title}"
                    )
                    progress.update(
                        current_book_task,
                        total=event.total_steps,
                        completed=event.current_step,
                        description=f"[bold magenta]{event.book_title} (p. {event.current_step}/{event.total_steps})"
                    )

                created = ConversionService.convert_batch(
                    books=detected_books,
                    output_dir=out_dir,
                    base_config=base_config,
                    progress_callback=update_batch
                )
                progress.update(overall_task, completed=len(detected_books))
        else:
            print(f"Converting {len(detected_books)} books...")
            created = ConversionService.convert_batch(
                books=detected_books,
                output_dir=out_dir,
                base_config=base_config
            )

        renderer.render_success(f"Success! {len(created)} EPUB books generated in:", out_dir)
        return

    # SINGLE BOOK CONVERSION
    book_title = args.title or source_path.name
    output_file = args.output or source_path.with_suffix('.epub')

    renderer.render_single_header(
        source=source_path,
        output_file=output_file,
        title=book_title,
        author=args.author,
        lang=args.lang,
        is_manga=args.manga,
        is_rtl=args.rtl
    )

    chapters = ScannerService.scan_chapters(source_path)
    if not chapters:
        renderer.print_error("No valid images found in the source directory.")
        sys.exit(1)

    cover = args.cover or ScannerService.find_cover(source_path)
    if cover:
        renderer.print_info(f"Cover detected: {cover.name}")

    single_book = Book(
        title=book_title,
        folder_path=source_path,
        chapters=chapters,
        cover_path=cover
    )

    renderer.render_chapters_table(single_book.chapters)
    single_config = ConversionConfig(
        title=book_title,
        author=args.author,
        language=args.lang,
        output_path=output_file,
        custom_cover_path=cover,
        source_dir=source_path,
        is_manga=args.manga,
        is_rtl=args.rtl
    )

    if renderer.is_rich:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=renderer.console
        ) as progress:
            task = progress.add_task("[bold cyan]Generating EPUB...", total=single_book.total_images)

            def update_single(event: ProgressEvent):
                progress.update(
                    task,
                    completed=event.current_step,
                    description=f"[bold cyan]Processing: {event.current_label}"
                )

            final_epub = ConversionService.convert_book(
                book=single_book,
                config=single_config,
                progress_callback=update_single
            )
    else:
        print(f"Generating EPUB for {single_book.total_images} pages...")
        final_epub = ConversionService.convert_book(
            book=single_book,
            config=single_config
        )

    renderer.render_success("Success! EPUB created successfully:", final_epub)


if __name__ == "__main__":
    main()
