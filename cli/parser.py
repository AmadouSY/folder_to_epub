"""Command-line argument parser definition for folder_to_epub."""

import argparse
from pathlib import Path


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds and returns the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert an image folder or chapter subdirectories into a clean, structured EPUB eBook.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Usage Examples:
  python folder_to_epub.py ./my_book
  python folder_to_epub.py ./manga_folder -o ./manga.epub --title "One Piece Vol 1" --author "Oda" --manga --rtl
  python folder_to_epub.py ./my_collection --batch -o ./output_epubs/
"""
    )
    parser.add_argument(
        "source_dir",
        nargs="?",
        type=Path,
        default=None,
        help="Path to the source folder containing images, chapters, or multiple books."
    )
    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Launch the graphical user interface (GUI)."
    )
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Enable multi-book batch mode (creates an EPUB file for each book subdirectory)."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output EPUB file path (or destination directory in batch mode)."
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        help="eBook title (defaults to source folder name; ignored in batch mode)."
    )
    parser.add_argument(
        "-a", "--author",
        type=str,
        default="Unknown",
        help="Author of the book (default: 'Unknown')."
    )
    parser.add_argument(
        "-l", "--lang",
        type=str,
        default="en",
        help="Language code (default: 'en')."
    )
    parser.add_argument(
        "-c", "--cover",
        type=Path,
        help="Optional custom cover image path."
    )
    parser.add_argument(
        "--manga",
        action="store_true",
        help="Enable Fixed-Layout formatting optimized for Manga and Comics."
    )
    parser.add_argument(
        "--rtl",
        action="store_true",
        help="Set reading progression from Right-To-Left (RTL)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output."
    )
    return parser
