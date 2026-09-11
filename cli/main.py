"""Main CLI orchestration flow."""

import sys
from pathlib import Path
from cli.parser import build_arg_parser
from cli.renderer import CliRenderer, RICH_AVAILABLE
from services.scanner import ScannerService
from services.converter import ConversionService
from services.builder import create_epub
from core.models import ConversionConfig

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
    """Entry point for the command-line interface."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Launch GUI if requested or if no directory argument is given
    if args.gui or args.source_dir is None:
        try:
            from ui.app import main as launch_gui
            launch_gui()
            return
        except ImportError as e:
            print(f"Error: Unable to load GUI ({e}). Install 'customtkinter'.", file=sys.stderr)
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

    if is_batch and len(detected_books) > 1:
        # BATCH MULTI-BOOKS CONVERSION
        out_dir = args.output.resolve() if args.output else source_path.parent / f"{source_path.name}_epubs"
        if out_dir.suffix.lower() == ".epub":
            out_dir = out_dir.parent

        renderer.render_batch_header(
            source_path=source_path,
            out_dir=out_dir,
            book_count=len(detected_books),
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
                    "[bold cyan]Overall books progress...",
                    total=len(detected_books)
                )
                current_book_task = progress.add_task(
                    "[bold magenta]Current page...",
                    total=1
                )

                def update_batch_progress(b_idx, total_b, book, curr_p, total_p):
                    progress.update(
                        overall_task,
                        completed=b_idx - 1,
                        description=f"[bold cyan]Book {b_idx}/{total_b}: {book.title}"
                    )
                    progress.update(
                        current_book_task,
                        total=total_p,
                        completed=curr_p,
                        description=f"[bold magenta]{book.title} (p. {curr_p}/{total_p})"
                    )

                created_files = ConversionService.convert_batch(
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
            created_files = ConversionService.convert_batch(
                books=detected_books,
                output_dir=out_dir,
                author=args.author,
                language=args.lang,
                is_manga=args.manga,
                is_rtl=args.rtl
            )

        renderer.render_success(
            f"Success! {len(created_files)} EPUB books generated in:",
            out_dir
        )
        return

    # SINGLE BOOK CONVERSION
    book_title = args.title or source_path.name
    output_file = args.output or source_path.with_suffix('.epub')

    renderer.render_single_header(
        source_path=source_path,
        output_file=output_file,
        title=book_title,
        author=args.author,
        lang=args.lang,
        is_manga=args.manga,
        is_rtl=args.rtl
    )

    chapters = ScannerService.collect_chapters_and_images(source_path)
    if not chapters:
        renderer.print_error("No valid images found in the source folder or its subdirectories.")
        sys.exit(1)

    total_images = sum(len(c.pages) for c in chapters)
    renderer.render_chapters_table(chapters)

    # Automatic root cover detection
    cover_to_use = args.cover
    if not cover_to_use:
        auto_cover = ScannerService.find_root_cover(source_path)
        if auto_cover:
            cover_to_use = auto_cover
            renderer.print_info(f"Root cover detected: {auto_cover.name}")

    if renderer.is_rich:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=renderer.console
        ) as progress:
            task = progress.add_task("[bold cyan]Generating EPUB...", total=total_images)

            def update_single_progress(current, total, current_chap):
                progress.update(
                    task,
                    completed=current,
                    description=f"[bold cyan]Processing: {current_chap}"
                )

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
                progress_callback=update_single_progress
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

    renderer.render_success("Success! EPUB file generated successfully:", final_epub)


if __name__ == "__main__":
    main()
