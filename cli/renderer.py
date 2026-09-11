"""Rich terminal rendering and formatted output for CLI."""

import sys
from pathlib import Path
from typing import List

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn
    )
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from core.models import BookData, ChapterData


class CliRenderer:
    """Provides formatted Rich terminal UI and fallback plain text outputs."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    @property
    def is_rich(self) -> bool:
        return RICH_AVAILABLE and self.console is not None

    def print_error(self, message: str) -> None:
        """Prints an error message to stderr."""
        if self.is_rich:
            self.console.print(f"[bold red]Error: {message}[/bold red]")
        else:
            print(f"Error: {message}", file=sys.stderr)

    def print_info(self, message: str) -> None:
        """Prints an informative message."""
        if self.is_rich:
            self.console.print(f"[bold cyan]ℹ {message}[/bold cyan]")
        else:
            print(f"ℹ {message}")

    def render_batch_header(
        self,
        source_path: Path,
        out_dir: Path,
        book_count: int,
        is_manga: bool,
        is_rtl: bool
    ) -> None:
        """Renders the summary panel for batch conversion."""
        if self.is_rich:
            self.console.print(Panel.fit(
                f"[bold cyan]Batch Processing Mode (Multi-Books)[/bold cyan]\n"
                f"[yellow]Collection Source :[/yellow] {source_path}\n"
                f"[yellow]Output Directory  :[/yellow] {out_dir}\n"
                f"[yellow]Books Detected    :[/yellow] {book_count}\n"
                f"[yellow]Manga/Comic Mode  :[/yellow] {'Yes' if is_manga else 'No'} | "
                f"[yellow]RTL Direction :[/yellow] {'Yes' if is_rtl else 'No'}",
                title="Batch Configuration"
            ))
        else:
            print(f"--- Batch Processing Mode ({book_count} books) ---")
            print(f"Source: {source_path}")
            print(f"Output: {out_dir}")

    def render_books_table(self, books: List[BookData]) -> None:
        """Renders the table of detected books in batch mode."""
        if self.is_rich:
            table = Table(title="Books to Convert")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("Book Title", style="magenta")
            table.add_column("Chapters", justify="right", style="blue")
            table.add_column("Pages", justify="right", style="green")
            table.add_column("Cover Image", style="yellow")

            for idx, b in enumerate(books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1st page"
                table.add_row(str(idx), b.title, str(len(b.chapters)), str(b.total_images), cov_str)
            self.console.print(table)
            self.console.print("")
        else:
            for idx, b in enumerate(books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1st page"
                print(f"  {idx}. {b.title} - {len(b.chapters)} chaps, {b.total_images} pages (cover: {cov_str})")

    def render_single_header(
        self,
        source_path: Path,
        output_file: Path,
        title: str,
        author: str,
        lang: str,
        is_manga: bool,
        is_rtl: bool
    ) -> None:
        """Renders the summary panel for a single book conversion."""
        if self.is_rich:
            self.console.print(Panel.fit(
                f"[bold cyan]EPUB Generator (Single Book)[/bold cyan]\n"
                f"[yellow]Source :[/yellow] {source_path}\n"
                f"[yellow]Output :[/yellow] {output_file}\n"
                f"[yellow]Title  :[/yellow] {title} | [yellow]Author :[/yellow] {author} | [yellow]Language :[/yellow] {lang}\n"
                f"[yellow]Manga/Comic Mode :[/yellow] {'Yes' if is_manga else 'No'} | "
                f"[yellow]RTL Direction :[/yellow] {'Yes' if is_rtl else 'No'}",
                title="Configuration"
            ))
        else:
            print(f"--- EPUB Generator (Single Book) ---")
            print(f"Source: {source_path}")
            print(f"Output: {output_file}")
            print(f"Title: {title} | Author: {author} | Lang: {lang}")

    def render_chapters_table(self, chapters: List[ChapterData]) -> None:
        """Renders the table of detected chapters."""
        total_images = sum(len(c.pages) for c in chapters)
        if self.is_rich:
            table = Table(title="Detected Chapters")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("Chapter Name", style="magenta")
            table.add_column("Pages", justify="right", style="green")

            for idx, chap in enumerate(chapters, start=1):
                table.add_row(str(idx), chap.title, str(len(chap.pages)))
            self.console.print(table)
            self.console.print(f"[bold green]Total: {len(chapters)} chapter(s), {total_images} image page(s).[/bold green]\n")
        else:
            for idx, chap in enumerate(chapters, start=1):
                print(f"  {idx}. {chap.title} ({len(chap.pages)} pages)")
            print(f"Total: {len(chapters)} chapters, {total_images} pages.")

    def render_success(self, message: str, destination: Path) -> None:
        """Renders a success confirmation message."""
        if self.is_rich:
            self.console.print(f"\n[bold green]{message}[/bold green]\n[cyan]{destination.resolve()}[/cyan]")
        else:
            print(f"{message}: {destination.resolve()}")
