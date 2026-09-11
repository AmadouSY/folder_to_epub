"""Rich console presentation and terminal output."""

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

from folder_to_epub.core.models import Book, Chapter


class CliRenderer:
    """Provides formatted console output with Rich (and standard terminal fallback)."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    @property
    def is_rich(self) -> bool:
        return RICH_AVAILABLE and self.console is not None

    def print_error(self, message: str) -> None:
        if self.is_rich:
            self.console.print(f"[bold red]Error: {message}[/bold red]")
        else:
            print(f"Error: {message}", file=sys.stderr)

    def print_info(self, message: str) -> None:
        if self.is_rich:
            self.console.print(f"[bold cyan]ℹ {message}[/bold cyan]")
        else:
            print(f"ℹ {message}")

    def render_batch_header(self, source: Path, output_dir: Path, count: int, is_manga: bool, is_rtl: bool) -> None:
        if self.is_rich:
            self.console.print(Panel.fit(
                f"[bold cyan]Batch Conversion Mode (Multi-Books)[/bold cyan]\n"
                f"[yellow]Source       :[/yellow] {source}\n"
                f"[yellow]Destination  :[/yellow] {output_dir}\n"
                f"[yellow]Books Count  :[/yellow] {count}\n"
                f"[yellow]Manga Layout :[/yellow] {'Yes' if is_manga else 'No'} | [yellow]RTL :[/yellow] {'Yes' if is_rtl else 'No'}",
                title="Batch Configuration"
            ))
        else:
            print(f"--- Batch Conversion Mode ({count} books) ---")
            print(f"Source: {source} -> Destination: {output_dir}")

    def render_books_table(self, books: List[Book]) -> None:
        if self.is_rich:
            table = Table(title="Books Detected")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Chapters", justify="right", style="blue")
            table.add_column("Pages", justify="right", style="green")
            table.add_column("Cover", style="yellow")

            for idx, b in enumerate(books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1st page"
                table.add_row(str(idx), b.title, str(b.chapter_count), str(b.total_images), cov_str)
            self.console.print(table)
            self.console.print("")
        else:
            for idx, b in enumerate(books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1st page"
                print(f"  {idx}. {b.title} ({b.chapter_count} chaps, {b.total_images} pages, cover: {cov_str})")

    def render_single_header(self, source: Path, output_file: Path, title: str, author: str, lang: str, is_manga: bool, is_rtl: bool) -> None:
        if self.is_rich:
            self.console.print(Panel.fit(
                f"[bold cyan]EPUB Generator (Single Book)[/bold cyan]\n"
                f"[yellow]Source       :[/yellow] {source}\n"
                f"[yellow]Output       :[/yellow] {output_file}\n"
                f"[yellow]Title        :[/yellow] {title} | [yellow]Author:[/yellow] {author} | [yellow]Lang:[/yellow] {lang}\n"
                f"[yellow]Manga Layout :[/yellow] {'Yes' if is_manga else 'No'} | [yellow]RTL :[/yellow] {'Yes' if is_rtl else 'No'}",
                title="Book Configuration"
            ))
        else:
            print(f"--- EPUB Generator (Single Book) ---")
            print(f"Source: {source} -> Output: {output_file}")
            print(f"Title: {title} | Author: {author} | Lang: {lang}")

    def render_chapters_table(self, chapters: List[Chapter]) -> None:
        total_images = sum(c.page_count for c in chapters)
        if self.is_rich:
            table = Table(title="Detected Chapters")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("Chapter Title", style="magenta")
            table.add_column("Pages", justify="right", style="green")

            for idx, chap in enumerate(chapters, start=1):
                table.add_row(str(idx), chap.title, str(chap.page_count))
            self.console.print(table)
            self.console.print(f"[bold green]Total: {len(chapters)} chapter(s), {total_images} image page(s).[/bold green]\n")
        else:
            for idx, chap in enumerate(chapters, start=1):
                print(f"  {idx}. {chap.title} ({chap.page_count} pages)")
            print(f"Total: {len(chapters)} chapters, {total_images} pages.")

    def render_success(self, message: str, destination: Path) -> None:
        if self.is_rich:
            self.console.print(f"\n[bold green]{message}[/bold green]\n[cyan]{destination.resolve()}[/cyan]")
        else:
            print(f"{message}: {destination.resolve()}")
