"""CLI argument parser."""

import argparse
from pathlib import Path


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="folder_to_epub",
        description="Convert an image directory or chapter subfolders into a clean EPUB 3 eBook.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  python -m folder_to_epub ./my_book
  python -m folder_to_epub ./my_manga -o ./manga.epub --title "One Piece Vol 1" --manga --rtl
  python -m folder_to_epub ./my_collection --batch -o ./output_epubs/
"""
    )
    parser.add_argument(
        "source_dir",
        nargs="?",
        type=Path,
        default=None,
        help="Path to the source directory containing images, chapters, or multiple books."
    )
    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Launch the interactive Graphical User Interface (GUI)."
    )
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Force multi-book batch mode (generates one EPUB per subdirectory)."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output EPUB file path (or output directory in batch mode)."
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
        help="Author name (default: 'Unknown')."
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
        help="Custom cover image file."
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
        help="Show detailed log output."
    )
    return parser
